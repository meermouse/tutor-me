# Netlify + Railway Deployment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the React frontend to Netlify and the FastAPI backend to Railway so the app is publicly accessible.

**Architecture:** Netlify hosts the compiled React static site. Railway hosts the FastAPI Python server with ffmpeg installed via nixpacks. The frontend reads the backend URL from an environment variable at build time, so local dev and production both work without code changes.

**Tech Stack:** Netlify (static hosting), Railway (Python + nixpacks, ffmpeg), Vite env vars (`VITE_API_URL`), Google Cloud service account credentials via JSON env var.

> **Working directory:** All file changes are inside `.worktrees/feature/chinese-audio-lesson-generator/` — that is where the app code lives. File paths below are relative to that directory.

---

## Why Railway for the backend?

Netlify Functions (Lambda) cannot run ffmpeg, have a 10-second timeout, and have no writable filesystem — all of which pydub requires. Railway runs a real Linux container, supports nixpacks to install ffmpeg as a system package, and does not sleep on inactivity.

---

## File Structure

Files created or modified by this plan:

```
(worktree root)
├── frontend/
│   ├── src/
│   │   └── api.js                    MODIFY — use VITE_API_URL env var
│   └── netlify.toml                  CREATE — Netlify build config
├── backend/
│   ├── main.py                       MODIFY — CORS reads from env var
│   ├── tts_client.py                 MODIFY — credentials from JSON env var
│   ├── Procfile                      CREATE — Railway start command
│   └── nixpacks.toml                 CREATE — tells Railway to install ffmpeg
```

---

## Task 1: Frontend — configurable API URL

**Files:**
- Modify: `frontend/src/api.js`

The hardcoded `http://localhost:8000` will break in production. Vite exposes env vars prefixed with `VITE_` to the browser bundle via `import.meta.env`.

- [ ] **Step 1: Update `api.js` to read the API base URL from an env var**

Replace the first line of `frontend/src/api.js`:

```js
// Before:
const API_BASE = 'http://localhost:8000'

// After:
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
```

The full file after the change:

```js
const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function generateScript(title, topic, wordList) {
  const response = await fetch(`${API_BASE}/generate-script`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, topic, word_list: wordList }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Script generation failed: ${detail}`)
  }
  return response.json()
}

export async function generateAudio(script) {
  const response = await fetch(`${API_BASE}/generate-audio`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script }),
  })
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Audio generation failed: ${detail}`)
  }
  return response.blob()
}
```

- [ ] **Step 2: Verify local dev still works**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` — the app should behave exactly as before (no `VITE_API_URL` set = falls back to localhost). Stop the server.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: read backend URL from VITE_API_URL env var for deployment"
```

---

## Task 2: Frontend — Netlify build config

**Files:**
- Create: `frontend/netlify.toml`

