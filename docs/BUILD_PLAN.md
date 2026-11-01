# SpeakWise Mobile – Build Plan (Demo)

Target: Android (Vivo V40e) · React Native + TypeScript + Expo (same setup as `D:\moment_app`) · free services only.
Status legend: `[ ]` todo · `[~]` in progress · `[x]` done

## Constraints (agreed)
- **No Android Studio / no new heavy software.** Develop with **Expo Go** on the phone; final APK via **EAS cloud build** (already set up in moment_app).
- Low disk space (C: ~6 GB, D: ~18 GB): Python venv on D:, `pip --no-cache-dir`, lightweight libraries only.
- No password login. First-launch **profile** (name, age, gender…) used to personalise the UI ("Hey Raj, here's your report for session 3").
- SQLite for storage (phone: expo-sqlite · backend: sqlite3 for analysis jobs).
- Free tiers only: Groq (Whisper + LLM judge) + Deepgram (ASR fallback/merge). No payment card on either account.

## Architecture

```
PHONE (Expo Go → EAS APK)                           BACKEND (FastAPI on laptop, CPU only)
- SQLite: profile, topics, sessions, reports         - POST /jobs        upload video + topic_id → job_id
- Onboarding profile                                 - GET  /jobs/{id}   status / progress / report
- Topic library (25 seeded, local search)            - GET  /health
- Reader → duration → record (expo-camera, ≤2 min)   Pipeline per job:
- Upload video, poll job, save report                  PyAV: video → 16 kHz audio + 10 fps frames
- Video + material + report kept in History            MediaPipe face/pose (POC vision.py)
- Resume exactly where the user left off               Groq Whisper ∥ Deepgram → merged words
                                                       POC speech rules + audio-signal pauses
                                                       Embeddings (ONNX, light) + Groq judge
                                                       POC scoring → report JSON (stored in SQLite)
                                                       Uploaded video deleted after processing
```

Why vision runs on the backend: an on-phone MediaPipe module needs native Kotlin code, which needs
Android Studio or a cloud build for every change, and doesn't work in Expo Go. Running it on the
backend reuses the POC's `vision.py` unchanged and keeps development inside Expo Go.

---

## Phase 0 – Setup
Dev phone: **Realme C55 over USB** (adb already at `%LOCALAPPDATA%\Android\Sdk\platform-tools`, no Android Studio). Demo phone: Vivo V40e.
- [x] 0.1 Realme C55 (RMX3710, Android 15): USB debugging on, authorised, `adb devices` shows it
- [x] 0.2 Create `SpeakWise/mobile` with `create-expo-app` (TypeScript, expo-router, `src/app`) – installed **Expo SDK 58** / RN 0.88
- [x] 0.3 Expo Go 58.0.5 on the phone matches SDK 58; starter app runs over USB
- [x] 0.4 Clean the template; mirror moment_app structure under `src/`: `app/`, `components/`, `constants/`, `context/`, `hooks/`, `utils/`, `db/`
- [x] 0.5 `adb reverse tcp:8081 tcp:8081` + `tcp:8000 tcp:8000` so the phone reaches Metro and the backend over USB
- [x] 0.6 Backend venv on D: with minimal deps (fastapi, uvicorn, python-multipart, av, mediapipe, opencv-headless, librosa, soundfile, fastembed, requests), `--no-cache-dir`

## Phase 1 – Content: 25 seeded articles (600–700 words each)
- [x] 1.1 Article JSON format: `id, title, category, level, word_count, read_minutes, summary, talking_points[], body (markdown), as_of`
- [x] 1.2 Write 25 articles – simple English, short sentences, 4–5 short sections, ends with "Key Talking Points"
- [x] 1.3 Validation script: required fields, 600–700 words, readability, unique ids
- [x] 1.4 One file `content/articles.json` shared by app (SQLite seed) and backend (judge)

| Science | Space | History | Current Affairs | Literature | Fiction & Myth |
|---|---|---|---|---|---|
| Why We Need Sleep | Black Holes Explained | The Indus Valley Civilisation | Digital Payments and UPI | William Shakespeare | Harry Potter |
| How Vaccines Work | Could Humans Live on Mars? | The Printing Press | Living with AI | Rabindranath Tagore | James Bond |
| Antibiotic Resistance | Chandrayaan-3 | The Industrial Revolution | Renewable Energy & Climate | Orwell's *Nineteen Eighty-Four* | Unicorns |
| How Machines Learn | James Webb Space Telescope | The Salt March | Social Media & Mental Health | The Panchatantra | The Phoenix (Fire Bird) |
| | | | | | Dragons |

