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


def test_generate_audio_rejects_empty_script(client):
    response = client.post("/generate-audio", json={"script": "no markers here"})
    assert response.status_code == 422


def test_generate_script_requires_word_list(client):
    response = client.post(
        "/generate-script",
        json={"title": "Test", "topic": "greetings"},
    )
    assert response.status_code == 422
