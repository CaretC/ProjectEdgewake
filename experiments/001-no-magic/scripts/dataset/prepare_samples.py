
#!/usr/bin/env python3

"""Generate experimental file samples from verified source material."""

import os
import sys
import tempfile
import zipfile
import zlib

from pathlib import Path

import PIL
from PIL import Image

from .generation import GenerationRecipe, load_generation
from .hashing import hash_file, verify_file
from .manifest import load_manifest
from .source import DatasetSource


# ---------------------------------------------------------
# Experiment paths
# ---------------------------------------------------------

EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = EXPERIMENT_ROOT / "data"

SOURCE_MANIFEST = DATA_DIR / "sources.json"
GENERATION_MANIFEST = DATA_DIR / "generation.json"

SOURCE_DIR = DATA_DIR / "source"
GENERATED_DIR = DATA_DIR / "generated"


# ---------------------------------------------------------
# Generation settings
# ---------------------------------------------------------

# Fixed ZIP metadata for best-effort reproducibility.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_PERMISSIONS = 0o100644 << 16


# ---------------------------------------------------------
# File transformations
# ---------------------------------------------------------

def generate_bmp(source: Path, destination: Path) -> None:
    """Convert an image to an uncompressed 24-bit RGB BMP."""

    with Image.open(source) as image:
        rgb = image.convert("RGB")

        # Exclusive creation prevents overwriting existing files.
        with destination.open("xb") as output:
            rgb.save(output, format="BMP")


def generate_zip(
    sources: list[Path],
    destination: Path,
    compresslevel: int = 6,
) -> None:
    """Create a DEFLATE archive with fixed metadata."""

    with zipfile.ZipFile(destination, mode="x") as archive:
        for source in sources:
            info = zipfile.ZipInfo(
                filename=source.name,
                date_time=ZIP_TIMESTAMP,
            )

            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = ZIP_PERMISSIONS

            archive.writestr(
                info,
                source.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=compresslevel,
            )


# ---------------------------------------------------------
# Source verification
# ---------------------------------------------------------

def verify_sources(
    sources: list[DatasetSource],
    recipes: list[GenerationRecipe],
    source_dir: Path,
) -> dict[str, Path]:
    """Verify all recipe inputs before generating any output."""

    source_map = {source.id: source for source in sources}

    required_ids = {
        source_id
        for recipe in recipes
        for source_id in recipe.source_ids
    }

    verified = {}

    for source_id in sorted(required_ids):
        if source_id not in source_map:
            raise ValueError(f"Unknown source ID: {source_id}")

        source = source_map[source_id]
        path = source_dir / source.filename

        if path.is_symlink() or not path.is_file():
            raise FileNotFoundError(
                f"Missing or unsafe source file: {path}"
            )

        if source.sha256 is None:
            raise ValueError(
                f"Source {source_id} has no pinned SHA-256"
            )

        verify_file(path, source.sha256)

        verified[source_id] = path

        print(f"VERIFIED SOURCE [{source_id}] {source.filename}")

    return verified


# ---------------------------------------------------------
# Dataset preparation
# ---------------------------------------------------------

def prepare_dataset(
    sources: list[DatasetSource],
    recipes: list[GenerationRecipe],
    source_dir: Path,
    output_dir: Path,
) -> None:
    """Generate samples from verified inputs without overwriting data."""

    # Verify all required source files before making changes.
    verified = verify_sources(
        sources,
        recipes,
        source_dir,
    )

    if output_dir.is_symlink():
        raise ValueError(
            f"Refusing symlink output directory: {output_dir}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each validated generation recipe.
    for recipe in recipes:
        destination = output_dir / recipe.filename

        if destination.is_symlink():
            raise ValueError(
                f"Refusing symlink output: {destination}"
            )

        if destination.exists() and not destination.is_file():
            raise ValueError(
                f"Output is not a regular file: {destination}"
            )

        inputs = [
            verified[source_id]
            for source_id in recipe.source_ids
        ]

        print(f"PREPARING [{recipe.id}] {recipe.filename}")

        # Generate into a temporary directory so incomplete
        # files cannot appear as completed dataset outputs.
        with tempfile.TemporaryDirectory(
            prefix=".no-magic-",
            dir=output_dir,
        ) as temporary_dir:

            temporary = Path(temporary_dir) / recipe.filename

            if recipe.type == "bmp":
                generate_bmp(
                    inputs[0],
                    temporary,
                )

            elif recipe.type == "zip":
                generate_zip(
                    inputs,
                    temporary,
                    compresslevel=recipe.compresslevel,
                )

            else:
                raise ValueError(
                    f"Unsupported generation type: {recipe.type}"
                )

            # Calculate the hash of the newly generated output.
            actual = hash_file(temporary)

            if destination.exists():
                existing = hash_file(destination)

                if existing != actual:
                    raise ValueError(
                        f"Generated output differs: {recipe.filename}\n"
                        f"Existing SHA-256:  {existing}\n"
                        f"Generated SHA-256: {actual}\n"
                        "Existing output was preserved."
                    )

                print(
                    f"VERIFIED [{recipe.id}] {recipe.filename}"
                )

            else:
                # Publish the completed file.
                # This is intended for single-user local execution.
                os.replace(temporary, destination)

                print(
                    f"GENERATED [{recipe.id}] {recipe.filename}"
                )

            print(f"  SHA-256: {actual}")


# ---------------------------------------------------------
# Application entry point
# ---------------------------------------------------------

def main() -> None:
    """Load generation recipes and prepare the experiment dataset."""

    sources = load_manifest(SOURCE_MANIFEST)

    recipes = load_generation(
        GENERATION_MANIFEST,
        sources,
    )

    print(f"Loaded {len(sources)} dataset sources")
    print(f"Loaded {len(recipes)} generation recipes")
    print()

    print("Generation environment:")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Pillow: {PIL.__version__}")
    print(
        f"  zlib: {zlib.ZLIB_VERSION} "
        f"(runtime {zlib.ZLIB_RUNTIME_VERSION})"
    )
    print()

    prepare_dataset(
        sources,
        recipes,
        SOURCE_DIR,
        GENERATED_DIR,
    )


if __name__ == "__main__":
    try:
        main()

    except (OSError, ValueError) as error:
        raise SystemExit(f"ERROR: {error}") from error
