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
| NLI | cross-encoder/nli-deberta-v3-xsmall (ONNX) | 293 MB | Apache-2.0 | 3-way entail/contradict/neutral per claim. |

Not chosen: CrisperWhisper (better at fillers, but CC-BY-NC), hosted LLM APIs (cost, privacy, keys;
can be added later as an optional evaluator), large NLI/LLM models (memory).

## Documentation still to come
Results, resource measurements and the final limitations list are filled in after the Colab runs.
