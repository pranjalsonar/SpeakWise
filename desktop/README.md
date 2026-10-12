# SpeakWise Desktop (first draft)

> **Step-by-step setup, Google OAuth, Colab notebook steps, demo script and screenshots:
> [../DESKTOP_APP_GUIDE.md](../DESKTOP_APP_GUIDE.md).**

Electron shell around a dedicated entry of the existing React frontend (`frontend/desktop.html` →
`frontend/src/desktop/`). One in-memory session at a time; no database, no login, no local models.
All analysis runs in the existing Colab notebook.

**Flow:** Connect → Random Topic → Reading → 1/3/5 min → Webcam + mic recording → Upload to Drive →
Colab notebook analyses it → Dashboard of the real report → Start New Session.

## How the Colab handoff works

The notebook has no remote API, so the app uses Google Drive as the hand-off point:

1. The app (scope `drive.file`, so it sees only files it created) makes a `SpeakWise Desktop` folder
   with `colab_heartbeat.json`, and per session uploads `recording_<id>.mp4`, `session_<id>.json` (topic,
   exact reading text, duration, file IDs) and a placeholder `report_<id>.json` (`{"status":"pending"}`).
2. **Manual step:** someone runs the notebook (sections 1–4, then **13. Desktop app worker**) with the
   same Google account. Uploading to Drive does not start Colab on its own.
3. The worker updates the heartbeat every 15 s, runs `process_session` for each pending session and
   writes `{"status":"done","session_id":…,"report":{…}}` (or `"error"`) into the placeholder report.
4. The app polls the report every 10 s. It checks the session ID, topic, SHA-256 of the reading text,
   schema version and every metric's value/status before showing anything. **Import report file** on
   the analysis screen accepts the same envelope if automatic retrieval fails.
5. **Start New Session** / **Discard** deletes the local temp files and the session's Drive files.

## Setup

Requires Node 22+.

```powershell
cd desktop
npm install
npm --prefix ../frontend install
```

### Google OAuth client (one-off)

1. Google Cloud Console → create a project → enable the **Google Drive API**.
2. OAuth consent screen: External, Testing mode. Add the Google account(s) you will use as test users.
   Scope: `.../auth/drive.file`.
3. Credentials → Create OAuth client ID → **Desktop app**.
4. Copy `speakwise.config.example.json` to `speakwise.config.json` (this folder, or
   `%APPDATA%\speakwise-desktop\`) and fill in the client ID and secret. Alternatively, set
   `SPEAKWISE_GOOGLE_CLIENT_ID` / `SPEAKWISE_GOOGLE_CLIENT_SECRET`. The file is git-ignored. For a
   Desktop client, Google does not treat the secret as confidential.

Sign-in uses the system browser with a loopback redirect and PKCE. The refresh token is encrypted with
Electron `safeStorage` (Windows DPAPI) in the app's user-data folder; it is never logged.

`colabNotebookUrl` defaults to the notebook on `main`. Point it at another branch if the worker section
has not been merged yet.

## Run

```powershell
npm start          # builds the desktop UI, then launches Electron
npm run start:only # launch without rebuilding
```

## Checks

```powershell
npm test                              # desktop: IPC input validation + MP4 conversion (ffmpeg-static)
npm run smoke                         # launches Electron, verifies the UI loads without renderer errors
npm --prefix ../frontend run test:desktop   # report validation: statuses, mismatches, malformed reports
npm --prefix ../frontend run build:desktop  # typecheck + build
```

## College-PC end-to-end test (needs real Colab)

1. `npm start` → **Connect Google** → approve in the browser → Test Connection shows authorization and
   file transfer as passed.
2. **Open Colab Notebook** → Runtime → change to GPU → run sections 1–4, then section 13 (approve the
   Colab Drive access prompt with the same account).
3. Test Connection in the app → inference row passes → **Ready**.
4. Random Topic → read → 1 minute → record → **Upload and analyse**. The status should go from
   "Waiting for Colab report" to "Colab is analysing" to the dashboard. The notebook cell prints the
   session ID.
5. Check that the dashboard's topic matches, then press **Start New Session** and confirm the session's
   files are gone from the `SpeakWise Desktop` Drive folder.

## Known limitations of this draft

- The reading passages are prepared texts of roughly 400–1,100 words (2–6 min of reading), not 15 min.
  No content-generation service is configured.
- Not packaged as an installer yet (no electron-builder). It runs from the repo with `npm start`.
- Closing the app mid-analysis loses the in-memory session. Its Drive files stay so they can be recovered by hand.
- The worker relies on the notebook's existing `poc_model` clone; `process_session` is unchanged.
