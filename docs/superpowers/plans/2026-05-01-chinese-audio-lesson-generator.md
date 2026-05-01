# Chinese Audio Lesson Generator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local web app where the user inputs a word list, Claude generates a Mandarin lesson script, the user edits it, and a stitched MP3 audio lesson is produced.

**Architecture:** React (Vite) single-page frontend calls a FastAPI backend. Backend uses the Anthropic Claude API to generate lesson scripts and Google Cloud TTS to synthesise each script segment into audio; pydub stitches segments and silence into a single MP3 returned to the browser. Lesson scripts are persisted in browser localStorage.

**Tech Stack:** Python 3.11+, FastAPI, pydub + ffmpeg, Anthropic Python SDK, Google Cloud TTS Python client, React 18 (Vite), plain CSS.

---

## Prerequisites (manual — do before Task 1)

1. Install ffmpeg on Windows: `winget install ffmpeg` (or download from ffmpeg.org and add to PATH)
2. Create a Google Cloud project, enable the Cloud Text-to-Speech API, create a service account with the "Cloud Text-to-Speech User" role, download the JSON key file.
3. Obtain an Anthropic API key from console.anthropic.com.

---

## File Structure

```
tutor-me/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, endpoint routing
│   ├── script_parser.py         # Parse marker-format script into typed segments
│   ├── script_generator.py      # Claude API call — returns raw script text
│   ├── tts_client.py            # Google Cloud TTS wrapper
│   ├── audio_builder.py         # Stitch TTS chunks + silence into MP3 bytes
│   ├── requirements.txt         # Runtime dependencies
│   ├── requirements-dev.txt     # Test-only dependencies
│   └── tests/
│       ├── __init__.py
│       ├── test_script_parser.py
│       ├── test_audio_builder.py
│       └── test_api.py
├── frontend/
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx              # Root component, all state, panel routing
│   │   ├── App.css              # Global styles
│   │   ├── api.js               # fetch() wrappers for backend endpoints
│   │   ├── hooks/
│   │   │   └── useLessons.js    # localStorage CRUD hook
│   │   └── components/
│   │       ├── SavedLessonsList.jsx
│   │       ├── InputPanel.jsx
│   │       ├── ScriptEditor.jsx
│   │       └── AudioPlayer.jsx
│   ├── index.html
│   └── package.json
├── .env                         # API keys (git-ignored)
├── .env.example                 # Key template committed to repo
└── README.md
```

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/tests/__init__.py`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: Create the backend directory and requirements files**

```
backend/requirements.txt
```
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
anthropic==0.40.0
google-cloud-texttospeech==2.17.2
pydub==0.25.1
python-dotenv==1.0.1
httpx==0.27.2
```

```
backend/requirements-dev.txt
```
```
pytest==8.3.3
pytest-mock==3.14.0
```

- [ ] **Step 2: Create the tests package marker**

Create `backend/tests/__init__.py` as an empty file.

- [ ] **Step 3: Create .env.example**

```
# backend/.env.example  — copy to backend/.env and fill in real values
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/your/service-account.json
```

Also create `backend/.env` (not committed) with your real values.

- [ ] **Step 4: Update .gitignore**

Add to `.gitignore` at the repo root:

```
# Python
backend/.env
backend/__pycache__/
backend/**/__pycache__/
backend/.venv/
backend/*.egg-info/

# Node
frontend/node_modules/
frontend/dist/

# Misc
*.mp3
```

- [ ] **Step 5: Install Python dependencies**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

- [ ] **Step 6: Scaffold the React app**

```bash
cd C:\Code\tutor-me
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

- [ ] **Step 7: Commit**

```bash
git add backend/ frontend/ .gitignore .env.example
git commit -m "feat: project scaffolding — backend + frontend structure"
```

---

## Task 2: Script Parser

**Files:**
- Create: `backend/script_parser.py`
- Create: `backend/tests/test_script_parser.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_script_parser.py`:
```python
import pytest
from script_parser import parse_script, EnglishSegment, MandarinSegment, PauseSegment


