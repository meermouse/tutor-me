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
