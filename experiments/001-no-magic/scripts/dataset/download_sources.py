#!/usr/bin/env python3

"""Download and verify No Magic experiment sources."""

from pathlib import Path

from .manifest import load_manifest


EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = EXPERIMENT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "sources.json"
SOURCE_DIR = DATA_DIR / "source"


def main() -> None:
    """Entry point for the source downloader."""

    sources = load_manifest(MANIFEST_PATH)

    print(f"Loaded {len(sources)} dataset sources.")

    for source in sources:
        print(f"  [{source.id}] {source.filename}")


if __name__ == "__main__":
    main()