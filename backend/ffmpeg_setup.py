"""Configure pydub to use the imageio-ffmpeg bundled binary when ffmpeg is not on PATH."""
import os
import re
import shutil
import subprocess
import tempfile

import pydub
import pydub.utils

try:
    import imageio_ffmpeg
    _ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
except (ImportError, RuntimeError):
    _ffmpeg_exe = None

_ffmpeg = _ffmpeg_exe or shutil.which("ffmpeg")
_ffprobe = shutil.which("ffprobe") or _ffmpeg

if _ffmpeg:
    pydub.AudioSegment.converter = _ffmpeg
if _ffprobe:
    pydub.AudioSegment.ffprobe = _ffprobe


def _mediainfo_json_via_ffmpeg(filepath, read_ahead_limit=-1):
    ffmpeg = _ffmpeg or "ffmpeg"

    if hasattr(filepath, "read"):
        filepath.seek(0)
        data = filepath.read()
        filepath.seek(0)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        cleanup = True
    else:
        tmp_path = str(filepath)
        cleanup = False

    try:
        result = subprocess.run(
            [ffmpeg, "-i", tmp_path],
            capture_output=True,
            text=True,
        )
        stderr = result.stderr
    finally:
        if cleanup:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    streams = []
    for line in stderr.splitlines():
        m = re.search(
            r"Stream #(\d+:\d+)[^:]*: Audio: (\w+)[^,]*, (\d+) Hz, (\w+), (\w+)",
            line,
        )
        if m:
            codec_name = m.group(2)
            sample_rate = int(m.group(3))
            channel_layout = m.group(4)
            sample_fmt = m.group(5)
            channels = 1 if channel_layout in ("mono",) else 2

            if sample_fmt == "fltp" and codec_name in ("mp3", "mp4", "aac", "webm", "ogg"):
                bits_per_sample = 16
            else:
                bits_map = {
                    "u8": 8, "s16": 16, "s16le": 16, "s32": 32, "s32le": 32,
                    "flt": 32, "dbl": 64,
                }
                bits_per_sample = bits_map.get(sample_fmt, 16)

            streams.append({
                "index": 0,
                "codec_type": "audio",
                "codec_name": codec_name,
                "sample_rate": str(sample_rate),
                "channels": channels,
                "channel_layout": channel_layout,
                "sample_fmt": sample_fmt,
                "bits_per_sample": bits_per_sample,
            })

    if not streams:
        return {}

    return {"streams": streams, "format": {}}


if _ffmpeg:
    pydub.utils.mediainfo_json = _mediainfo_json_via_ffmpeg
    import pydub.audio_segment as _pydub_as
    _pydub_as.mediainfo_json = _mediainfo_json_via_ffmpeg
