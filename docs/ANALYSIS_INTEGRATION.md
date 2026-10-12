# Wiring the video analysis pipeline into the backend

The pipeline lives in `backend/app/analysis/` and is **standalone**: it does not import FastAPI,
the database, or `app.core.config`. Nothing in the existing app has been changed to use it yet.
This page describes the intended hook-up.

## What it does

```
upload (webm/mp4) -> 1 preprocess -> 2 audio -> 3 vision -> 4 fusion/scores -> 5 feedback -> FinalReport
```

| Phase | Module | Output file (in `backend/data/runs/<run_id>/`) |
|---|---|---|
| 1 | `preprocess.py` | `audio.wav`, `frames/`, `metadata.json` |
| 2 | `audio/` | `audio_analysis.json` |
| 3 | `vision/` | `vision_analysis.json`, `vision_features.csv`, optional `debug_vision.mp4` |
| 4 | `fusion/` | `session_report.json` |
| 5 | `feedback/` | `final_report.json` (this is what the frontend renders) |

Command line: `python -m app.analysis.cli analyze <video> --topic "..."` (or run phases one by one;
see `python -m app.analysis.cli --help`).

## Calling it from an API route

One function runs everything:

```python
from app.analysis.service import analyze_recording

final = analyze_recording(saved_upload_path, topic="Climate change", key_points=[...])
```

It is synchronous and heavy (roughly 1-3 minutes for a 5-minute video on CPU), so a route should
**save the upload, start a background task, and return a job id** that the frontend polls.
Suggested module, following `ARCHITECTURE.md`:

```
app/modules/analysis/
    analysis_controller.py   POST /analysis (upload) , GET /analysis/{job_id}
    analysis_service.py      calls analyze_recording() in a background task, then persists
    analysis_repository.py   inserts the rows below
    analysis_schemas.py      response models (can re-export FinalReport)
```

Run-time notes:
- Needs **FFmpeg** on PATH and the MediaPipe model files (`python -m app.analysis.vision.models`).
- Whisper model size is chosen from free RAM at run time (`audio/asr.py`); use a machine with
  more RAM for `small`/`medium`, which transcribe fillers better.
- Dependencies for the pipeline are in `backend/analysis_requirements.txt` (kept apart from
  the large root `requirements.txt`).
- Delete uploaded videos and `data/runs/<id>/frames` after analysis unless the user opts in to keep them.

## Persisting results

`app/analysis/persistence.py::to_db_payload(final)` returns the values for the existing tables,
keyed by table name (pure data, no SQLAlchemy):

| Table | Filled from |
|---|---|
| `talk_session` | `context` = topic, `score` = overall score |
| `talk_session_audio` | filler count, long-pause count |
| `repeated_words` | repeated-word events grouped by word |
| `talk_session_video` | `posture_count` = slouch + lean events, `head_movement_count` = look-aways, `hand_gesture_count` = fidget + face-touch events |
| `talk_session_summary` | topic, transcript, feedback summary |
| `ai_feedback_alternate_words` | each filler -> its first suggested alternative |

**Please confirm the three `*_count` column meanings in `talk_session_video`;** they are guesses.

Most of the result (events timeline, scores with reasons, segments, issues with timestamps,
practice plan) has no column. Proposed: one JSONB column on a new table, written in an Alembic
migration (not applied):

```sql
CREATE TABLE talk_session_analysis (
    id               BIGSERIAL PRIMARY KEY,
    talk_session_id  BIGINT NOT NULL UNIQUE REFERENCES talk_session(id) ON DELETE CASCADE,
    analysis_json    JSONB  NOT NULL,          -- payload["analysis_json"] (the FinalReport)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Insert everything in one transaction. `mispronounced_words` stays empty (pronunciation is not analysed).

## Optional LLM for the feedback wording

Phase 5 works fully offline with template text built from your own metrics and the tips in
`feedback/knowledge/`. To have an LLM reword the summary/advice, set these environment variables
(for example in `backend/.env`; never commit keys):

| Variable | Meaning |
|---|---|
| `SPEAKWISE_LLM_API_KEY` | provider key (required) |
| `SPEAKWISE_LLM_MODEL` | model id (required) |
| `SPEAKWISE_LLM_PROVIDER` | `openai` (default; any OpenAI-compatible endpoint) or `anthropic` |
| `SPEAKWISE_LLM_BASE_URL` | optional, e.g. a local server |

**Privacy:** when enabled, the session transcript and metrics are sent to that provider. Leave the
variables unset to keep everything on the machine. The LLM only rewords text; numbers, timestamps,
scores and the list of issues always come from the analysis, and an unusable reply falls back to
the template text.

## Known limitations

- Scores and thresholds are heuristics; tune them on real recordings (`config.py`, `fusion/scoring.py`).
  An ML scorer slot exists (`fusion/ml.py`) but needs human-rated sessions to train.
- Filler detection depends on Whisper keeping "um"/"uh"; small models under-count them.
- Gesturing and fidgeting are not separated (both show up as "restless hands").
- Left/right look-away labels assume an un-mirrored video; verify with the debug video.
