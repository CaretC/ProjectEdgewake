
#!/usr/bin/env python3

"""Acquire and verify No Magic experiment source files."""

import argparse
import os
import tempfile

from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)

from .hashing import hash_file, verify_file
from .manifest import load_manifest
from .source import DatasetSource


EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = EXPERIMENT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "sources.json"
SOURCE_DIR = DATA_DIR / "source"

CHUNK_SIZE = 1024 * 1024


class HTTPSRedirectHandler(HTTPRedirectHandler):
    """Prevent HTTPS downloads from redirecting to HTTP."""

    def redirect_request(
        self, req, fp, code, msg, headers, newurl
    ):
        parsed = urlsplit(newurl)

        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
        ):
            raise HTTPError(
                newurl,
                code,
                "Refusing unsafe download redirect",
                headers,
                fp,
            )

        return super().redirect_request(
            req, fp, code, msg, headers, newurl
        )


def _open_source(url: str):
    """Open an HTTPS source as a readable binary stream."""

    request = Request(
        url,
        headers={"User-Agent": "Edgewake-NoMagic/0.1"},
    )

    opener = build_opener(HTTPSRedirectHandler())

    return opener.open(request, timeout=30)


def _preflight(
    sources: list[DatasetSource],
    directory: Path,
    replace: bool,
) -> None:
    """Validate existing files before any downloads begin."""

    for source in sources:
        destination = directory / source.filename

        if destination.is_symlink():
            raise ValueError(
                f"Refusing symlink destination: {destination}"
            )

        if not destination.exists():
            continue

        if not destination.is_file():
            raise ValueError(
                f"Destination is not a regular file: {destination}"
            )

        if replace and source.sha256 is not None:
            raise ValueError(
                f"Cannot replace pinned source: {source.id}\n"
                "Set sha256 to null in sources.json and "
                "review the change before replacing."
            )

        if source.sha256 is not None:
            verify_file(destination, source.sha256)


def _download_source(
    source: DatasetSource,
    destination: Path,
) -> str:
    """Download into a temporary file, verify, then install."""

    temporary = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{source.filename}.",
            suffix=".part",
            dir=destination.parent,
            delete=False,
        ) as output:
            temporary = Path(output.name)

            with _open_source(source.url) as response:
                while chunk := response.read(CHUNK_SIZE):
                    output.write(chunk)

        # Verify the completed temporary file before installation.
        actual = hash_file(temporary)

        if source.sha256 is not None:
            verify_file(temporary, source.sha256)

        # Atomic replacement on supported local filesystems.
        os.replace(temporary, destination)

        return actual

    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def acquire_sources(
    sources: list[DatasetSource],
    directory: Path,
    replace: bool = False,
) -> None:
    """Acquire sources without silently modifying existing data."""

    directory.mkdir(parents=True, exist_ok=True)

    # Check all existing data before starting network operations.
    _preflight(sources, directory, replace)

    for source in sources:
        destination = directory / source.filename

        if destination.exists() and not replace:
            if source.sha256 is None:
                actual = hash_file(destination)

                print(
                    f"UNPINNED [{source.id}] {source.filename}\n"
                    f"  SHA-256: {actual}"
                )
            else:
                print(
                    f"VERIFIED [{source.id}] {source.filename}"
                )

            continue

        action = "REPLACING" if destination.exists() else "DOWNLOADING"

        print(f"{action} [{source.id}] {source.filename}")

        actual = _download_source(source, destination)

        print(
            f"ACQUIRED [{source.id}] {source.filename}\n"
            f"  SHA-256: {actual}"
        )

        if source.sha256 is None:
            print("  Checksum not pinned in sources.json")


def main(replace: bool = False) -> None:
    """Load the manifest and acquire its source files."""

    sources = load_manifest(MANIFEST_PATH)

    print(f"Loaded {len(sources)} dataset sources.")

    for source in sources:
        print(f"  [{source.id}] {source.filename}")

    acquire_sources(sources, SOURCE_DIR, replace=replace)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Acquire No Magic experiment sources"
    )

    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing unpinned source files",
    )

    args = parser.parse_args()

    try:
        main(replace=args.replace)
    except (OSError, ValueError) as error:
        parser.exit(1, f"ERROR: {error}\n")
