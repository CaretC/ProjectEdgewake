
"""Extract and measure fixed-size fragments from binary files."""

import argparse
import math
import random

from collections import Counter
from dataclasses import dataclass
from pathlib import Path


DEFAULT_FRAGMENT_SIZE = 4096
DEFAULT_SAMPLE_COUNT = 16
DEFAULT_SEED = 42


@dataclass(frozen=True, slots=True)
class Fragment:
    offset: int
    data: bytes


@dataclass(frozen=True, slots=True)
class FragmentMetrics:
    entropy: float
    printable_fraction: float
    zero_fraction: float


def sample_fragments(
    path: Path,
    size: int = DEFAULT_FRAGMENT_SIZE,
    count: int = DEFAULT_SAMPLE_COUNT,
    seed: int = DEFAULT_SEED,
) -> list[Fragment]:
    """Sample complete, non-overlapping fragments after the first block."""

    if size <= 0:
        raise ValueError("Fragment size must be positive")

    if count <= 0:
        raise ValueError("Sample count must be positive")

    file_size = path.stat().st_size

    # Aligned blocks only, excluding the first block and any
    # incomplete final block.
    offsets = range(
        size,
        file_size - size + 1,
        size,
    )

    rng = random.Random(seed)
    selected = sorted(
        rng.sample(offsets, min(count, len(offsets)))
    )

    fragments = []

    with path.open("rb") as file:
        for offset in selected:
            file.seek(offset)
            data = file.read(size)

            if len(data) != size:
                raise IOError(
                    f"Incomplete fragment at offset {offset}"
                )

            fragments.append(Fragment(offset, data))

    return fragments


def measure_fragment(data: bytes) -> FragmentMetrics:
    """Calculate simple byte-level statistical properties."""

    if not data:
        raise ValueError("Cannot measure an empty fragment")

    length = len(data)
    frequencies = Counter(data)

    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in frequencies.values()
    )

    # Normalise negative zero produced by the entropy calculation.
    # This ensures consistent values in downstream reporting.
    if entropy == 0.0:
        entropy = 0.0

    # Printable ASCII plus common text whitespace.
    printable = sum(
        32 <= byte <= 126 or byte in (9, 10, 13)
        for byte in data
    )

    zeros = frequencies.get(0, 0)

    return FragmentMetrics(
        entropy=entropy,
        printable_fraction=printable / length,
        zero_fraction=zeros / length,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explore statistical properties of file fragments."
    )

    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--size", type=int, default=DEFAULT_FRAGMENT_SIZE
    )
    parser.add_argument(
        "--count", type=int, default=DEFAULT_SAMPLE_COUNT
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED
    )

    args = parser.parse_args()

    fragments = sample_fragments(
        args.path,
        size=args.size,
        count=args.count,
        seed=args.seed,
    )

    print(f"File: {args.path}")
    print(f"Fragment size: {args.size} bytes")
    print(f"Seed: {args.seed}")
    print(f"Fragments sampled: {len(fragments)}")
    print()

    if not fragments:
        print("No eligible complete fragments.")
        return

    print(
        f"{'Offset':>12} "
        f"{'Entropy':>10} "
        f"{'Printable':>12} "
        f"{'Zero':>10}"
    )

    measurements = []

    for fragment in fragments:
        metrics = measure_fragment(fragment.data)
        measurements.append(metrics)

        print(
            f"{fragment.offset:12d} "
            f"{metrics.entropy:10.4f} "
            f"{metrics.printable_fraction:12.4f} "
            f"{metrics.zero_fraction:10.4f}"
        )

    n = len(measurements)

    print()
    print("Averages:")
    print(
        f"  Entropy:   "
        f"{sum(m.entropy for m in measurements) / n:.4f} bits/byte"
    )
    print(
        f"  Printable: "
        f"{sum(m.printable_fraction for m in measurements) / n:.4f}"
    )
    print(
        f"  Zero:      "
        f"{sum(m.zero_fraction for m in measurements) / n:.4f}"
    )


if __name__ == "__main__":
    main()
