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
