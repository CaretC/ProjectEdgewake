
"""SHA-256 hashing and integrity verification for dataset files."""

import hashlib

from pathlib import Path


CHUNK_SIZE = 1024 * 1024  # 1 MiB


def hash_file(path: Path) -> str:
    """Calculate the SHA-256 digest of a file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


def verify_file(path: Path, expected: str) -> None:
    """Raise ValueError if a file does not match its expected SHA-256."""

    actual = hash_file(path)

    if actual.lower() != expected.lower():
        raise ValueError(
            f"SHA-256 mismatch: {path}\n"
            f"Expected: {expected}\n"
            f"Actual:   {actual}"
        )