def test_parses_english_line():
    segments = parse_script("[EN] Hello there")
    assert len(segments) == 1
    assert isinstance(segments[0], EnglishSegment)
    assert segments[0].text == "Hello there"


def test_parses_mandarin_line():
    segments = parse_script("[ZH] 你好")
    assert len(segments) == 1
    assert isinstance(segments[0], MandarinSegment)
    assert segments[0].text == "你好"
    assert segments[0].slow is False


def test_parses_mandarin_slow_line():
    segments = parse_script("[ZH SLOW] 你好")
    assert len(segments) == 1
    assert isinstance(segments[0], MandarinSegment)
    assert segments[0].text == "你好"
    assert segments[0].slow is True


def test_parses_pause_line():
    segments = parse_script("[PAUSE 4s]")
    assert len(segments) == 1
    assert isinstance(segments[0], PauseSegment)
    assert segments[0].duration == 4.0


def test_parses_multi_line_script():
    script = """[EN] Welcome to the lesson.
[PAUSE 2s]
[ZH] 左
[ZH SLOW] 左
[PAUSE 5s]"""
    segments = parse_script(script)
    assert len(segments) == 5
    assert isinstance(segments[0], EnglishSegment)
    assert isinstance(segments[1], PauseSegment)
    assert isinstance(segments[2], MandarinSegment)
    assert segments[2].slow is False
    assert isinstance(segments[3], MandarinSegment)
    assert segments[3].slow is True
    assert isinstance(segments[4], PauseSegment)
    assert segments[4].duration == 5.0


def test_ignores_blank_lines():
    script = "[EN] Hello\n\n[ZH] 你好\n"
    segments = parse_script(script)
    assert len(segments) == 2


def test_unknown_lines_are_skipped():
    script = "[EN] Hello\nsome random text\n[ZH] 你好"
    segments = parse_script(script)
    assert len(segments) == 2
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend
.venv\Scripts\activate
pytest tests/test_script_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'script_parser'`

- [ ] **Step 3: Implement the parser**

`backend/script_parser.py`:
```python
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Union


@dataclass
class EnglishSegment:
    text: str


@dataclass
class MandarinSegment:
    text: str
    slow: bool = False


@dataclass
class PauseSegment:
    duration: float


Segment = Union[EnglishSegment, MandarinSegment, PauseSegment]

_PAUSE_RE = re.compile(r'^\[PAUSE (\d+(?:\.\d+)?)s\]$')


def parse_script(script: str) -> list[Segment]:
    segments: list[Segment] = []
    for raw_line in script.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('[EN] '):
            segments.append(EnglishSegment(text=line[5:]))
        elif line.startswith('[ZH SLOW] '):
            segments.append(MandarinSegment(text=line[10:], slow=True))
        elif line.startswith('[ZH] '):
            segments.append(MandarinSegment(text=line[5:], slow=False))
        elif m := _PAUSE_RE.match(line):
            segments.append(PauseSegment(duration=float(m.group(1))))
    return segments
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
pytest tests/test_script_parser.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/script_parser.py backend/tests/test_script_parser.py backend/tests/__init__.py
git commit -m "feat: script parser with full marker support"
```

---

## Task 3: Audio Builder

**Files:**
- Create: `backend/audio_builder.py`
- Create: `backend/tests/test_audio_builder.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_audio_builder.py`:
```python
import io
import pytest
from pydub import AudioSegment
from script_parser import EnglishSegment, MandarinSegment, PauseSegment
from audio_builder import build_audio


def _make_mp3_bytes(duration_ms: int = 100) -> bytes:
    """Return minimal valid MP3 bytes (silent segment exported by pydub)."""
    silent = AudioSegment.silent(duration=duration_ms)
    buf = io.BytesIO()
    silent.export(buf, format="mp3")
    return buf.getvalue()


def _mock_tts(text: str, lang: str, slow: bool) -> bytes:
    return _make_mp3_bytes(200)