Netlify needs to know the build command and where the compiled output lives. We also need a redirect rule so that React's client-side routing doesn't 404 on page refresh (even though this app is a single panel, it's good practice).

- [ ] **Step 1: Create `frontend/netlify.toml`**

```toml
[build]
  command   = "npm run build"
  publish   = "dist"

[[redirects]]
  from   = "/*"
  to     = "/index.html"
  status = 200
```

- [ ] **Step 2: Commit**

```bash
git add frontend/netlify.toml
git commit -m "chore: add netlify.toml build config for frontend"
```

---

## Task 3: Backend — CORS reads allowed origin from env var

**Files:**
- Modify: `backend/main.py`

The hardcoded `http://localhost:5173` will reject requests from the Netlify domain. We read a comma-separated list of origins from `CORS_ORIGINS`, falling back to localhost for local dev.

- [ ] **Step 1: Update CORS middleware in `backend/main.py`**

Find the `app.add_middleware(CORSMiddleware, ...)` block and replace it:

```python
# Before:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# After:
_cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`os` is already imported at the top of `main.py` via `load_dotenv`. Confirm the import is present — if not, add `import os` near the top.

- [ ] **Step 2: Run the API tests to confirm nothing broke**

```bash
cd backend
.venv\Scripts\activate
pytest tests/test_api.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: CORS origins configurable via CORS_ORIGINS env var"
```

---

## Task 4: Backend — Google Cloud credentials from env var

**Files:**
- Modify: `backend/tts_client.py`

Locally, the Google TTS client reads credentials from the path in `GOOGLE_APPLICATION_CREDENTIALS`. On Railway there is no filesystem to store a JSON key file, so we store the entire key JSON as a single env var `GOOGLE_APPLICATION_CREDENTIALS_JSON` and build the client credentials at runtime.

The change is backward-compatible: if `GOOGLE_APPLICATION_CREDENTIALS_JSON` is not set, the client falls back to the default file-path behaviour (local dev still works unchanged).

- [ ] **Step 1: Update `backend/tts_client.py`**

```python
from __future__ import annotations
import json
import os
from google.cloud import texttospeech
from google.oauth2 import service_account

_EN_VOICE = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Neural2-F",
)
_ZH_VOICE = texttospeech.VoiceSelectionParams(
    language_code="cmn-CN",
    name="cmn-CN-Wavenet-D",
)
_MP3_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)
_MP3_SLOW_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3,
    speaking_rate=0.7,
)


def _make_client() -> texttospeech.TextToSpeechClient:
    json_str = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if json_str:
        info = json.loads(json_str)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return texttospeech.TextToSpeechClient(credentials=creds)
    return texttospeech.TextToSpeechClient()


def synthesize(text: str, lang: str, slow: bool) -> bytes:
    client = _make_client()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = _EN_VOICE if lang == "en" else _ZH_VOICE
    audio_config = _MP3_SLOW_CONFIG if (lang == "zh" and slow) else _MP3_CONFIG
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )
    return response.audio_content
```

- [ ] **Step 2: Confirm API tests still pass**

```bash
pytest tests/test_api.py -v
```

Expected: all 4 tests PASS (the TTS client is mocked in these tests, so credentials don't matter).

- [ ] **Step 3: Commit**

```bash
git add backend/tts_client.py
git commit -m "feat: Google Cloud TTS credentials from JSON env var for hosted deployment"
```

---

## Task 5: Backend — Railway config files

**Files:**
- Create: `backend/Procfile`
- Create: `backend/nixpacks.toml`

Railway auto-detects Python via nixpacks. We need two small config files:
- `Procfile` — tells Railway how to start the server and which port to bind
- `nixpacks.toml` — tells nixpacks to install `ffmpeg` as a system package (pydub needs it)

- [ ] **Step 1: Create `backend/Procfile`**

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Railway injects `$PORT` automatically. `--host 0.0.0.0` is required to accept external connections.

- [ ] **Step 2: Create `backend/nixpacks.toml`**

```toml
[phases.setup]
nixPkgs = ["ffmpeg"]
```

This instructs nixpacks (Railway's build system) to install ffmpeg before building the Python environment.

- [ ] **Step 3: Commit**

```bash
git add backend/Procfile backend/nixpacks.toml
git commit -m "chore: add Railway deployment config (Procfile + nixpacks ffmpeg)"
```

---

## Task 6: Deploy backend to Railway

This task is mostly manual clicks in the Railway dashboard. You will need a free Railway account (railway.app — sign up with GitHub).

- [ ] **Step 1: Push the feature branch to GitHub**

```bash
git push origin chinese-audio-lesson-generator
```

- [ ] **Step 2: Create a new Railway project**

1. Go to railway.app → **New Project** → **Deploy from GitHub repo**
2. Select the `tutor-me` repository
3. When asked which branch, select `chinese-audio-lesson-generator`
4. Railway will detect the Python project and start a build

- [ ] **Step 3: Set the root directory**

Railway needs to know the backend lives in `/backend`, not the repo root.

In the Railway service settings → **Source** tab:
- Set **Root Directory** to `/backend`

Trigger a redeploy after saving.

- [ ] **Step 4: Set environment variables in Railway**

In the service → **Variables** tab, add:

| Variable | Value |
|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | The full contents of your Google service account JSON file (paste the entire JSON as one line or multi-line — Railway handles it) |
| `CORS_ORIGINS` | Leave blank for now — you'll fill this in after Netlify is deployed |

To get the JSON value: open your service account `.json` file in a text editor, select all, copy.

- [ ] **Step 5: Confirm deployment succeeded**

Once the build finishes, Railway shows a public URL like `https://tutor-me-backend-production.up.railway.app`.

