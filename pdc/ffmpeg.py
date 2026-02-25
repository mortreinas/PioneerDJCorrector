"""FFmpeg availability check."""

import platform
import shutil
import subprocess


def is_available() -> bool:
    """Return True if ffmpeg is in PATH."""
    return shutil.which("ffmpeg") is not None


def ensure_available() -> None:
    """Check ffmpeg; attempt install if missing."""
    if is_available():
        return
    _try_install()


def _try_install() -> None:
    system = platform.system()
    if system == "Windows":
        subprocess.run(["winget", "install", "-e", "--id", "Gyan.FFmpeg"], check=False)
    elif system == "Linux":
        subprocess.run(["sudo", "apt-get", "install", "-y", "ffmpeg"], check=False)
    elif system == "Darwin":
        subprocess.run(["brew", "install", "ffmpeg"], check=False)
    else:
        print("Unsupported OS. Install FFmpeg manually.")
