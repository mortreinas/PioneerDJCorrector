"""Unified processing logic for Pioneer DJ Corrector."""

import os
import shutil
from typing import Callable

from pdc.cache import make_key as cache_key
from pdc.cache import read as read_cache
from pdc.cache import write as write_cache
from pdc.conversion import convert_to_pcm_s16le, is_pcm_s16le_44100
from pdc.io import calculate_file_hash
from pdc.wav import fix_header_in_place, needs_header_fix_only

AUDIO_EXTENSIONS = (".wav", ".aif", ".flac")
CONTENTS_DIR = "Contents"

FileStatus = str  # ok | cached | needs_fix | needs_convert | fixed | converted | will_not_fix | failed


def process(
    usb_drive: str,
    on_status: Callable[[str], None] | None = None,
    on_progress: Callable[[str, int, int, str], None] | None = None,
    on_file: Callable[[str, FileStatus], None] | None = None,
) -> None:
    """
    Process USB drive: fix or convert audio files in Contents/.

    on_status(msg): optional callback for status text
    on_progress(phase, current, total, desc): optional callback for progress
        phase: "analyzing" | "converting"
    on_file(relative_path, status, error_msg): optional callback per file.
        status: ok, cached, needs_fix, needs_convert, fixed, converted, failed
        error_msg: non-empty only when status is "failed"
    """
    contents_path = os.path.join(usb_drive, CONTENTS_DIR)
    if not os.path.isdir(contents_path):
        _notify(on_status, "Contents folder not found.")
        return

    cache = read_cache(usb_drive)
    to_process: list[tuple[str, str, str]] = []

    total_audio = sum(
        1
        for root, _, files in os.walk(contents_path)
        for name in files
        if name.lower().endswith(AUDIO_EXTENSIONS)
    )

    _notify(on_status, "Analyzing files...")
    analyzed = 0

    for root, _, files in os.walk(contents_path):
        for name in files:
            if not name.lower().endswith(AUDIO_EXTENSIONS):
                continue

            path = os.path.join(root, name)
            rel = cache_key(contents_path, path)
            try:
                stat = os.stat(path)
                size = stat.st_size
                mtime = stat.st_mtime
            except OSError:
                analyzed += 1
                if total_audio > 0:
                    _notify(on_progress, "analyzing", analyzed, total_audio, name)
                continue

            # Fast path: cache hit with mtime+size match → skip hash (real speedup)
            if rel in cache:
                rec = cache[rel]
                if rec.get("size") == size and rec.get("mtime") == mtime:
                    _notify(on_file, rel, "cached", "")
                    analyzed += 1
                    if total_audio > 0:
                        _notify(on_progress, "analyzing", analyzed, total_audio, name)
                    continue

            file_hash = calculate_file_hash(path)
            if file_hash is None:
                analyzed += 1
                if total_audio > 0:
                    _notify(on_progress, "analyzing", analyzed, total_audio, name)
                continue

            if rel in cache:
                rec = cache[rel]
                if rec.get("hash") == file_hash and rec.get("size") == size:
                    rec["mtime"] = mtime  # upgrade old cache entries for fast path next run
                    _notify(on_file, rel, "cached", "")
                    analyzed += 1
                    if total_audio > 0:
                        _notify(on_progress, "analyzing", analyzed, total_audio, name)
                    continue

            if is_pcm_s16le_44100(path):
                cache[rel] = {"hash": file_hash, "size": size, "mtime": mtime}
                _notify(on_file, rel, "ok", "")
                analyzed += 1
                if total_audio > 0:
                    _notify(on_progress, "analyzing", analyzed, total_audio, name)
                continue

            _notify(on_file, rel, "needs_fix" if needs_header_fix_only(path) else "needs_convert", "")
            to_process.append((path, rel, name))
            analyzed += 1
            if total_audio > 0:
                _notify(on_progress, "analyzing", analyzed, total_audio, name)

    total = len(to_process)
    if total == 0:
        write_cache(usb_drive, cache)
        _notify(on_status, "All files already compatible.")
        _notify(on_progress, "done", total_audio or 1, total_audio or 1, "")
        return

    ffmpeg_ok = shutil.which("ffmpeg") is not None

    _notify(on_status, f"Processing {total} file(s)...")
    fixed = 0
    converted = 0
    failed: list[str] = []

    for i, (path, key, name) in enumerate(to_process):
        _notify(on_progress, "converting", i, total, name)

        if needs_header_fix_only(path):
            if fix_header_in_place(path):
                h = calculate_file_hash(path)
                if h is not None:
                    try:
                        st = os.stat(path)
                        cache[key] = {"hash": h, "size": st.st_size, "mtime": st.st_mtime}
                    except OSError:
                        cache[key] = {"hash": h, "size": os.path.getsize(path)}
                fixed += 1
                _notify(on_file, key, "fixed", "")
            else:
                failed.append(name)
                _notify(on_file, key, "failed", "Header fix failed")
        else:
            if not ffmpeg_ok:
                failed.append(name)
                _notify(on_file, key, "will_not_fix")
            else:
                ok, err = convert_to_pcm_s16le(path, key, cache)
                if ok:
                    converted += 1
                    _notify(on_file, key, "converted", "")
                else:
                    failed.append(name)
                    _notify(on_file, key, "failed", err or "Unknown error")

        _notify(on_progress, "converting", i + 1, total, name)

    write_cache(usb_drive, cache)

    if failed:
        msg = f"Done. Header fixes: {fixed}, conversions: {converted}. Failed: {', '.join(failed)}"
        if not ffmpeg_ok and any(not needs_header_fix_only(p) for p, _, _ in to_process):
            msg += " (FFmpeg not found for conversion)"
        _notify(on_status, msg)
    else:
        _notify(on_status, f"Done. Header fixes: {fixed}, conversions: {converted}.")


def _notify(cb: Callable | None, *args) -> None:
    if cb is not None:
        cb(*args)
