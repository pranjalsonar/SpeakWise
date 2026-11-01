# Deploy the SpeakWise backend to the cloud

Use this when the app must work **without your laptop** (always-on address). For a demo where
your laptop is present, [SETUP_LOCAL_TUNNEL.md](SETUP_LOCAL_TUNNEL.md) is simpler.

## Which platform?

The backend analyses video (MediaPipe), so it needs roughly **1 GB RAM and a real CPU** while a
job runs. Checked in November 2026:

| Platform | Cost | Card | Verdict |
|---|---|---|---|
| **Hugging Face Spaces (Docker, CPU Basic)** | Free (2 vCPU / 16 GB) | No | **First choice**, if your account is allowed to create a free Docker Space (see note). |
| **Google Cloud Run** | Free tier covers a demo | Yes | **Fallback.** Reliable; needs a billing account and a budget alert. |
| Render free | 512 MB, 0.1 CPU | No | Too small for video analysis. |
| Railway / Fly.io | Trial only | Yes | Not free. |

> **Note:** In 2026 some users reported that new free Hugging Face accounts cannot create free
> CPU Docker Spaces. Step 1 below tells you within a minute whether your account can.

Everything needed is already in the repo: `backend/Dockerfile`, `backend/.dockerignore`,
`backend/deploy/huggingface/README.md` and the access-key support (`APP_TOKEN`).

---

## Option 1 – Hugging Face Spaces (free, no card)

### 1. Create the Space

1. Sign up / log in at https://huggingface.co
2. Go to https://huggingface.co/new-space
3. Fill in:
   - **Space name:** `speakwise-api`
   - **SDK:** **Docker** → **Blank**
   - **Hardware:** **CPU basic · Free**
   - **Visibility:** **Public** (the app needs to reach it without a Hugging Face login;
     the access key in step 3 protects it)
4. Click **Create Space**.

If **CPU basic · Free** is not selectable or Docker is marked as paid, your account doesn't get
the free tier. Use Option 2 instead.

### 2. Upload the backend

**Easiest – in the browser:** on the Space page open **Files → Add file → Upload files** and
upload these from `D:\madam_project\SpeakWise\backend\`:

- the folders `app\`, `content\`, `scripts\`
- the files `Dockerfile`, `.dockerignore`, `requirements.txt`
- `deploy\huggingface\README.md` → upload it as **README.md** at the top level (replace the
  existing one). Its header (`sdk: docker`, `app_port: 8000`) tells Hugging Face how to run the app.

**Never upload** `.env`, `.venv\`, `data\` or `models\`.

<details>
<summary>Alternative – with git</summary>

```powershell
cd D:\
git clone https://huggingface.co/spaces/<your-username>/speakwise-api hf-speakwise
cd hf-speakwise
robocopy D:\madam_project\SpeakWise\backend . /E /XD .venv data models tools deploy __pycache__ /XF .env
copy D:\madam_project\SpeakWise\backend\deploy\huggingface\README.md README.md
git add .
git commit -m "Deploy SpeakWise backend"
git push
```

When git asks for a password, use a Hugging Face **access token** with *write* permission
(Settings → Access Tokens).
</details>

### 3. Add the secrets

Space → **Settings → Variables and secrets → New secret**, add:

| Name | Value |
|---|---|
| `GROQ_API_KEY` | your Groq key |
| `DEEPGRAM_API_KEY` | your Deepgram key |
| `APP_TOKEN` | any long random phrase, e.g. `speakwise-demo-7f3k9q` |

`APP_TOKEN` stops strangers from using your free API quota through the public URL.

### 4. Wait for the build

The **Logs** tab shows the Docker build (about 5–10 minutes the first time; it downloads the
models during the build). When the status turns **Running**, open:

```
https://<your-username>-speakwise-api.hf.space/health
```

You should see `"status":"ok"`, `"articles":25` and `"access_key_required":true`.

### 5. Connect the app

In the app: **Profile → Server**

- **Server address:** `https://<your-username>-speakwise-api.hf.space`
- **Access key:** the same `APP_TOKEN` value

Tap **Save & test connection** → *Connected · 25 articles on the server*.

### 6. Updating later

Upload the changed files again (or `git push`). The Space rebuilds automatically. If you change
the articles, run `node content/build-articles.mjs` first and upload `content\articles.json`.

### Things to know

- Free Spaces **sleep** after a period without visitors. The first request wakes it up and can
  take a minute or more. Before a demo, open the `/health` address in a browser and wait for it.
- Free Space storage is temporary: finished job records are lost when the Space restarts. That is
  fine, because reports are saved on the phone, and the app re-uploads automatically if a job is lost.

---

## Option 2 – Google Cloud Run (free tier, card required)

Cloud Run's monthly free allowance (about 240,000 vCPU-seconds for always-allocated CPU, plus
free requests) is far more than a demo uses, but Google requires a billing account. A **budget
alert** makes sure you notice any cost straight away.

### 1. Project and budget

1. Go to https://console.cloud.google.com, create a project `speakwise`.
2. **Billing** → link a billing account (card).
3. **Billing → Budgets & alerts → Create budget**: amount ₹100 (or $1), alerts at 50 / 90 / 100 %.

### 2. Put the code on GitHub

The repo must be on GitHub (it already is: `SpeakWise`). Make sure `backend/.env` is **not**
committed (it is in `.gitignore`), and that `backend/content/articles.json` **is** committed.

### 3. Create the service (no local tools needed)

**Cloud Run → Deploy container → Service → Continuously deploy from a repository** →
**Set up with Cloud Build** → connect GitHub → choose the `SpeakWise` repo and branch `main` →
**Build type: Dockerfile**, source location `/backend/Dockerfile`.

Then set:

| Setting | Value | Why |
|---|---|---|
| Region | `us-central1` (or another free-tier region) | Free allowance applies there |
| Authentication | **Allow public access** | The app calls it directly; `APP_TOKEN` protects it |
| Billing | **Instance-based** ("CPU always allocated") | Analysis runs in the background after the upload returns; with request-based billing the CPU is paused and jobs stall |
| Minimum instances | `0` | Scale to zero when unused (free) |
| Maximum instances | `1` | Jobs are kept in one instance's memory/disk |
| Memory / CPU | `2 GiB` / `1` | Enough for MediaPipe + embeddings |
| Request timeout | `300` seconds | Uploads on slow connections |
| Variables | `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, `APP_TOKEN` | (Secret Manager is better for production) |

Click **Create**. The first build takes about 10 minutes.

### 4. Connect the app

Copy the service URL (`https://speakwise-xxxxx-uc.a.run.app`), check `/health` in a browser, then
enter it with the access key in the app under **Profile → Server**.

### Things to know

- After about 15 minutes without requests the service scales to zero; the next request takes
  20–40 seconds to start.
- Keep **maximum instances = 1**: job status is stored inside the instance, so a second instance
  would not know about jobs created on the first.
- Watch **Billing → Reports** after your first few runs; it should show ₹0.

---

## After deploying: build the APK

Once you have a permanent `https://` address, the APK can be built with EAS (next step in
`docs/BUILD_PLAN.md`, 8.4). Users still enter the address and access key once under
**Profile → Server**, or we can bake the address in as the default.
