# SpeakWise backend

FastAPI service that analyses a recorded talk. The mobile app uploads a video, the backend runs the
pipeline and the app polls for the report. Keys for Groq and Deepgram are read from `backend/.env`
(`GROQ_API_KEY`, `DEEPGRAM_API_KEY`) and never sent to the app.

## Run

```powershell
cd D:\madam_project\SpeakWise\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

First start downloads the MediaPipe models and the embedding model into `backend/models/`.

Check: http://localhost:8000/health

## Make it reachable from phones

- Demo from your laptop (free, no account): [docs/SETUP_LOCAL_TUNNEL.md](../docs/SETUP_LOCAL_TUNNEL.md),
  or just run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\scripts\start-demo.ps1`
- Always-on cloud deployment: [docs/DEPLOY_CLOUD.md](../docs/DEPLOY_CLOUD.md)

## First-time setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

## Test without the app

```powershell
.\.venv\Scripts\python.exe scripts\test_job.py "..\demo videos\test_demo_video_unicorn.mp4" unicorns Raj
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status, article count, which providers are configured |
| POST | `/jobs` | Multipart: `video`, `topic_id`, `first_name`, `client_ref` → `202` job |
| GET | `/jobs/{id}` | `status` (queued/running/done/failed), `step`, `progress`, `error`, `result` |

Errors use `{"detail": {"code": "...", "message": "..."}}`.

## Pipeline (`app/services/analysis/`)

1. `media.py` – PyAV decodes audio (16 kHz) and frames (10 fps); audio is re-encoded as Opus for upload.
2. `vision.py` – MediaPipe face + pose (orientation auto-detected) → eye contact, posture, gestures.
3. `asr.py` – Groq Whisper and Deepgram in parallel; Groq words (keeps fillers) + Deepgram timings/confidence.
4. `speech.py` – fillers, pauses (from the audio signal), repetition, clarity, pace, voice.
5. `llm.py` + `app/prompts/` – Groq judge (content relevance) and coach feedback, strict JSON, validated.
6. `context.py` – embeddings (fastembed, CPU) blended with the judge score.
7. `scoring.py` – 0–100 scores, grade, summary and tips.

Jobs are stored in `data/jobs.db` (SQLite); uploaded videos are deleted after processing.
