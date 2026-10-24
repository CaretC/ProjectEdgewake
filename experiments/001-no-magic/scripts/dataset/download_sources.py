#!/usr/bin/env python3

"""Download and verify No Magic experiment sources."""

import json
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = EXPERIMENT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / "sources.json"
SOURCE_DIR = DATA_DIR / "source"


def load_manifest(path: Path) -> list[dict]:
    """Load and validate the source manifest."""

    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    sources = manifest.get("sources")

    if not isinstance(sources, list):
        raise ValueError("Manifest must contain a 'sources' list")

    required = {
        "id",
        "format",
        "purpose",
        "filename",
        "url",
        "sha256",
    }

    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"Source {index} must be an object")

        missing = required - source.keys()

        if missing:
            raise ValueError(
                f"Source {index} missing fields: {sorted(missing)}"
            )

    return sources