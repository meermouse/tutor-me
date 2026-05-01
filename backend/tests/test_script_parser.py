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
