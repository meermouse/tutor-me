"""Configure pydub to use the imageio-ffmpeg bundled binary when ffmpeg is not on PATH."""
import io
import os
import re
import subprocess
import sys
import tempfile

import pydub
import pydub.utils

try:
    import imageio_ffmpeg
    _ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    _ffmpeg_exe = None

# Point pydub's converter (used for encode/decode) at our bundled ffmpeg.
if _ffmpeg_exe:
    pydub.AudioSegment.converter = _ffmpeg_exe


def _mediainfo_json_via_ffmpeg(filepath, read_ahead_limit=-1):
    """
    Replacement for pydub.utils.mediainfo_json that uses 'ffmpeg -i' instead of
    ffprobe.  ffprobe is a separate binary not included in the imageio-ffmpeg
    bundle; ffmpeg -i writes stream info to stderr which we parse here.

    Returns a dict shaped like the JSON that ffprobe -of json -show_streams
    -show_format would produce — just enough for pydub's from_file() to work.
    """
    ffmpeg = _ffmpeg_exe or "ffmpeg"

    # filepath may be a BytesIO / file-like object – write to a temp file so
    # ffmpeg can read it.
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

    # Parse the stream line, e.g.:
    #   Stream #0:0: Audio: mp3 (mp3float), 44100 Hz, stereo, fltp, 128 kb/s
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

            # Mirror pydub's logic: mp3/fltp → treat as s16
            if sample_fmt == "fltp" and codec_name in ("mp3", "mp4", "aac", "webm", "ogg"):
                bits_per_sample = 16
            else:
                # map common sample formats
                bits_map = {
                    "u8": 8, "s16": 16, "s16le": 16, "s32": 32, "s32le": 32,
                    "flt": 32, "dbl": 64,
                }
                bits_per_sample = bits_map.get(sample_fmt, 16)

            streams.append(
                {
                    "index": 0,
                    "codec_type": "audio",
                    "codec_name": codec_name,
                    "sample_rate": str(sample_rate),
                    "channels": channels,
                    "channel_layout": channel_layout,
                    "sample_fmt": sample_fmt,
                    "bits_per_sample": bits_per_sample,
                }
            )

    # Pydub checks `if info:` — return empty dict on failure so it falls back
    # to a default acodec rather than crashing.
    if not streams:
        return {}

    return {"streams": streams, "format": {}}


# Monkey-patch pydub so both the module-level function and any already-imported
# references inside audio_segment.py see the replacement.
if _ffmpeg_exe:
    pydub.utils.mediainfo_json = _mediainfo_json_via_ffmpeg
    # audio_segment imports mediainfo_json directly at the top of the file, so
    # we must also patch it there.
    import pydub.audio_segment as _pydub_as
    _pydub_as.mediainfo_json = _mediainfo_json_via_ffmpeg
