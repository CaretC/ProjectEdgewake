
"""Tests for deterministic fragment extraction and measurement."""

import tempfile
import unittest

from pathlib import Path

from scripts.dataset.fragments import (
    measure_fragment,
    sample_fragments,
)


class TestFragments(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_skips_header_and_preserves_offsets(self):
        path = self.root / "sample.bin"

        path.write_bytes(
            b"HEAD" +
            b"AAAA" +
            b"BBBB" +
            b"CCCC" +
            b"DDDD"
        )

        fragments = sample_fragments(
            path, size=4, count=10, seed=42
        )

        self.assertEqual(
            [fragment.offset for fragment in fragments],
            [4, 8, 12, 16],
        )

        self.assertEqual(
            [fragment.data for fragment in fragments],
            [b"AAAA", b"BBBB", b"CCCC", b"DDDD"],
        )

    def test_sampling_is_deterministic(self):
        path = self.root / "sample.bin"
        path.write_bytes(bytes(range(100)))

        first = sample_fragments(
            path, size=4, count=5, seed=123
        )
        second = sample_fragments(
            path, size=4, count=5, seed=123
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)

        offsets = [fragment.offset for fragment in first]

        self.assertEqual(len(offsets), len(set(offsets)))
        self.assertTrue(all(offset >= 4 for offset in offsets))

    def test_short_file_has_no_eligible_fragments(self):
        path = self.root / "short.bin"
        path.write_bytes(b"1234567")

        self.assertEqual(
            sample_fragments(path, size=4),
            [],
        )

    def test_rejects_invalid_parameters(self):
        path = self.root / "sample.bin"
        path.write_bytes(b"12345678")

        with self.assertRaises(ValueError):
            sample_fragments(path, size=0)

        with self.assertRaises(ValueError):
            sample_fragments(path, count=0)

    def test_entropy(self):
        self.assertAlmostEqual(
            measure_fragment(b"\x00" * 100).entropy,
            0.0,
        )

        self.assertAlmostEqual(
            measure_fragment(b"\x00\x01" * 50).entropy,
            1.0,
        )

    def test_byte_fractions(self):
        metrics = measure_fragment(
            b"AB\n\x00"
        )

        self.assertAlmostEqual(
            metrics.printable_fraction, 0.75
        )
        self.assertAlmostEqual(
            metrics.zero_fraction, 0.25
        )

    def test_rejects_empty_measurement(self):
        with self.assertRaises(ValueError):
            measure_fragment(b"")


if __name__ == "__main__":
    unittest.main()
