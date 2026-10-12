# SpeakWise speech-analysis pipeline

Standalone Python package (`speakwise`) that analyses **one MP4 recording** (audio + video) of a
practice talk against its **topic** and the **exact reading material** the speaker was given, and returns
a validated, structured report (Python object / JSON). Developed and tested in Google Colab; runs anywhere
with Python 3.10+ and FFmpeg. No database, GUI or web server.

```python
from speakwise.pipeline import process_session
report = process_session("talk.mp4", topic, reading_material, speaking_duration=180)
print(report.to_json())          # validated against the schema in configs/report.schema.json
```

> Status: development POC. Software behaviour is tested; **model accuracy has not been measured on real,
> human-annotated recordings yet**. See "Results" and "Limitations".

## Quick start

**Colab (recommended):** open `notebooks/speakwise_pipeline_colab.ipynb` from GitHub
(`https://colab.research.google.com/github/pranjalsonar/SpeakWise/blob/poc_model/speakwise_pipeline/notebooks/speakwise_pipeline_colab.ipynb`)
and run cells 1-6. Each session re-clones the repo; nothing depends on earlier sessions.

**Local:**
```bash
cd speakwise_pipeline
pip install -r requirements.txt          # plus FFmpeg on PATH
python -m speakwise.models download      # ~330 MB (MiniLM, NLI, MediaPipe)
python -m pytest tests -m "not slow"     # fast test suite
python scripts/generate_test_fixture.py  # synthetic MP4 (needs espeak-ng or Windows SAPI)
```
On a low-memory machine use `configs/low_memory_cpu.json` (`PipelineConfig.from_json(...)`).

## Architecture

| Stage | Module | What it does |
|---|---|---|
| Input | `media_preprocessing.py` | Validates the MP4 (readable, container, streams, decodable start/end, silence, duration, metadata consistency), extracts 16 kHz mono WAV to a temp workspace, streams sampled video frames through an ffmpeg pipe (no frames on disk), records alignment. |
| Audio | `audio_transcription.py` | faster-whisper with word timestamps and probabilities; model/device chosen from detected hardware. |
| | `audio_metrics.py` | Fillers (context-aware), repetitions (accidental / phrase / possible emphasis), pauses (VAD + energy check, boundaries separated), clarity segments, recording quality. |
| Video | `video_analysis.py` | MediaPipe face + pose-lite: face visibility, head orientation, estimated camera-directed gaze, posture/movement only when shoulders are visible. |
| Context | `context_matching.py` | Topic relevance, key-point coverage (duration-adjusted), per-claim consistency with the material (NLI), off-topic segments, reliability gate. Rubric in the module docstring. |
| Aggregation | `report_aggregation.py` | Evidence-grounded suggestions; collects warnings. No overall "confidence" score. |
| Output | `schemas.py`, `pipeline.py` | `SessionReport` (Pydantic) with sections session_metadata, input_validation, preprocessing, transcription, audio_analysis, video_analysis, context_evaluation, improvement_suggestions, processing_metadata, warnings, errors. |

Shared clock: seconds from the start of the container. Every measurement is a `Metric`
`{value, unit, status, denominator, note}`; status `ok|warning` carries a value, `unavailable|failed|skipped`
never does, so a valid zero is always distinguishable from a missing measurement.

Adapted from the existing backend POC (`backend/app/analysis/`, unchanged): FFmpeg extraction and rotation
handling, filler rules, VAD pause logic, MediaPipe head pose / iris / smoothing chain, MiniLM ONNX embedder.

## Model selection (initial stack)

| Task | Choice | Size | Licence | Why |
|---|---|---|---|---|
| ASR | faster-whisper `small` (GPU, fp16) / `base`-`tiny` (CPU int8, by free RAM) | 75-480 MB | MIT | Word timestamps + probabilities; CTranslate2 keeps memory low. `large-v3-turbo` is measured, not default. |
| VAD | Silero VAD (bundled with faster-whisper) | <2 MB | MIT | Independent of the transcript. |
| Face / pose | MediaPipe Face Landmarker, Pose Landmarker lite | 10 MB | Apache-2.0 | CPU real-time; iris + head-pose matrix; suits webcam framing. |
| Embeddings | all-MiniLM-L6-v2 (ONNX int8) | 23 MB | Apache-2.0 | Relevance, retrieval, key points; no PyTorch. |
| NLI | cross-encoder/nli-deberta-v3-xsmall, 8-bit ONNX | 96 MB | Apache-2.0 | 3-way entail/contradict/neutral per claim; same accuracy as full precision (below). |

Not chosen: CrisperWhisper (better at fillers, but CC-BY-NC), hosted LLM APIs (cost, privacy, keys;
can be added later as an optional evaluator), large NLI/LLM models (memory).

