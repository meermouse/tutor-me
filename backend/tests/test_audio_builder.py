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
