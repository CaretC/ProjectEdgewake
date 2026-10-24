
"""Tests for fragment statistics collection and reporting."""

import csv
import tempfile
import unittest

from pathlib import Path

from scripts.analysis.fragment_statistics import (
    CSV_FIELDS,
    Specimen,
    collect_statistics,
    run_analysis,
    write_csv,
)

from scripts.dataset.hashing import hash_file


class TestFragmentStatistics(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.root = Path(self.directory.name)
        self.results_dir = self.root / "results"

    def make_specimen(
        self,
        filename: str,
        content: bytes,
        format_name: str = "TEST",
        source_id: str = "test-source",
    ) -> Specimen:
        """Create a local specimen with a real checksum."""

        path = self.root / filename
        path.write_bytes(content)

        return Specimen(
            format=format_name,
            source_id=source_id,
            path=path,
            sha256=hash_file(path),
        )

    # ---------------------------------------------------------
    # Measurement collection
    # ---------------------------------------------------------

    def test_collects_correct_fragment_statistics(self):
        specimen = self.make_specimen(
            "sample.bin",
            b"HEAD"
            + b"AAAA"
            + b"\x00" * 4
            + b"\x00\x01\x00\x01",
        )

        observations = collect_statistics(
            [specimen],
            fragment_size=4,
            sample_count=16,
            seed=42,
        )

        self.assertEqual(len(observations), 3)

        self.assertEqual(
            [row["offset"] for row in observations],
            [4, 8, 12],
        )

        # Four identical ASCII bytes.
        self.assertAlmostEqual(
            observations[0]["entropy"], 0.0
        )
        self.assertAlmostEqual(
            observations[0]["printable_fraction"], 1.0
        )
        self.assertAlmostEqual(
            observations[0]["zero_fraction"], 0.0
        )

        # Four zero bytes.
        self.assertAlmostEqual(
            observations[1]["entropy"], 0.0
        )
        self.assertAlmostEqual(
            observations[1]["printable_fraction"], 0.0
        )
        self.assertAlmostEqual(
            observations[1]["zero_fraction"], 1.0
        )

        # Two equally frequent byte values.
        self.assertAlmostEqual(
            observations[2]["entropy"], 1.0
        )
        self.assertAlmostEqual(
            observations[2]["zero_fraction"], 0.5
        )

    # ---------------------------------------------------------
    # Provenance
    # ---------------------------------------------------------

    def test_preserves_specimen_identity(self):
        first = self.make_specimen(
            "first.bin",
            b"HEAD" + b"AAAA" + b"BBBB",
            format_name="TXT",
            source_id="source-text",
        )

        second = self.make_specimen(
            "second.bin",
            b"HEAD" + b"\x00" * 4 + b"\xff" * 4,
            format_name="BMP",
            source_id="source-image",
        )

        observations = collect_statistics(
            [first, second],
            fragment_size=4,
            sample_count=16,
            seed=42,
        )

        self.assertEqual(len(observations), 4)

        for row in observations[:2]:
            self.assertEqual(row["format"], "TXT")
            self.assertEqual(row["source_id"], "source-text")
            self.assertEqual(row["filename"], "first.bin")
            self.assertEqual(row["file_sha256"], first.sha256)
            self.assertEqual(row["size"], 4)
            self.assertEqual(row["seed"], 42)

        for row in observations[2:]:
            self.assertEqual(row["format"], "BMP")
            self.assertEqual(row["source_id"], "source-image")
            self.assertEqual(row["filename"], "second.bin")
            self.assertEqual(row["file_sha256"], second.sha256)

    # ---------------------------------------------------------
    # CSV reproducibility
    # ---------------------------------------------------------

    def test_csv_is_complete_and_repeatable(self):
        specimen = self.make_specimen(
            "sample.bin",
            b"HEAD" + b"AAAA" + b"BBBB",
        )

        observations = collect_statistics(
            [specimen],
            fragment_size=4,
            sample_count=16,
            seed=42,
        )

        destination = self.results_dir / "data" / "test.csv"

        write_csv(observations, destination)

        self.assertTrue(destination.is_file())

        first_contents = destination.read_bytes()

        with destination.open(
            "r", encoding="utf-8", newline=""
        ) as file:
            reader = csv.DictReader(file)
            rows = list(reader)

            self.assertEqual(
                reader.fieldnames,
                list(CSV_FIELDS),
            )

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["offset"], "4")
        self.assertEqual(rows[1]["offset"], "8")

        self.assertEqual(rows[0]["entropy"], "0.000000")
        self.assertEqual(
            rows[0]["printable_fraction"], "1.000000"
        )

        # Writing the same observations again must produce
        # exactly the same CSV bytes.
        write_csv(observations, destination)

        self.assertEqual(
            destination.read_bytes(),
            first_contents,
        )

    # ---------------------------------------------------------
    # Figure and complete analysis
    # ---------------------------------------------------------

    def test_run_analysis_produces_csv_and_png(self):
        specimen = self.make_specimen(
            "sample.bin",
            b"HEAD" + b"AAAA" + b"BBBB",
        )

        run_analysis(
            specimens=[specimen],
            results_dir=self.results_dir,
            fragment_size=4,
            sample_count=16,
            seed=42,
        )

        csv_path = (
            self.results_dir
            / "data"
            / "001-fragment-statistics.csv"
        )

        figure_path = (
            self.results_dir
            / "figures"
            / "001-fragment-statistics.png"
        )

        self.assertTrue(csv_path.is_file())
        self.assertTrue(figure_path.is_file())

        # PNG file signature.
        self.assertEqual(
            figure_path.read_bytes()[:8],
            b"\x89PNG\r\n\x1a\n",
        )

        self.assertGreater(
            figure_path.stat().st_size,
            1000,
        )

    # ---------------------------------------------------------
    # Invalid input
    # ---------------------------------------------------------

    def test_rejects_specimen_without_eligible_fragments(self):
        specimen = self.make_specimen(
            "short.bin",
            b"1234567",
        )

        with self.assertRaisesRegex(
            ValueError, "No eligible fragments"
        ):
            collect_statistics(
                [specimen],
                fragment_size=4,
            )


if __name__ == "__main__":
    unittest.main()
