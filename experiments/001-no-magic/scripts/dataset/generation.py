
"""Load and validate dataset generation recipes."""

import json

from dataclasses import dataclass
from pathlib import Path

from .source import DatasetSource, _validate_filename


@dataclass(frozen=True, slots=True)
class GenerationRecipe:
    """A validated instruction for generating a sample file."""

    id: str
    type: str
    filename: str
    source_ids: tuple[str, ...]
    compresslevel: int = 6


def load_generation(
    path: Path,
    sources: list[DatasetSource],
) -> list[GenerationRecipe]:
    """Load generation recipes and resolve their source IDs."""

    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict) or set(manifest) != {"outputs"}:
        raise ValueError("Generation manifest must contain 'outputs'")

    outputs = manifest["outputs"]

    if not isinstance(outputs, list):
        raise ValueError("'outputs' must be a list")

    known_sources = {source.id for source in sources}
    seen_ids = set()
    seen_filenames = set()
    recipes = []

    for index, entry in enumerate(outputs):
        if not isinstance(entry, dict):
            raise ValueError(f"Output {index} must be an object")

        kind = entry.get("type")

        if kind == "bmp":
            required = {"id", "type", "source", "filename", "mode"}

            if set(entry) != required:
                raise ValueError(f"Invalid BMP recipe fields at {index}")

            if entry["mode"] != "RGB":
                raise ValueError("Only RGB BMP generation is supported")

            source_ids = (entry["source"],)
            compresslevel = 6

        elif kind == "zip":
            required = {
                "id", "type", "sources", "filename",
                "compression", "compresslevel",
            }

            if set(entry) != required:
                raise ValueError(f"Invalid ZIP recipe fields at {index}")

            if entry["compression"] != "deflate":
                raise ValueError("Only DEFLATE compression is supported")

            compresslevel = entry["compresslevel"]

            if (
                type(compresslevel) is not int
                or not 0 <= compresslevel <= 9
            ):
                raise ValueError("ZIP compresslevel must be 0-9")

            source_ids = entry["sources"]

            if (
                not isinstance(source_ids, list)
                or not source_ids
            ):
                raise ValueError("ZIP sources must be a non-empty list")

            source_ids = tuple(source_ids)

        else:
            raise ValueError(f"Unknown generation type: {kind}")

        recipe_id = entry["id"]
        filename = entry["filename"]

        if not isinstance(recipe_id, str) or not recipe_id.strip():
            raise ValueError("Invalid generation recipe ID")

        _validate_filename(filename)

        if any(
            not isinstance(source_id, str)
            or source_id not in known_sources
            for source_id in source_ids
        ):
            raise ValueError(
                f"Recipe {recipe_id} references an unknown source"
            )

        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"Duplicate input in recipe {recipe_id}")

        if recipe_id.casefold() in seen_ids:
            raise ValueError(f"Duplicate generation ID: {recipe_id}")

        if filename.casefold() in seen_filenames:
            raise ValueError(f"Duplicate generated filename: {filename}")

        seen_ids.add(recipe_id.casefold())
        seen_filenames.add(filename.casefold())

        recipes.append(
            GenerationRecipe(
                id=recipe_id,
                type=kind,
                filename=filename,
                source_ids=source_ids,
                compresslevel=compresslevel,
            )
        )

    return recipes
