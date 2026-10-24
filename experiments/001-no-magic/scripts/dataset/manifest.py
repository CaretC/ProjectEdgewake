"""Dataset source manifest loading."""

import json
from pathlib import Path

from .source import DatasetSource


def load_manifest(path: Path) -> list[DatasetSource]:
    """Load a JSON manifest into validated source objects."""

    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    entries = manifest.get("sources")

    if not isinstance(entries, list):
        raise ValueError("Manifest must contain a 'sources' list")

    sources = []

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                f"Source {index} must be a JSON object"
            )

        try:
            source = DatasetSource.from_dict(entry)
        except ValueError as error:
            raise ValueError(
                f"Invalid source at index {index}: {error}"
            ) from error

        sources.append(source)

    return sources