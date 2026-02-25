"""File I/O utilities."""

import hashlib


def calculate_file_hash(file_path: str) -> str | None:
    """Compute SHA256 hash of file. Returns None on I/O error."""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(block)
        return sha256_hash.hexdigest()
    except OSError:
        return None
