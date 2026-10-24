
"""Collect and visualise file-fragment statistics for No Magic."""

import csv

from dataclasses import dataclass
from pathlib import Path

import matplotlib

# Headless rendering: works on Windows and in CI.
matplotlib.use("Agg")

import matplotlib.pyplot as plt

from scripts.dataset.fragments import (
    measure_fragment,
    sample_fragments,
)


FRAGMENT_SIZE = 4096
SAMPLE_COUNT = 16
SEED = 42

CSV_FILENAME = "001-fragment-statistics.csv"
FIGURE_FILENAME = "001-fragment-statistics.png"

CSV_FIELDS = (
    "format",
    "source_id",
    "filename",
    "file_sha256",
    "offset",
    "size",
    "seed",
    "entropy",
    "printable_fraction",
    "zero_fraction",
)


@dataclass(frozen=True, slots=True)
class Specimen:
    """A known file selected for an investigation."""

    format: str
    source_id: str
    path: Path
    sha256: str


def collect_statistics(
    specimens: list[Specimen],
    fragment_size: int = FRAGMENT_SIZE,
    sample_count: int = SAMPLE_COUNT,
    seed: int = SEED,
) -> list[dict]:
    """Collect one labelled observation per sampled fragment."""

    observations = []

    for specimen in specimens:
        fragments = sample_fragments(
            specimen.path,
            size=fragment_size,
            count=sample_count,
            seed=seed,
        )

        if not fragments:
            raise ValueError(
                f"No eligible fragments in {specimen.path}"
            )

        for fragment in fragments:
            metrics = measure_fragment(fragment.data)

            observations.append({
                "format": specimen.format,
                "source_id": specimen.source_id,
                "filename": specimen.path.name,
                "file_sha256": specimen.sha256,
                "offset": fragment.offset,
                "size": len(fragment.data),
                "seed": seed,
                "entropy": metrics.entropy,
                "printable_fraction": metrics.printable_fraction,
                "zero_fraction": metrics.zero_fraction,
            })

    return observations


def write_csv(
    observations: list[dict],
    destination: Path,
) -> None:
    """Write deterministic, labelled observations to CSV."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output:
        writer = csv.DictWriter(
            output,
            fieldnames=CSV_FIELDS,
            lineterminator="\n",
        )

        writer.writeheader()

        for observation in observations:
            row = observation.copy()

            for field in (
                "entropy",
                "printable_fraction",
                "zero_fraction",
            ):
                row[field] = f"{row[field]:.6f}"

            writer.writerow(row)


def write_figure(
    observations: list[dict],
    specimens: list[Specimen],
    destination: Path,
) -> None:
    """Create a 4 x 3 grid of fragment statistics."""

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics = (
        ("entropy", "Shannon entropy", "bits/byte"),
        ("printable_fraction", "Printable bytes", "fraction"),
        ("zero_fraction", "Zero bytes", "fraction"),
    )

    figure, axes = plt.subplots(
        nrows=len(specimens),
        ncols=3,
        figsize=(15, 12),
        squeeze=False,
        constrained_layout=True,
    )

    figure.suptitle(
        "No Magic — Interior File Fragment Statistics",
        fontsize=17,
        fontweight="bold",
    )

    # Use one shared zero-fraction scale across file types.
    # This makes comparisons possible without wasting
    # most of the axis on unused values.
    max_zero = max(
        observation["zero_fraction"]
        for observation in observations
    )

    zero_limit = min(
        1.0,
        max(0.02, max_zero * 1.1),
    )

    for row_index, specimen in enumerate(specimens):
        rows = [
            observation
            for observation in observations
            if observation["source_id"] == specimen.source_id
            and observation["format"] == specimen.format
        ]

        # Actual file offset; no connecting lines between samples.
        # Large files use MiB, smaller files use KiB.
        use_mib = specimen.path.stat().st_size >= 1024 * 1024
        divisor = 1024 * 1024 if use_mib else 1024
        unit = "MiB" if use_mib else "KiB"

        offsets = [
            observation["offset"] / divisor
            for observation in rows
        ]

        for column_index, (key, title, unit_label) in enumerate(metrics):
            axis = axes[row_index][column_index]

            values = [
                observation[key]
                for observation in rows
            ]

            axis.scatter(
                offsets,
                values,
                s=28,
                alpha=0.85,
            )

            axis.grid(
                True,
                alpha=0.2,
            )

            axis.set_xlim(left=0)
            axis.set_xlabel(f"File offset ({unit})")

            if key == "entropy":
                axis.set_ylim(0, 8)
            elif key == "printable_fraction":
                axis.set_ylim(0, 1)
            else:
                axis.set_ylim(0, zero_limit)

            if row_index == 0:
                axis.set_title(
                    f"{title}\n({unit_label})",
                    fontsize=12,
                )

            if column_index == 0:
                axis.set_ylabel(
                    f"{specimen.format}\n"
                    f"{len(rows)} fragments",
                    fontweight="bold",
                )

    figure.savefig(
        destination,
        dpi=160,
        metadata={
            "Title": "No Magic Result 001",
            "Description": "Deterministic file fragment statistics",
        },
    )

    plt.close(figure)


def run_analysis(
    specimens: list[Specimen],
    results_dir: Path,
    fragment_size: int = FRAGMENT_SIZE,
    sample_count: int = SAMPLE_COUNT,
    seed: int = SEED,
) -> None:
    """Collect measurements and generate investigation outputs."""

    observations = collect_statistics(
        specimens,
        fragment_size=fragment_size,
        sample_count=sample_count,
        seed=seed,
    )

    csv_path = results_dir / "data" / CSV_FILENAME
    figure_path = results_dir / "figures" / FIGURE_FILENAME

    write_csv(observations, csv_path)
    write_figure(observations, specimens, figure_path)

    print()
    print("Result 001 — Fragment Statistics")
    print("--------------------------------")

    for specimen in specimens:
        rows = [
            row
            for row in observations
            if row["source_id"] == specimen.source_id
            and row["format"] == specimen.format
        ]

        n = len(rows)

        mean_entropy = sum(
            row["entropy"] for row in rows
        ) / n

        mean_printable = sum(
            row["printable_fraction"] for row in rows
        ) / n

        mean_zero = sum(
            row["zero_fraction"] for row in rows
        ) / n

        print(
            f"{specimen.format:5s} "
            f"n={n:2d} "
            f"entropy={mean_entropy:.4f} "
            f"printable={mean_printable:.4f} "
            f"zero={mean_zero:.4f}"
        )

    print()
    print(f"Observations: {len(observations)}")
    print(f"CSV:    {csv_path}")
    print(f"Figure: {figure_path}")