def test_build_audio_returns_bytes():
    segments = [EnglishSegment(text="Hello")]
    result = build_audio(segments, _mock_tts)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_build_audio_handles_pause():
    segments = [PauseSegment(duration=1.0)]
    result = build_audio(segments, _mock_tts)
    audio = AudioSegment.from_mp3(io.BytesIO(result))
    # 1 second silence ± 100ms tolerance
    assert 900 <= len(audio) <= 1100


def test_build_audio_calls_tts_for_each_spoken_segment():
    calls = []

    def recording_tts(text, lang, slow):
        calls.append((text, lang, slow))
        return _make_mp3_bytes()

    segments = [
        EnglishSegment(text="Hello"),
        MandarinSegment(text="你好", slow=False),
        MandarinSegment(text="你好", slow=True),
        PauseSegment(duration=2.0),
    ]
    build_audio(segments, recording_tts)
    assert len(calls) == 3
    assert calls[0] == ("Hello", "en", False)
    assert calls[1] == ("你好", "zh", False)
    assert calls[2] == ("你好", "zh", True)
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_audio_builder.py -v
```

Expected: `ModuleNotFoundError: No module named 'audio_builder'`

- [ ] **Step 3: Implement the audio builder**

`backend/audio_builder.py`:
```python
from __future__ import annotations
import io
from typing import Callable
from pydub import AudioSegment
from script_parser import EnglishSegment, MandarinSegment, PauseSegment, Segment

TtsFn = Callable[[str, str, bool], bytes]


def build_audio(segments: list[Segment], tts_fn: TtsFn) -> bytes:
    combined = AudioSegment.empty()
    for segment in segments:
        if isinstance(segment, PauseSegment):
            combined += AudioSegment.silent(duration=int(segment.duration * 1000))
        elif isinstance(segment, EnglishSegment):
            mp3_bytes = tts_fn(segment.text, "en", False)
            combined += AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
        elif isinstance(segment, MandarinSegment):
            mp3_bytes = tts_fn(segment.text, "zh", segment.slow)
            combined += AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
    output = io.BytesIO()
    combined.export(output, format="mp3")
    return output.getvalue()
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
pytest tests/test_audio_builder.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/audio_builder.py backend/tests/test_audio_builder.py
git commit -m "feat: audio builder — stitch TTS segments and silence into MP3"
```

---

## Task 4: TTS Client

**Files:**
- Create: `backend/tts_client.py`

No unit tests for the TTS client — it is a thin wrapper around an external SDK. It is exercised through the API integration tests in Task 6.

- [ ] **Step 1: Implement the TTS client**

`backend/tts_client.py`:
```python
from __future__ import annotations
from google.cloud import texttospeech

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


def synthesize(text: str, lang: str, slow: bool) -> bytes:
    """Call Google Cloud TTS and return MP3 bytes.

    lang: "en" for English, "zh" for Mandarin.
    slow: only applies when lang == "zh".
    """
    client = texttospeech.TextToSpeechClient()
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

- [ ] **Step 2: Commit**

```bash
git add backend/tts_client.py
git commit -m "feat: Google Cloud TTS client wrapper"
```

---

## Task 5: Script Generator

**Files:**
- Create: `backend/script_generator.py`

No isolated unit tests — exercised through API integration tests in Task 6 with the Claude client mocked.

- [ ] **Step 1: Implement the script generator**

`backend/script_generator.py`:
```python
from __future__ import annotations
import os
import anthropic

_SYSTEM_PROMPT = """\
You are a Mandarin Chinese lesson designer. Generate audio lesson scripts using this exact marker format:

[EN] - English instruction or context
[ZH] - Mandarin at normal speaking rate
[ZH SLOW] - Mandarin at ~70% speaking rate, for the learner to repeat
[PAUSE Ns] - N seconds of silence

Apply this structure for each word or phrase in the lesson:
1. [EN] Brief English introduction
2. [ZH] The word/phrase at normal speed
3. [PAUSE 4s]
4. [EN] Prompt the learner to repeat
5. [ZH SLOW] The word/phrase slowly
6. [PAUSE 5s]
7. [EN] Introduce an example sentence
8. [ZH] The sentence at normal speed
9. [PAUSE 5s]
10. [ZH SLOW] The sentence slowly
11. [PAUSE 6s]

After introducing all words, revisit earlier words inside new sentences to reinforce recall.

Output ONLY the marker-format script. No explanations, no markdown, no preamble.\
"""


def generate_script_text(topic: str, word_list: list[str]) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    words_formatted = "\n".join(f"- {w}" for w in word_list)
    user_message = f"Topic: {topic}\n\nWords and phrases to teach:\n{words_formatted}"
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return message.content[0].text
```

