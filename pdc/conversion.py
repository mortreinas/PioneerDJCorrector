"""Audio conversion for Pioneer DJ compatibility."""

import os
import shutil
import subprocess
import tempfile

from pdc.io import calculate_file_hash
from pdc.wav import WAV_FORMAT_PCM, read_header


def is_pcm_s16le_44100(file_path: str) -> bool:
    """Check if file is PCM S16LE 44100 Hz. Uses header for WAV (fast), ffprobe for others."""
    if file_path.lower().endswith(".wav"):
        header = read_header(file_path)
        if header is not None:
            format_tag, channels, sample_rate, bits_per_sample = header
            return (
                format_tag == WAV_FORMAT_PCM
                and channels == 2
                and sample_rate == 44100
                and bits_per_sample == 16
            )
    return _check_with_ffprobe(file_path)


def _check_with_ffprobe(file_path: str) -> bool:
    """Fallback for non-WAV or ambiguous WAV."""
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_name,sample_rate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file_path,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        lines = out.split("\n")
        if len(lines) >= 2:
            return lines[0] == "pcm_s16le" and lines[1] == "44100"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return False


def convert_to_pcm_s16le(
    input_path: str, cache_key: str, cache_data: dict
) -> tuple[bool, str]:
    """Convert file in-place. Returns (success, error_message)."""
    if shutil.which("ffmpeg") is None:
        return False, "FFmpeg not found. Install FFmpeg and add to PATH."

    # Convert to system temp first (e.g. C:\Users\...\AppData\Local\Temp\)
    # avoids USB permission/lock issues on Windows when writing directly to external drive
    # Use .wav extension so FFmpeg recognizes the output format (else "Invalid argument")
    fd_out, output_tmp = tempfile.mkstemp(suffix=".wav", prefix="pdc_")
    os.close(fd_out)
    ext = os.path.splitext(input_path)[1].lower() or ".wav"
    fd_in, input_tmp = tempfile.mkstemp(suffix=ext, prefix="pdc_in_")
    os.close(fd_in)
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    try:
        shutil.copy2(input_path, input_tmp)
    except OSError as e:
        _safe_remove(input_tmp)
        return False, str(e)

    # FFmpeg on Windows: use temp paths (ASCII-only) to avoid Unicode/special-char issues
    input_ff = input_tmp.replace("\\", "/")
    output_ff = output_tmp.replace("\\", "/")

    try:
        proc = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i",
                input_ff,
                "-c:a",
                "pcm_s16le",
                "-ar",
                "44100",
                "-ac",
                "2",
                "-f",
                "wav",
                "-map_metadata",
                "0",
                output_ff,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            encoding="utf-8",
            errors="replace",
        )
        out, _ = proc.communicate()

        if proc.returncode != 0 or not os.path.exists(output_tmp):
            err = (out or "").strip().split("\n")[-1] if out else "Unknown error"
            return False, err

        try:
            shutil.copy2(output_tmp, input_path)
        except OSError as e:
            return False, str(e)
    finally:
        _safe_remove(output_tmp)
        _safe_remove(input_tmp)

    file_hash = calculate_file_hash(input_path)
    if file_hash is not None:
        try:
            st = os.stat(input_path)
            cache_data[cache_key] = {"hash": file_hash, "size": st.st_size, "mtime": st.st_mtime}
        except OSError:
            cache_data[cache_key] = {"hash": file_hash, "size": os.path.getsize(input_path)}
    return True, ""


def _safe_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
