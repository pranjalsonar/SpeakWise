2026-10-07

# SpeakWise: Video Analysis POC (Phases 1-5)

Reference note for picking this project up again. Everything described here exists in the repo
and was run end to end on test data.

## 1. What we built

A proof of concept that takes **one recorded speech video** (1/3/5 minutes) and produces a full
report: filler words, pauses, eye contact, posture, hand movement, scores, and coaching feedback.

It is a **standalone package** at `backend/app/analysis/`. It does not import FastAPI, the
database, or `app.core.config`, so it runs from the command line today and can be wired into an
API route later. **Nothing in the existing app was changed to use it.**

```
video -> 1 preprocess -> 2 audio -> 3 vision -> 4 fusion/scores -> 5 feedback -> final_report.json
```

| Phase | Package / file | Does | Output (in `backend/data/runs/<run_id>/`) |
|---|---|---|---|
| 1 | `preprocess.py` | FFmpeg: audio to 16 kHz mono WAV, frames at 10 fps, metadata | `audio.wav`, `frames/`, `metadata.json` |
| 2 | `audio/` | VAD, Whisper transcript with word times, fillers, repetitions, pauses, prosody | `audio_analysis.json` |
| 3 | `vision/` | MediaPipe face/pose/hands to eye contact, posture, face touch, fidget, sway | `vision_analysis.json`, `vision_features.csv`, optional `debug_vision.mp4` |
| 4 | `fusion/` | Merged timeline, 30 s segments, struggle clusters, correlations, scores | `session_report.json` |
| 5 | `feedback/` | Issues with evidence, tips retrieval (RAG), vocabulary, practice plan | `final_report.json` |

Extras: `service.py` (one-call entry point), `persistence.py` (maps results onto the DB tables),
`cli.py` (command line), `config.py` (all thresholds), `schemas.py` (all data contracts).

## 2. How to run it

Run from `D:\SpeakWise\backend` with the project's venv active (`D:\SpeakWise\.venv`).
Use a **real** video path; `C:\path\to\video.mp4` is only a placeholder.

```powershell
# everything at once (phases 1-5)
python -m app.analysis.cli analyze "C:\your\video.mp4" --run-id mytest --topic "Climate change" --debug

# or phase by phase, using the run id
python -m app.analysis.cli preprocess "C:\your\video.mp4" --run-id mytest
python -m app.analysis.cli audio mytest
python -m app.analysis.cli vision mytest --debug
python -m app.analysis.cli report mytest
python -m app.analysis.cli feedback mytest --topic "Climate change"

# tests (41, all pass)
python -m pytest tests -q -p no:cacheprovider
```

Test runs already on disk: `tts` (synthetic speech with planted fillers and a long pause),
`face` (still portrait), `svc` (full service run), `demo`.

Python API (what a future route calls):

```python
from app.analysis.service import analyze_recording
final = analyze_recording(path, topic="...", key_points=[...])   # -> FinalReport
```

## 3. One-time setup (already done on this machine)

- **FFmpeg** on PATH (v7.1).
- **Venv packages:** `pip install -r backend/analysis_requirements.txt` (pydantic, faster-whisper,
  parselmouth, mediapipe, psutil, scikit-learn, joblib, pytest).
- **MediaPipe model files** (about 21 MB, git-ignored): `python -m app.analysis.vision.models`
  downloads them into `backend/app/analysis/models/`.
- **Whisper model** downloads on first use into `C:\Users\shri\.cache\huggingface`.
- **Drive C: is full (0 GB free).** pip's cache there is 19.7 GB (not touched). Before any
  `pip install`, point temp and cache at D:

  ```powershell
  $env:TEMP = "D:\pip_tmp"; $env:TMP = "D:\pip_tmp"
  pip install --cache-dir D:\pip_cache <package>
  ```

## 4. Key design decisions

- **One shared clock.** Every timestamp is seconds from the start of the video; frame `i` is at
  `i / 10` s; both audio and frames are shifted to start at t=0. All phases use one `Event`
  format `{type, source, start, end, confidence, meta}`, so merging audio and video is trivial.
- **Phases communicate through files in a run directory**, never through the raw video.
- **Audio pauses** come from VAD silences (independent of the ASR), with ASR word gaps as backup.
  Each pause is labelled `sentence_boundary`, `clause_boundary` or `hesitation`, because a pause
  at a boundary is healthy and one mid-phrase is hesitation.
- **Fillers:** um/uh patterns, lexical fillers ("basically"), phrases ("you know"), and context
  rules for ambiguous words ("like" only counts when set off by commas or pauses).
- **Vision uses calibration.** The baseline ("looking at camera, sitting straight") is the median
  of the first 3 s (`calibration_s`). The frontend should ask the user to do that before speaking.
  Falls back to the whole-clip median.
- **Every signal is smoothed:** gap fill, median filter, hysteresis (separate enter/exit
  thresholds), minimum duration, merge gap. Without this one blink would count as a look-away.
- **Head pose** uses MediaPipe's facial transformation matrix. My first 6-point `solvePnP`
  version had a roughly 30 degree constant pitch error.
- **Scores are rule-based and explainable.** Each metric maps linearly from "good" (100) to "bad"
  (0); every sub-score lists which metrics cost it points. Missing audio or video is handled by
  reweighting. Overall weights: fluency 35, eye contact 25, delivery 15, composure 15, posture 10.
- **ML is a slot, not a model.** There are no human-rated sessions, and a model trained on made-up
  labels would be fake. `fusion/ml.py` has the feature vector, a training command and a loader
  that adds `ml_overall` when `models/confidence_model.joblib` exists.
