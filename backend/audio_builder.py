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
