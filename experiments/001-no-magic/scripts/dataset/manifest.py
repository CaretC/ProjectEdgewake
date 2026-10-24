
"""Dataset source manifest loading and validation."""

import json
from pathlib import Path

from .source import DatasetSource


def load_manifest(path: Path) -> list[DatasetSource]:
    """Load and validate a dataset source manifest."""

    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    entries = manifest.get("sources")

    if not isinstance(entries, list):
        raise ValueError("Manifest must contain a 'sources' list")

    sources = []
    seen_ids = set()
    seen_filenames = set()

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

        # Source IDs must be unique, regardless of case.
        source_id = source.id.casefold()

        if source_id in seen_ids:
            raise ValueError(
                f"Duplicate source ID: {source.id}"
            )

        # Prevent destination collisions across filesystems.
        filename = source.filename.casefold()

        if filename in seen_filenames:
            raise ValueError(
                f"Duplicate filename: {source.filename}"
            )

        seen_ids.add(source_id)
        seen_filenames.add(filename)

        sources.append(source)

    return sources
