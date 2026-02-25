"""Pioneer DJ cache (pioneerdj.dick) for tracking processed files."""

import json
import os


def _normalize_key(path: str) -> str:
    return path.replace("\\", "/")


def read(usb_drive: str) -> dict:
    """Load cache from USB drive. Returns empty dict if missing."""
    path = os.path.join(usb_drive, "pioneerdj.dick")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write(usb_drive: str, data: dict) -> None:
    """Write cache atomically: write to .tmp then rename."""
    base = os.path.join(usb_drive, "pioneerdj.dick")
    tmp = base + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, base)
    except OSError:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def make_key(contents_dir: str, file_path: str) -> str:
    """Create cache key from full path."""
    return _normalize_key(os.path.relpath(file_path, contents_dir))
