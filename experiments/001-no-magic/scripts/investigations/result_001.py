
#!/usr/bin/env python3

"""Reproduce No Magic Result 001: file fragment statistics."""

import argparse
import subprocess
import sys

from pathlib import Path

from scripts.analysis.fragment_statistics import (
    Specimen,
    run_analysis,
)

from scripts.dataset.generation import load_generation
from scripts.dataset.hashing import hash_file
from scripts.dataset.manifest import load_manifest


# ---------------------------------------------------------
# Experiment paths
# ---------------------------------------------------------

EXPERIMENT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = EXPERIMENT_ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
GENERATED_DIR = DATA_DIR / "generated"
RESULTS_DIR = EXPERIMENT_ROOT / "results" / "001-fragment-statistics"

SOURCE_MANIFEST = DATA_DIR / "sources.json"
GENERATION_MANIFEST = DATA_DIR / "generation.json"


# ---------------------------------------------------------
# Investigation configuration
# ---------------------------------------------------------

# Result 001 compares one specimen from each file format.
#
# Source and generated filenames are resolved against
# their respective manifests.

SOURCE_SPECIMENS = (
    ("TXT", "alice.txt"),
    ("JPEG", "fronalpstock.jpg"),
)

GENERATED_SPECIMENS = (
    ("BMP", "blue-marble.bmp"),
    ("ZIP", "mixed-content.zip"),
)


# ---------------------------------------------------------
# Input preparation
# ---------------------------------------------------------

def prepare_inputs() -> None:
    """Acquire, verify and generate the required dataset files."""

    modules = (
        "scripts.dataset.download_sources",
        "scripts.dataset.prepare_samples",
    )

    for module in modules:
        print(f"Running {module}", flush=True)

        subprocess.run(
            [sys.executable, "-m", module],
            cwd=EXPERIMENT_ROOT,
            check=True,
        )


# ---------------------------------------------------------
# Specimen selection
# ---------------------------------------------------------

def require_regular_file(path: Path) -> None:
    """Reject missing inputs and symbolic links."""

    if path.is_symlink() or not path.is_file():
        raise FileNotFoundError(
            f"Missing or unsafe input file: {path}"
        )


def select_specimens() -> list[Specimen]:
    """Select the four specimens used in Result 001."""

    sources = load_manifest(SOURCE_MANIFEST)

    recipes = load_generation(
        GENERATION_MANIFEST,
        sources,
    )

    source_by_filename = {
        source.filename: source
        for source in sources
    }

    recipe_by_filename = {
        recipe.filename: recipe
        for recipe in recipes
    }

    specimens = []

    # -----------------------------------------------------
    # Original source files: TXT and JPEG
    # -----------------------------------------------------

    for format_name, filename in SOURCE_SPECIMENS:
        if filename not in source_by_filename:
            raise ValueError(
                f"Source not found in manifest: {filename}"
            )

        source = source_by_filename[filename]
        path = SOURCE_DIR / source.filename

        require_regular_file(path)

        if source.sha256 is None:
            raise ValueError(
                f"Source has no pinned SHA-256: {source.id}"
            )

        actual_hash = hash_file(path)

        if actual_hash.lower() != source.sha256.lower():
            raise ValueError(
                f"Source checksum mismatch: {filename}"
            )

        specimens.append(
            Specimen(
                format=format_name,
                source_id=source.id,
                path=path,
                sha256=actual_hash,
            )
        )

    # -----------------------------------------------------
    # Generated files: BMP and ZIP
    # -----------------------------------------------------

    for format_name, filename in GENERATED_SPECIMENS:
        if filename not in recipe_by_filename:
            raise ValueError(
                f"Recipe not found in manifest: {filename}"
            )

        recipe = recipe_by_filename[filename]
        path = GENERATED_DIR / recipe.filename

        require_regular_file(path)

        specimens.append(
            Specimen(
                format=format_name,
                source_id=recipe.id,
                path=path,
                sha256=hash_file(path),
            )
        )

    return specimens


# ---------------------------------------------------------
# Investigation entry point
# ---------------------------------------------------------

def main() -> None:
    """Run the complete Result 001 investigation."""

    parser = argparse.ArgumentParser(
        description=(
            "Reproduce No Magic Result 001: "
            "interior file fragment statistics."
        )
    )

    parser.add_argument(
        "--prepare",
        action="store_true",
        help=(
            "Download and verify sources, then generate "
            "and verify derived samples before analysis."
        ),
    )

    args = parser.parse_args()

    print("No Magic — Investigation 001")
    print("============================")
    print()

    if args.prepare:
        prepare_inputs()

    specimens = select_specimens()

    print("Selected specimens:")

    for specimen in specimens:
        print(
            f"  {specimen.format:5s} "
            f"[{specimen.source_id}] "
            f"{specimen.path.name}"
        )

    print()

    run_analysis(
        specimens=specimens,
        results_dir=RESULTS_DIR,
    )


if __name__ == "__main__":
    try:
        main()

    except (OSError, ValueError) as error:
        raise SystemExit(f"ERROR: {error}") from error