## Phase 2 – Mobile foundation
- [x] 2.1 Design tokens from the web frontend: primary `#2563eb`, pressed `#1d4ed8`, secondary `#3b82f6`, tint `#eff6ff`, surface `#f8fafc`, text `#1e293b`, muted `#64748b`, border `#e2e8f0`, radius 10/14/16, soft shadows, pill badges
- [x] 2.2 Components: Button, Card, Badge, CategoryChip, SearchBar, ProgressBar, ScoreRing, MetricTile, Banner, EmptyState, FormField
- [x] 2.3 Drop web-only parts (navbar links, fake stats, marketing hero)
- [x] 2.4 Navigation: onboarding stack → tabs **Home · Topics · History** (+ profile/settings); Android back handling
- [x] 2.5 SQLite schema + migrations (`PRAGMA user_version`) + seed from `articles.json`
      - `profile` (name, age, gender, role, goal, created_at)
      - `topics` (id, title, category, level, read_minutes, summary, talking_points, body, word_count)
      - `sessions` (id, topic_id, stage, duration_sec, reading_progress, video_path, job_id, report, overall_score, error, created_at, updated_at)
      - `settings` (key, value) – backend URL, font size
- [x] 2.6 Typed repository layer + React context for profile and active session

## Phase 3 – Session state machine & resume
- [x] 3.1 Stages: `reading → choosing_duration → ready_to_record → recorded → uploading → analyzing → done | failed`
- [x] 3.2 Every stage change saved to SQLite immediately; reading scroll position saved periodically
- [x] 3.3 On app launch: open the active session at its stage (reader scrolled back to position, etc.)
- [x] 3.4 Killed mid-recording → partial recording discarded, back to "ready to record" with a message
- [x] 3.5 Killed while uploading → re-upload saved video; while analyzing → poll the saved `job_id`
- [x] 3.6 "Abandon session" option; one active session at a time

## Phase 4 – Screens (mobile layout)
- [x] 4.1 Onboarding: welcome → profile form (validated) → permissions explainer
- [x] 4.2 Home: "Hey {name}", random topic, resume active session card, last score
- [x] 4.3 Topic library: local search (title/category/summary) + category chips
- [x] 4.4 Reader: typography, font size, progress bar, summary + talking points, "I'm ready"
- [x] 4.5 Duration picker: 1 min / 2 min
- [x] 4.6 Pre-record checklist: permissions, network + backend, storage, framing tips
- [x] 4.7 Recording: front camera, 3-2-1, timer, auto-stop at limit, finish early, back button guarded
- [x] 4.8 Analysis progress: live steps from job progress
- [x] 4.9 Report: "Hey {name}, here's your report for session {n}", overall score, sub-scores, fillers, pauses, repetition, pace, eye contact, body language, context match, tips, highlighted transcript
- [x] 4.10 History: list → session detail (report + material + video playback), delete session/video
- [x] 4.11 Profile & Settings: edit profile, backend URL + test, text size, clear data
- [ ] 4.12 Layout checks: safe areas, font scaling, keyboard handling, portrait lock

## Phase 5 – Permissions & device validation
- [x] 5.1 Camera + mic: explain → request → granted / denied (retry) / blocked ("Open Settings")
- [x] 5.2 Re-check on app foreground
- [x] 5.3 No storage/media-library permission (app-private files)
- [x] 5.4 Free-storage check before recording; keep screen awake while recording
- [x] 5.5 Interruptions (background, call, camera error) handled per 3.4

## Phase 6 – Network & API robustness
- [x] 6.1 NetInfo offline banner; reading/recording work offline
- [x] 6.2 Backend health check with timeout
- [x] 6.3 API client: timeouts, retry with backoff, upload progress, friendly errors (413/422/429/5xx)
- [x] 6.4 Recorded offline → waits and uploads when back online; manual retry
- [ ] 6.5 Demo connectivity: laptop backend via cloudflared HTTPS tunnel; URL editable in Settings

## Phase 7 – Backend
- [x] 7.1 Clean minimal `requirements.txt`; remove Postgres + auth from the app startup (keep code parked)
- [x] 7.2 Job API: `POST /jobs` (multipart video ≤ 60 MB, topic_id, duration_sec, profile first name), `GET /jobs/{id}`, `GET /health`; jobs in SQLite; background worker
- [x] 7.3 Validation: file type/size, duration ≤ 125 s, known topic, minimum speech
- [x] 7.4 PyAV decode → audio + frames; MediaPipe (POC `vision.py`)
- [x] 7.5 ASR: Groq ∥ Deepgram, merged; single-provider fallback
- [x] 7.6 POC `speech.py` + audio-signal pauses; POC `scoring.py`
- [x] 7.7 **Groq prompts module**: versioned system/user prompts, transcript and material wrapped in tags and treated as data (injection-safe), strict JSON schema output, pydantic validation, one repair retry, temperature 0, timeouts, 429 back-off, embedding-only fallback
- [x] 7.8 Delete uploaded video after processing; log usage per job
- [x] 7.9 Test with the unicorn demo video; compare to POC

## Phase 8 – Integration & build
- [ ] 8.1 End-to-end on the Vivo in Expo Go
- [ ] 8.2 Loading / empty / error states reviewed
- [ ] 8.3 App icon, splash, name
- [ ] 8.4 EAS cloud build → APK (preview profile); HTTPS backend URL

## Phase 9 – Demo prep
- [ ] 9.1 3–4 full test runs; check Groq/Deepgram dashboards
- [ ] 9.2 Offline-viewable sample report as backup
- [ ] 9.3 Demo walkthrough