- [ ] **Step 2: Commit**

```bash
git add backend/script_generator.py
git commit -m "feat: Claude API script generator with Pimsleur-style prompt"
```

---

## Task 6: FastAPI App

**Files:**
- Create: `backend/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

`backend/tests/test_api.py`:
```python
import io
import pytest
from fastapi.testclient import TestClient
from pydub import AudioSegment
from unittest.mock import patch


def _minimal_mp3() -> bytes:
    buf = io.BytesIO()
    AudioSegment.silent(duration=100).export(buf, format="mp3")
    return buf.getvalue()


@pytest.fixture()
def client():
    from main import app
    return TestClient(app)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_generate_script_returns_script_text(client):
    fake_script = "[EN] Hello\n[ZH] 你好\n[PAUSE 3s]"
    with patch("main.generate_script_text", return_value=fake_script):
        response = client.post(
            "/generate-script",
            json={"title": "Test", "topic": "greetings", "word_list": ["你好"]},
        )
    assert response.status_code == 200
    assert response.json()["script"] == fake_script


def test_generate_audio_returns_mp3(client):
    script = "[EN] Hello\n[PAUSE 1s]\n[ZH] 你好"
    with patch("main.synthesize", return_value=_minimal_mp3()):
        response = client.post("/generate-audio", json={"script": script})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 0