**Colab GPU note.** Colab (Oct 2026) ships CUDA 13; CTranslate2 needs CUDA 12 cuBLAS/cuDNN 9. The notebook
installs `nvidia-cublas-cu12` and `nvidia-cudnn-cu12==9.*` and the pipeline preloads them
(`environment.preload_cuda12_libs`). If the GPU path still fails, transcription falls back to CPU and the
report says so.

## Results (what was actually executed)

Status labels: **F** = functional test outcome, **P** = preliminary model evaluation (author-written or
synthetic data), **M** = measured accuracy on human-annotated data (**none yet**).

| What | Where | Outcome |
|---|---|---|
| Unit, edge-case and end-to-end tests (50) | Windows 10, Python 3.10, CPU | **F** 50 passed |
| Same suite | Colab, Python 3.13, Tesla T4 | **F** 47/47 passed on the first commit (3 regression tests added since) |
| Full pipeline on synthetic MP4 (30 s, espeak-ng speech) | Colab T4, Whisper `small` fp16 | **F/P** 10.6 s end to end; transcript mean word probability 0.95; fillers 3/3 (um, uh, you know); inserted pauses 4/4 with correct short/long class (longest measured 2.4 s vs 2.5 s true); no face found in the test pattern and reported as *unavailable* |
| Speech recognisers on the fixture | Colab T4 | **P** WER: base 3.0 %, small 3.0 %, large-v3-turbo 1.5 %; decode 0.5-0.9 s for 30 s; all kept "um/uh"; **none kept the deliberate "the the"** |
| NLI candidates on 20 author-written pairs | Colab | **P** xsmall 8-bit 0.75, xsmall fp32 0.75 (identical: quantisation was *not* the problem), binary MIT model 0.90 (entailed vs not; cannot detect contradiction) |
| Context rubric on 11 author-written seed speeches | Local | **P** relevance ordering 16/16 pairs; poor transcript flagged unavailable; key points precision 0.85 / recall 0.82; planted inconsistencies 3/3 with 0 false flags **after tuning the rule on this same set** (2 false flags before) |

Resource use (Colab T4, 30 s clip): peak process RSS 2.7 GB, GPU memory 1.2 GB, timings
preprocessing 1.3 s, transcription 1.4 s, audio metrics 0.1 s, video 3.9 s (5 fps), context 3.6 s.
On an 8 GB Windows laptop with < 1 GB free RAM, Whisper could not load at all (`mkl_malloc`); the
pipeline reports this as a failed transcription and continues with signal-level metrics.

## Limitations and open evidence needs

* **No accuracy claim is possible yet.** All numbers above come from synthetic speech or author-written
  examples. Needed: consented real recordings (Indian English, laptop webcam) annotated with
  `annotations/` templates, scored with `scripts/evaluate_annotations.py`, and human relevance ratings.
* **Fillers and repetitions are lower bounds:** Whisper drops many hesitations and cleaned up the planted
  "the the" in every model tested. Short untranscribed voiced sounds are reported separately as possible
  dropped fillers.
* **Consistency:** the xsmall NLI model over-predicts contradiction for related and even unrelated passages;
  only the closest passage may contradict a claim (threshold tuned on seed data). "Supported" is
  under-detected for paraphrases, so most correct claims show as "not addressed", which is *not* "wrong".
* **Context thresholds** (relevance anchors 0.12/0.50, coverage 0.50 + margin 0.02, contradiction rule) were
  set on the seed set; the 70/100 target is provisional.
* **Gaze** is a head-pose + iris heuristic, never validated; a test pattern cannot validate it. Posture is
  only reported when both shoulders are visible and is relative to the speaker's own median.
* **Language:** English only. Filler lexicons are keyed by language (`audio_metrics.LEXICONS`) so
  Hindi-English terms can be added; Whisper's language can be set or auto-detected in config.
* **TTS fixture** speech is clean and robotic; it validates software paths, not real-world recognition.

## Privacy and retention
Everything runs locally in the runtime; no external APIs. Extracted audio lives in a temporary workspace
that is deleted at the end of every run (also on errors and interruptions) unless `keep_artifacts=True`.
Reports store the reading material as a SHA-256 hash and word count, plus the transcript. Recordings,
reports, annotations and model files are git-ignored.

## Integrating into a desktop app
Call `speakwise.pipeline.process_session(...)` from a worker thread or process (it takes seconds on a GPU,
minutes on a CPU) and read `SessionReport` (or the JSON, schema in `configs/report.schema.json`). Every
metric carries its status, so the UI can show "not measured" instead of zero.
