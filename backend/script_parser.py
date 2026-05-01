from __future__ import annotations
import re
from dataclasses import dataclass
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