def test_generate_script_requires_word_list(client):
    response = client.post(
        "/generate-script",
        json={"title": "Test", "topic": "greetings"},
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement main.py**

`backend/main.py`:
```python
from __future__ import annotations
import io
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

from script_generator import generate_script_text
from script_parser import parse_script
from tts_client import synthesize
from audio_builder import build_audio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScriptRequest(BaseModel):
    title: str
    topic: str
    word_list: list[str]


class AudioRequest(BaseModel):
    script: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-script")
def generate_script_endpoint(request: ScriptRequest):
    script = generate_script_text(request.topic, request.word_list)
    return {"script": script}


@app.post("/generate-audio")
def generate_audio_endpoint(request: AudioRequest):
    segments = parse_script(request.script)
    audio_bytes = build_audio(segments, synthesize)
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "attachment; filename=lesson.mp3"},
    )
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
pytest tests/test_api.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Smoke-test the running server**

```bash
uvicorn main:app --reload --port 8000
```

In a separate terminal:
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`

Stop the server (`Ctrl+C`).

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py
git commit -m "feat: FastAPI app with /generate-script, /generate-audio, /health"
```

---

## Task 7: React App Scaffold

**Files:**
- Modify: `frontend/src/main.jsx`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/App.css`
- Modify: `frontend/index.html`

- [ ] **Step 1: Replace the Vite default main.jsx**

`frontend/src/main.jsx`:
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 2: Replace index.html title**

In `frontend/index.html`, change the `<title>` tag to:
```html
<title>Tutor Me — Mandarin Lessons</title>
```

- [ ] **Step 3: Write the base App.jsx shell**

`frontend/src/App.jsx`:
```jsx
import { useState } from 'react'

export default function App() {
  const [panel, setPanel] = useState('input') // 'input' | 'editor' | 'player'
  const [currentLesson, setCurrentLesson] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)

  return (
    <div className="app">
      <h1>Tutor Me</h1>
      <p>Panel: {panel}</p>
    </div>
  )
}
```

- [ ] **Step 4: Write base CSS**

`frontend/src/App.css`:
```css
*, *::before, *::after { box-sizing: border-box; }

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  background: #f9f9f9;
  color: #222;
}

.app {
  max-width: 720px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 2rem;
}

h2 {
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

input[type="text"],
textarea {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
  font-family: inherit;
  background: #fff;
}

textarea {
  resize: vertical;
  min-height: 120px;
}

button {
  padding: 0.5rem 1.25rem;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  background: #2563eb;
  color: #fff;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.secondary {
  background: #e5e7eb;
  color: #222;
}

button.danger {
  background: #dc2626;
  color: #fff;
}

.field {
  margin-bottom: 1rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.spinner {
  display: inline-block;
  width: 1rem;
  height: 1rem;
  border: 2px solid #fff;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  vertical-align: middle;
  margin-right: 0.4rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

.saved-lessons {
  margin-bottom: 2rem;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  padding: 1rem;
}

.saved-lessons ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.saved-lessons li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f3f4f6;
}

.saved-lessons li:last-child { border-bottom: none; }

.saved-lessons .lesson-meta {
  font-size: 0.8rem;
  color: #6b7280;
}

.panel {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1.5rem;
}

audio {
  width: 100%;
  margin-bottom: 1rem;
}
```

- [ ] **Step 5: Verify the dev server starts**

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`. Expected: page shows "Tutor Me" heading and "Panel: input". Stop the server.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: React app scaffold with base styles"
```

---

## Task 8: useLessons Hook

**Files:**
- Create: `frontend/src/hooks/useLessons.js`

- [ ] **Step 1: Create the hooks directory and implement useLessons**

`frontend/src/hooks/useLessons.js`:
```js
import { useState, useEffect } from 'react'

const STORAGE_KEY = 'tutor-me-lessons'

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveToStorage(lessons) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(lessons))
}

export function useLessons() {
  const [lessons, setLessons] = useState(loadFromStorage)

  useEffect(() => {
    saveToStorage(lessons)
  }, [lessons])

  function saveLesson(lesson) {
    setLessons(prev => {
      const exists = prev.findIndex(l => l.id === lesson.id)
      if (exists >= 0) {
        const updated = [...prev]
        updated[exists] = lesson
        return updated
      }
      return [lesson, ...prev]
    })
  }

  function deleteLesson(id) {
    setLessons(prev => prev.filter(l => l.id !== id))
  }

  return { lessons, saveLesson, deleteLesson }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/useLessons.js
git commit -m "feat: useLessons hook — localStorage CRUD for saved lessons"
```

---

## Task 9: API Client

**Files:**
- Create: `frontend/src/api.js`

- [ ] **Step 1: Implement the API client**

`frontend/src/api.js`:
```js
const API_BASE = 'http://localhost:8000'

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
  return response.json() // { script: string }
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
  return response.blob() // MP3 blob
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: API client — fetch wrappers for backend endpoints"
```

---

## Task 10: InputPanel Component

**Files:**
- Create: `frontend/src/components/InputPanel.jsx`

- [ ] **Step 1: Implement InputPanel**

`frontend/src/components/InputPanel.jsx`:
```jsx
import { useState } from 'react'
import { generateScript } from '../api.js'

export default function InputPanel({ onScriptGenerated }) {
  const [title, setTitle] = useState('')
  const [topic, setTopic] = useState('')
  const [wordListRaw, setWordListRaw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleGenerate() {
    if (!title.trim() || !topic.trim() || !wordListRaw.trim()) return
    const wordList = wordListRaw.split('\n').map(w => w.trim()).filter(Boolean)
    setLoading(true)
    setError(null)
    try {
      const { script } = await generateScript(title.trim(), topic.trim(), wordList)
      onScriptGenerated({ title: title.trim(), topic: topic.trim(), wordList, script })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>New Lesson</h2>

      <div className="field">
        <label htmlFor="title">Lesson title</label>
        <input
          id="title"
          type="text"
          placeholder="e.g. Directions — Train Station"
          value={title}
          onChange={e => setTitle(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="topic">Topic (sent to Claude)</label>
        <input
          id="topic"
          type="text"
          placeholder="e.g. asking for directions at a train station"
          value={topic}
          onChange={e => setTopic(e.target.value)}
        />
      </div>

      <div className="field">
        <label htmlFor="words">Words and phrases (one per line)</label>
        <textarea
          id="words"
          placeholder={"左 (zuǒ) — left\n右 (yòu) — right\n直走 — go straight"}
          value={wordListRaw}
          onChange={e => setWordListRaw(e.target.value)}
          rows={6}
        />
      </div>

      {error && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</p>}

      <div className="actions">
        <button onClick={handleGenerate} disabled={loading || !title.trim() || !topic.trim() || !wordListRaw.trim()}>
          {loading && <span className="spinner" />}
          {loading ? 'Generating…' : 'Generate Script'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/InputPanel.jsx
git commit -m "feat: InputPanel component — lesson title, topic, word list input"
```

---

## Task 11: ScriptEditor Component

**Files:**
- Create: `frontend/src/components/ScriptEditor.jsx`

- [ ] **Step 1: Implement ScriptEditor**

`frontend/src/components/ScriptEditor.jsx`:
```jsx
import { useState, useEffect } from 'react'
import { generateAudio } from '../api.js'

export default function ScriptEditor({ lesson, onScriptChange, onAudioGenerated }) {
  const [script, setScript] = useState(lesson.script)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setScript(lesson.script)
  }, [lesson.id])

  function handleScriptChange(e) {
    const updated = e.target.value
    setScript(updated)
    onScriptChange(updated)
  }

  async function handleGenerateAudio() {
    setLoading(true)
    setError(null)
    try {
      const blob = await generateAudio(script)
      const url = URL.createObjectURL(blob)
      onAudioGenerated(url)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>{lesson.title}</h2>
      <p style={{ fontSize: '0.875rem', color: '#6b7280', marginBottom: '0.75rem' }}>
        Review and edit the script below, then generate your audio lesson.
      </p>

      <div className="field">
        <textarea
          value={script}
          onChange={handleScriptChange}
          rows={20}
          style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}
        />
      </div>

      {error && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>{error}</p>}

      <div className="actions">
        <button onClick={handleGenerateAudio} disabled={loading || !script.trim()}>
          {loading && <span className="spinner" />}
          {loading ? 'Generating audio…' : 'Generate Audio'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/ScriptEditor.jsx
git commit -m "feat: ScriptEditor component — editable script textarea with audio generation"
```

---

## Task 12: AudioPlayer Component

**Files:**
- Create: `frontend/src/components/AudioPlayer.jsx`

- [ ] **Step 1: Implement AudioPlayer**

`frontend/src/components/AudioPlayer.jsx`:
```jsx
export default function AudioPlayer({ audioUrl, lessonTitle, onStartOver }) {
  function handleDownload() {
    const a = document.createElement('a')
    a.href = audioUrl
    a.download = `${lessonTitle.replace(/\s+/g, '-').toLowerCase()}.mp3`
    a.click()
  }

  return (
    <div className="panel">
      <h2>Your Lesson is Ready</h2>
      <audio src={audioUrl} controls />
      <div className="actions">
        <button onClick={handleDownload}>Download MP3</button>
        <button className="secondary" onClick={onStartOver}>Start Over</button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AudioPlayer.jsx
git commit -m "feat: AudioPlayer component — HTML5 audio with download and reset"
```

---

## Task 13: SavedLessonsList Component

**Files:**
- Create: `frontend/src/components/SavedLessonsList.jsx`

- [ ] **Step 1: Implement SavedLessonsList**

`frontend/src/components/SavedLessonsList.jsx`:
```jsx
export default function SavedLessonsList({ lessons, onLoad, onDelete }) {
  if (lessons.length === 0) return null

  return (
    <div className="saved-lessons">
      <h2>Saved Lessons</h2>
      <ul>
        {lessons.map(lesson => (
          <li key={lesson.id}>
            <div>
              <strong>{lesson.title}</strong>
              <div className="lesson-meta">
                {new Date(lesson.createdAt).toLocaleDateString()}
              </div>
            </div>
            <div className="actions" style={{ marginTop: 0 }}>
              <button className="secondary" onClick={() => onLoad(lesson)}>
                Load
              </button>
              <button className="danger" onClick={() => onDelete(lesson.id)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SavedLessonsList.jsx
git commit -m "feat: SavedLessonsList component — load and delete saved lessons"
```

---

## Task 14: App.jsx Wiring

**Files:**
- Modify: `frontend/src/App.jsx`

- [ ] **Step 1: Replace App.jsx with the fully wired component**

`frontend/src/App.jsx`:
```jsx
import { useState } from 'react'
import { useLessons } from './hooks/useLessons.js'
import SavedLessonsList from './components/SavedLessonsList.jsx'
import InputPanel from './components/InputPanel.jsx'
import ScriptEditor from './components/ScriptEditor.jsx'
import AudioPlayer from './components/AudioPlayer.jsx'

export default function App() {
  const [panel, setPanel] = useState('input') // 'input' | 'editor' | 'player'
  const [currentLesson, setCurrentLesson] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const { lessons, saveLesson, deleteLesson } = useLessons()

  function handleScriptGenerated({ title, topic, wordList, script }) {
    const lesson = {
      id: crypto.randomUUID(),
      title,
      topic,
      wordList,
      script,
      createdAt: new Date().toISOString(),
    }
    setCurrentLesson(lesson)
    saveLesson(lesson)
    setPanel('editor')
  }

  function handleScriptChange(updatedScript) {
    const updated = { ...currentLesson, script: updatedScript }
    setCurrentLesson(updated)
    saveLesson(updated)
  }

  function handleAudioGenerated(url) {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(url)
    setPanel('player')
  }

  function handleLoadLesson(lesson) {
    setCurrentLesson(lesson)
    setAudioUrl(null)
    setPanel('editor')
  }

  function handleStartOver() {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
    setAudioUrl(null)
    setCurrentLesson(null)
    setPanel('input')
  }

  return (
    <div className="app">
      <h1>Tutor Me</h1>

      <SavedLessonsList
        lessons={lessons}
        onLoad={handleLoadLesson}
        onDelete={deleteLesson}
      />

      {panel === 'input' && (
        <InputPanel onScriptGenerated={handleScriptGenerated} />
      )}

      {panel === 'editor' && currentLesson && (
        <ScriptEditor
          lesson={currentLesson}
          onScriptChange={handleScriptChange}
          onAudioGenerated={handleAudioGenerated}
        />
      )}

      {panel === 'player' && audioUrl && (
        <AudioPlayer
          audioUrl={audioUrl}
          lessonTitle={currentLesson.title}
          onStartOver={handleStartOver}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/App.jsx
git commit -m "feat: wire App.jsx — connect all panels, localStorage, and audio lifecycle"
```

---

## Task 15: End-to-End Manual Test

- [ ] **Step 1: Start the backend**

```bash
cd backend
.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` returns `{"status":"ok"}`

- [ ] **Step 2: Start the frontend**

In a second terminal:
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

- [ ] **Step 3: Test the full flow**

1. Enter a lesson title (e.g. "Directions 1"), topic (e.g. "asking for directions"), and a few words (e.g. `左\n右\n直走`).
2. Click **Generate Script** — spinner appears, then the Script Editor panel opens with a Claude-generated script.
3. Verify the script uses `[EN]`, `[ZH]`, `[ZH SLOW]`, and `[PAUSE Ns]` markers.
4. Edit one line in the script, then click **Generate Audio** — spinner appears while TTS and pydub run.
5. Verify the Audio Player panel appears with a working `<audio>` element.
6. Press play — confirm the lesson audio plays with English instructions, Mandarin words, and audible pauses.
7. Click **Download MP3** — verify a file downloads with the lesson title as the filename.
8. Click **Start Over** — verify the Input Panel is shown again.
9. Verify the lesson now appears in the **Saved Lessons** list.
10. Click **Load** on the saved lesson — verify the Script Editor opens with the saved script.

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "chore: end-to-end verified — Chinese audio lesson generator complete"
```