Open `https://<your-railway-url>/health` in a browser.

Expected: `{"status":"ok"}`

Copy this URL — you'll need it in Task 7.

---

## Task 7: Deploy frontend to Netlify

- [ ] **Step 1: Create a new Netlify site from Git**

1. Log in to netlify.com → **Add new site** → **Import an existing project**
2. Connect to GitHub → select the `tutor-me` repo
3. Select branch: `chinese-audio-lesson-generator`
4. Set **Base directory** to `frontend`
5. Build command: `npm run build` (Netlify reads netlify.toml but the UI lets you confirm)
6. Publish directory: `dist`

- [ ] **Step 2: Set the environment variable**

In Netlify → Site settings → **Environment variables**:

| Variable | Value |
|---|---|
| `VITE_API_URL` | Your Railway backend URL, e.g. `https://tutor-me-backend-production.up.railway.app` |

No trailing slash.

- [ ] **Step 3: Trigger a deploy**

In Netlify → **Deploys** → **Trigger deploy** → Deploy site.

Wait for the build to complete (~1–2 minutes). Netlify shows a public URL like `https://tutor-me-abc123.netlify.app`.

Copy this URL — you need it for CORS.

---

## Task 8: Wire CORS and verify end-to-end

- [ ] **Step 1: Set CORS_ORIGINS on Railway**

Go back to Railway → your backend service → **Variables**:

Set `CORS_ORIGINS` to your Netlify URL, e.g.:
```
https://tutor-me-abc123.netlify.app
```

If you also want local dev to keep working against the production backend (optional), comma-separate:
```
https://tutor-me-abc123.netlify.app,http://localhost:5173
```

Railway will automatically redeploy on variable change.

- [ ] **Step 2: Verify the full flow on the live site**

Open your Netlify URL in a browser and test:

1. Enter a lesson title, topic, and a few words
2. Click **Generate Script** — spinner appears, then the script editor loads with a Claude-generated script
3. Click **Generate Audio** — spinner runs while TTS and pydub process the audio (may take 20–60 seconds depending on lesson length)
4. The audio player appears — press play and confirm you hear the lesson
5. Click **Download MP3** — file downloads

If anything fails, open the browser DevTools → Network tab to check which request is failing and what error it returns.

- [ ] **Step 3: Final commit (if any local fixes were needed)**

```bash
git add -p   # stage only the files you changed
git commit -m "fix: <whatever you had to fix>"
git push origin chinese-audio-lesson-generator
```

---

## Troubleshooting Reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `/health` returns 502 on Railway | Server not binding to `$PORT` | Confirm Procfile uses `--port $PORT` |
| CORS error in browser | `CORS_ORIGINS` not set or wrong URL | Check Railway env var matches Netlify URL exactly |
| Audio generation times out | ffmpeg not installed | Check Railway build logs for nixpacks ffmpeg install step |
| Google TTS auth error | JSON env var malformed | Paste the raw JSON again; ensure no extra quotes wrapping it |
| `VITE_API_URL` is `undefined` | Env var not set before deploy | Set in Netlify env vars, then retrigger a deploy |
| 422 on `/generate-script` | Request body missing `word_list` | Frontend sending wrong field name — check `api.js` serialisation |
