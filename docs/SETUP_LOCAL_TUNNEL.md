# Run SpeakWise from your laptop (free Cloudflare tunnel)

This runs the backend on your laptop and gives it a free public `https://…trycloudflare.com`
address, so the app works from **any network** (Wi‑Fi or mobile data), including the release APK.
No account, no card, no cost. It is the same approach the Colab POC used.

**Trade-offs:** the laptop must stay on and connected during the demo, and the address changes
every time you restart the tunnel (you paste the new one into the app; it takes 10 seconds).

```
Phone (Expo Go or APK) ──https──► Cloudflare ──tunnel──► your laptop :8000 (FastAPI)
                                                          └─► Groq / Deepgram APIs
```

---

## 1. One-time: backend ready

You only need to do this once (already done on this laptop).

```powershell
cd D:\madam_project\SpeakWise\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
```

`backend\.env` must contain your keys:

```
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=...
```

## 2. One-time: get `cloudflared` (about 60 MB)

Pick **one** option.

**Option A – winget (simplest)**

```powershell
winget install --id Cloudflare.cloudflared
```

Close and reopen the terminal, then check: `cloudflared --version`

**Option B – download the file (no installer)**

1. Open https://github.com/cloudflare/cloudflared/releases/latest
2. Download `cloudflared-windows-amd64.exe`
3. Save it as `D:\madam_project\SpeakWise\backend\tools\cloudflared.exe`
   (create the `tools` folder; it is ignored by git)

## 3. Every time: start everything with one command

```powershell
cd D:\madam_project\SpeakWise\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force   # allows scripts in this window only
.\scripts\start-demo.ps1
```

The script:

1. starts the backend (or reuses it if it is already running),
2. starts the tunnel,
3. prints the public address and copies it to the clipboard:

```
  SpeakWise is online at:
  https://some-random-words.trycloudflare.com
```

Keep this window open. **Ctrl+C** stops the tunnel and the backend.

Logs are in `backend\data\logs\` (`backend.log`, `cloudflared.log`).

<details>
<summary>Prefer to run the two parts by hand?</summary>

Terminal 1 – backend:

```powershell
cd D:\madam_project\SpeakWise\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2 – tunnel (look for the `https://…trycloudflare.com` line):

```powershell
cloudflared tunnel --no-autoupdate --url http://localhost:8000
```

</details>

## 4. Check it works

Open `https://<your-address>/health` in the phone's browser. You should see:

```json
{"status":"ok","articles":25,"providers":{"groq":true,"deepgram":true}}
```

## 5. Point the app at it

In the app: **Profile → Server → Server address** → paste the `https://…` address →
**Save & test connection** → you should see *Connected · 25 articles on the server*.

Leave **Access key** empty (it is only needed for public cloud deployments).

---

## Demo-day checklist

- [ ] Laptop plugged in; Windows sleep set to **Never** (Settings → System → Power & sleep).
- [ ] Run `start-demo.ps1`, copy the new address.
- [ ] Paste it in the app on every demo phone (Profile → Server → Save & test).
- [ ] Do one full practice run before the audience arrives (first run is slower while models warm up).
- [ ] Keep the script window open for the whole demo.

## Troubleshooting

| Problem | Fix |
|---|---|
| `cloudflared was not found` | Do step 2, then open a new terminal. |
| `Backend did not start` | Open `backend\data\logs\backend.log`. Usually a missing package (redo step 1) or port 8000 in use (close the other backend window). |
| App says *Can't reach the SpeakWise server* | The address changed: copy the new one from the script and paste it in the app. Make sure it starts with `https://`. |
| Health check works but analysis fails | Check `backend.log`. A `rate limited` message means the free Groq/Deepgram limit was hit; wait a minute. |
| Upload is slow | Normal on slow laptop internet: the video (about 10–25 MB) travels phone → Cloudflare → laptop. |

## Notes

- Quick tunnels are meant for testing and demos: no uptime guarantee and a new address each time.
  For an always-on address, see [DEPLOY_CLOUD.md](DEPLOY_CLOUD.md).
- The tunnel makes an outgoing connection, so no router or Windows Firewall changes are needed.
- Anyone who knows the random address could use the backend while it runs. For a short demo this
  is fine; if you want to lock it, set `APP_TOKEN=some-secret` in `backend\.env`, restart, and type
  the same value in the app under **Access key**.