- **Feedback works offline.** Templates plus tips retrieval (BM25, tag-filtered, the curated
  primary tip first). An LLM is optional and only rewords text; numbers, timestamps and issues
  always come from the analysis, and a bad LLM reply falls back to the template.
- **Whisper size is chosen from free RAM** (`audio/asr.py`), and the speech model is released
  before the vision phase starts.

## 5. Where to change things

| Want to change | Edit |
|---|---|
| Any threshold (pauses, gaze, slouch, fidget, segments) | `backend/app/analysis/config.py` |
| Scoring targets and weights | `fusion/scoring.py` |
| Coaching tips | `feedback/knowledge/tips.json` (tag with `issues`, mark `primary_for`) |
| Filler alternatives and synonyms | `feedback/knowledge/vocabulary.json` |
| Filler word lists and rules | `audio/fillers.py` |
| Look-away / posture / hand logic | `vision/behaviors.py` |
| Whisper size (accuracy vs RAM) | `whisper_model` in `config.py` (`small` needs about 1.6 GB free RAM) |

## 6. Open items and known limitations

**To do next (highest value first):**
1. **Test on a real recording.** Everything so far ran on synthetic speech, a still photo and
   synthetic feature tables. Record about 60 s with a few "ums", some looking down, some hand
   gestures, run `analyze ... --debug`, watch `debug_vision.mp4`, then tune thresholds and scoring.
2. **Confirm look-away direction labels** (left/right might be mirrored): turn your head right in
   a test clip and check the label.
3. **Confirm the DB column mapping** in `persistence.py` (see below), then build the route.
4. **Pick an LLM provider** if you want reworded feedback (see section 7).
5. **Collect rated sessions** (3-5 raters x about 10 sessions, scores 0-100) and train the ML
   scorer: `python -m app.analysis.fusion.ml train labels.csv`. Report leave-one-out error versus
   the "predict the median" baseline.
6. **Annotate 15-20 clips by hand** (fillers, pauses, look-aways) to report precision/recall.
   Good for the final report.

**Limitations:**
- Whisper often **deletes "um"/"uh"**; small models under-count fillers. Upgrade options:
  larger model, CrisperWhisper, or an audio filler classifier.
- The `tiny`/`base` models are used when RAM is low; the report warns about it.
- Gesturing and fidgeting are not separated (both are "restless hands").
- Hand detection and fidget thresholds are untested on real hands.
- Gaze uses head pose plus iris position with heuristic gains (`gaze_gain_h/v`).
- Heuristic score targets are not validated.
- No pronunciation analysis (`mispronounced_words` stays empty).

## 7. Integrating with the backend (not done yet)

Details are in `docs/ANALYSIS_INTEGRATION.md`. Summary:

- **Your DB schema changed during the session.** There is no `speech_analysis` table now; sessions
  use `talk_session`, `talk_session_audio`, `talk_session_video`, `talk_session_summary`,
  `ai_feedback`, `ai_feedback_alternate_words`, `repeated_words`, `mispronounced_words`.
- `persistence.to_db_payload(final)` returns the values for those tables, plus `analysis_json`
  (the full report) for one proposed JSONB table `talk_session_analysis` (SQL in the doc).
  **Guessed column meanings to confirm:** `posture_count` = slouch + lean events,
  `head_movement_count` = look-aways, `hand_gesture_count` = fidget + face-touch events.
- The pipeline takes about 1-3 minutes for a 5-minute video, so a route should save the upload,
  run `analyze_recording()` in a background task, and return a job id to poll. Suggested module:
  `app/modules/analysis/` (controller, service, repository, schemas), following `ARCHITECTURE.md`.
- **Optional LLM:** set `SPEAKWISE_LLM_API_KEY` and `SPEAKWISE_LLM_MODEL` (plus
  `SPEAKWISE_LLM_PROVIDER=openai|anthropic`, `SPEAKWISE_LLM_BASE_URL`). The client is tested only
  against a mocked network, not a live API. When on, the transcript is sent to that provider.
- Delete uploaded videos and extracted frames after analysis unless the user opts in to keep them.

## 8. Gotchas we hit (so they don't bite twice)

- **Placeholder paths:** `C:\path\to\video.mp4` and `C:\your\video.mp4` are examples, not files.
  `cd backend` fails if you are already in `backend`.
- **`.venv` was missing packages** (pydantic, fastapi, uvicorn). The pipeline's packages are in
  `backend/analysis_requirements.txt`; the backend's own app still needs its own install.
- **Low RAM (about 1 GB free of 8 GB):** `mkl_malloc: failed to allocate memory` from Whisper, or
  an `AllocateTensors` / XNNPACK error from MediaPipe, means too little free memory. Close other
  apps. The code already selects a smaller Whisper model and frees it before the vision phase.
- **MediaPipe 1.1.0 no longer bundles models** and has no old `mp.solutions` API; the code uses
  the Tasks API and the downloaded `.task` files.
- **Installing MediaPipe upgraded numpy to 2.x** in the venv. Phases 1-5 work with it; check this
  before installing the backend's other packages there.
- **Disk:** C: is full (see section 3); keep installs and temp on D:.

## 9. Repo state

Branch: `feature/knowledge-pack`. **Nothing from this work is committed.** New, untracked:
`backend/app/analysis/`, `backend/tests/`, `backend/analysis_requirements.txt`,
`docs/ANALYSIS_INTEGRATION.md`, this note. Modified: root `.gitignore` (ignores `backend/data/`
and `backend/app/analysis/models/`). `backend/app/domains/` was already untracked before this work.

Suggested commit: `feat(analysis): add video analysis POC (preprocess, audio, vision, fusion, feedback)`.
Run the tests first.
