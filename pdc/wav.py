"""WAV header utilities for E-8305 fix."""

import struct

WAV_FORMAT_PCM = 0x0001
WAV_FORMAT_EXTENSIBLE = 0xFFFE


def read_header(file_path: str) -> tuple[int, int, int, int] | None:
    """Read WAV header. Returns (format_tag, channels, sample_rate, bits_per_sample) or None."""
    try:
        with open(file_path, "rb") as f:
            riff, _, fformat = struct.unpack("<4sI4s", f.read(12))
            if riff != b"RIFF" or fformat != b"WAVE":
                return None
            subchunk_id, _ = struct.unpack("<4sI", f.read(8))
            if subchunk_id != b"fmt ":
                return None
            fmt_data = f.read(16)
            if len(fmt_data) < 16:
                return None
            format_tag, channels, sample_rate, _, _, bits_per_sample = struct.unpack(
                "<HHIIHH", fmt_data
            )
            return (format_tag, channels, sample_rate, bits_per_sample)
    except (OSError, struct.error):
        return None


def needs_header_fix_only(file_path: str) -> bool:
    """True if WAV is PCM S16LE 44100 stereo but has wrong format tag (0xFFFE)."""
    if not file_path.lower().endswith(".wav"):
        return False
    header = read_header(file_path)
    if header is None:
        return False
    format_tag, channels, sample_rate, bits_per_sample = header
    return (
        format_tag == WAV_FORMAT_EXTENSIBLE
        and channels == 2
        and sample_rate == 44100
        and bits_per_sample == 16
    )


def fix_header_in_place(file_path: str) -> bool:
    """Rewrite bytes 20-21 to PCM (0x0001). Returns True on success."""
    try:
        with open(file_path, "r+b") as f:
            f.seek(20)
            f.write(struct.pack("<H", WAV_FORMAT_PCM))
        return True
    except OSError:
        return False
