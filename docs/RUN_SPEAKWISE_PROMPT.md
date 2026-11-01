# Claude Code prompt: run SpeakWise and hand the APK to a phone

Paste everything below into Claude Code, from a session opened in
`D:\madam_project\SpeakWise`. Claude Code will start the backend, open the
Cloudflare tunnel, build/collect the APK into one folder, and serve that folder
so an Android phone can download the APK over the tunnel.

---

You are running the SpeakWise demo for me end to end. Do the steps in order.
After each step, tell me in one line whether it succeeded. If a step fails, stop,
show me the relevant log lines, and wait for me — do not guess past a failure.

Paths:
- Backend: `D:\madam_project\SpeakWise\backend`
- App (Expo project): find it under `D:\madam_project\SpeakWise` (look for `app.json` / `eas.json`)
- Delivery folder (create it): `D:\madam_project\SpeakWise\dist`

## Step 1 — Pre-flight checks
- Confirm `backend\.env` exists and contains `GROQ_API_KEY` and `DEEPGRAM_API_KEY`. Do NOT print the key values — just confirm each is present and non-empty.
- Confirm `cloudflared` is available (`cloudflared --version`). If it is missing, tell me to run `winget install --id Cloudflare.cloudflared` in a new terminal, then stop.
- Confirm the Python venv exists at `backend\.venv`. If not, create it and install `requirements.txt`.

## Step 2 — Start the backend
- Start it in the background:
  `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
  from the `backend` folder.
- Wait until `http://localhost:8000/health` returns `"status":"ok"`.
- If port 8000 is already in use, reuse the running backend instead of starting a second one.

## Step 3 — Start the Cloudflare tunnel
- Run `cloudflared tunnel --no-autoupdate --url http://localhost:8000` in the background.
- Read its output and capture the `https://<random>.trycloudflare.com` address.
- Verify the tunnel works: open `https://<address>/health` and confirm `"status":"ok"`.
- Show me the full address. This address changes every run, so it is never baked into the APK.

## Step 4 — Get the APK into the delivery folder
Create `D:\madam_project\SpeakWise\dist` if it does not exist. Then get an installable APK into it, trying these in order:

1. **If an APK already exists** anywhere under the project (search for `*.apk`), copy the newest one into `dist\SpeakWise.apk` and skip to Step 5.
2. **Local Expo/EAS build** (no Expo account needed if the Android SDK is set up):
   from the app folder, run `npx eas build --platform android --profile preview --local`, then copy the produced `.apk` into `dist\SpeakWise.apk`.
3. **Cloud EAS build** (needs me logged in to Expo): run `npx eas build --platform android --profile preview`, wait for it, download the artifact, and save it as `dist\SpeakWise.apk`.

If none of these can run (missing Android SDK for local, not logged in for cloud), stop and tell me exactly what is missing and the one command I need to run. Do not fabricate an APK.

Do NOT hardcode the tunnel address into the build — the address is entered in the app at runtime (Profile → Server), so the same APK keeps working across restarts.

## Step 5 — Serve the delivery folder so the phone can download the APK
- Serve `D:\madam_project\SpeakWise\dist` over HTTP on a free port, e.g. port 8080:
  `python -m http.server 8080 --directory D:\madam_project\SpeakWise\dist` (run in background).
- Start a second quick tunnel for it:
  `cloudflared tunnel --no-autoupdate --url http://localhost:8080`
- Capture that second `https://<random>.trycloudflare.com` address — this is the **download link**.
- Confirm `https://<download-address>/SpeakWise.apk` returns the file (check it responds with a non-zero size).

## Step 6 — Print a summary for me to use
Print a block exactly like this, filled in:

```
SpeakWise is ready.

APK download (open this on the Android phone's browser):
  https://<download-address>/SpeakWise.apk

Backend/server address (paste into the app → Profile → Server → Server address):
  https://<backend-address>

Access key: leave empty (unless APP_TOKEN is set in backend\.env)
```

Then remind me: keep both tunnel windows open for the whole demo, the laptop must
stay awake, and if I restart a tunnel its address changes so I re-paste the new
server address in the app. The APK itself never needs rebuilding unless the app's
code changes.

## Housekeeping
- Keep all long-running processes (backend, both tunnels, the file server) alive until I say stop. When I say "stop", shut them all down cleanly.
- Keep logs where the project already puts them (`backend\data\logs\`), and tell me the path if anything fails.
- Never print secret values from `.env`.
