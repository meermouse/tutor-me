# Chinese Audio Lesson Generator — Design Spec

**Date:** 2026-05-01  
**Status:** Approved

---

## Overview

A local web application for learning spoken Mandarin Chinese. The user provides a topic and a list of words/phrases; Claude generates a structured lesson script; the user reviews and edits it; the app produces a single MP3 audio file with spoken examples, slow repetitions, and timed pauses — a personalised, on-demand Pimsleur-style lesson.

---

## Goals

- Generate audio lessons from a user-supplied word list
- Pure audio output — no screen needed during the lesson
- AI generates the lesson script; the user reviews and edits before audio is produced
- Runs locally; designed to be hostable later without significant rework

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | React (Vite), plain CSS |
| Backend | Python, FastAPI |
| Lesson generation | Anthropic Claude API |
| Text-to-speech | Google Cloud TTS |
| Audio stitching | pydub + ffmpeg |
| Config | python-dotenv (.env file) |

---

## Architecture & Data Flow

```
User (browser)
  │
  ├─ POST /generate-script  →  FastAPI  →  Claude API
  │    (topic + word list)       │           (returns script text)
  │                              └──────────────────────────────→ script text
  │
  ├─ POST /generate-audio   →  FastAPI  →  Google Cloud TTS (per segment)
  │    (script text)             │           (spoken audio chunks)
  │                              ├─ pydub stitches chunks + silence
  │                              └──────────────────────────────→ MP3 file
  │
  └─ GET /health            →  FastAPI  →  200 OK
```

No database. Lessons are stateless — word list in, MP3 out. API keys are stored in a `.env` file and never leave the local machine.

---

## Script Format

The lesson script is plain text. Each line starts with a marker that controls voice and timing.

| Marker | Effect |
|---|---|
| `[EN]` | English voice — instructions and context |
| `[ZH]` | Mandarin voice, normal speaking rate |
| `[ZH SLOW]` | Mandarin voice at ~70% speaking rate — for repetition |
| `[PAUSE Ns]` | N seconds of silence |

### Example Script (word: 左 zuǒ — "left")

```
[EN] In this lesson we'll practice directions.
[PAUSE 2s]
[EN] The word for "left" is:
[ZH] 左
[PAUSE 4s]
[EN] Repeat after me, slowly:
[ZH SLOW] 左
[PAUSE 5s]
[EN] Now in a sentence — "Turn left at the traffic light":
[ZH] 在红绿灯左转
[PAUSE 5s]
[ZH SLOW] 在红绿灯左转
[PAUSE 6s]
[EN] Once more:
[ZH] 左转
[PAUSE 4s]
```

Claude is prompted to produce exactly this format. Because the script is plain text, the user can edit it in a standard text area before audio is generated.

---

## Backend

### Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/generate-script` | Receives topic + word list, calls Claude, returns script text |
| POST | `/generate-audio` | Receives script text, produces and returns MP3 |
| GET | `/health` | Health check |

### Audio Generation Pipeline (`/generate-audio`)

1. Split script into lines; classify each by marker
2. For `[EN]` lines: call Google Cloud TTS with an English voice (`en-US-Neural2-F`)
3. For `[ZH]` lines: call Google Cloud TTS with Mandarin voice (`cmn-CN-Wavenet-D`), normal rate
4. For `[ZH SLOW]` lines: same Mandarin voice at 70% speaking rate
5. For `[PAUSE Ns]` lines: generate N seconds of silence as an audio segment
6. Stitch all segments in order using pydub; export as MP3
7. Stream the MP3 back to the frontend

### Claude Prompt Design

The system prompt instructs Claude to:
- Act as a Mandarin lesson designer
- Use the exact marker format
- Apply a spaced repetition structure per word: first encounter → slow repeat → sentence context → sentence repeat → quick recall
- Write natural, useful example sentences appropriate to the topic

### CORS

FastAPI must allow requests from the React dev server origin (`http://localhost:5173`). The `fastapi.middleware.cors` middleware is configured to permit this. For future hosting, the allowed origin is updated to the deployed frontend URL.

### Python Dependencies

```
fastapi
uvicorn
anthropic
google-cloud-texttospeech
pydub
python-dotenv
```

ffmpeg must be installed locally for pydub to export MP3 files.

---

## Frontend

Single-page React app (Vite). Three sequential panels:

### Panel 1 — Input
- Text field: lesson topic (e.g. "directions at a train station")
- Text area: words/phrases, one per line
- "Generate Script" button — calls `/generate-script`, shows loading spinner

### Panel 2 — Script Editor
- Appears after script is returned
- Editable `<textarea>` pre-filled with the generated script
- "Generate Audio" button — sends edited script to `/generate-audio`

### Panel 3 — Audio Player
- Appears once MP3 is ready
- HTML5 `<audio>` element with play/pause/seek
- "Download MP3" button
- "Start Over" button to reset

### Styling
Plain CSS — clean, minimal, readable. No UI component library. Function over form for a local tool.

### State Management
Plain React `useState`. No context or external state library needed.

---

## Project Structure

```
tutor-me/
├── frontend/          # React (Vite) app
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── index.html
│   └── package.json
├── backend/           # FastAPI app
│   ├── main.py
│   ├── script_parser.py
│   ├── tts_client.py
│   ├── audio_builder.py
│   └── requirements.txt
├── .env               # API keys (not committed)
├── .env.example       # Template for API keys
└── README.md
```

---

## Configuration

`.env.example`:
```
ANTHROPIC_API_KEY=your_key_here
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

---

## Out of Scope (for now)

- User accounts or saved lessons
- Vocabulary database or spaced repetition scheduling
- Mobile app
- Any on-screen display during lesson playback
- Multiple language support beyond Mandarin
