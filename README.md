# Tutor Me — Mandarin Audio Lesson Generator

A local web app that generates personalised Pimsleur-style Mandarin listening lessons. Provide a topic and a word list, Claude generates a lesson script, you review it, and the app produces a single MP3 with English instructions, Mandarin speech, slow repetitions, and timed pauses.

## Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com)
- A Google Cloud project with the [Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com) enabled, and a service account JSON key file

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/meermouse/tutor-me.git
cd tutor-me
```

### 2. Set up the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
```

Copy the example environment file and fill in your credentials:

```powershell
copy .env.example .env
```

Edit `backend\.env`:

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account.json
```

### 3. Set up the frontend

```powershell
cd frontend
npm install
```

## Starting the app

Open two terminals.

**Terminal 1 — Backend** (runs on port 8000):

```powershell
cd backend
.\start.ps1
```

**Terminal 2 — Frontend** (runs on port 5173):

```powershell
cd frontend
npm run dev
```

Then open `http://localhost:5173` in your browser.

## Usage

1. Enter a lesson title, topic, and a list of words/phrases (one per line)
2. Click **Generate Script** — Claude writes a structured lesson script
3. Review and edit the script if needed
4. Click **Generate Audio** — the app calls Google Cloud TTS and stitches an MP3
5. Play the lesson directly in the browser or click **Download MP3**
6. Previously generated lessons are saved automatically and listed at the top of the page

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for script generation |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account JSON |

## Running tests

```powershell
cd backend
.venv\Scripts\pytest
```
