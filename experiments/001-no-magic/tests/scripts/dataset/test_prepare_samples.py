
"""Tests for reproducible dataset sample generation."""

import tempfile
import unittest
import zipfile

from pathlib import Path

from PIL import Image

from scripts.dataset.hashing import hash_file
from scripts.dataset.prepare_samples import (
    generate_bmp,
    generate_zip,
)


class TestSampleGeneration(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.root = Path(self.directory.name)
        self.source_dir = self.root / "source"
        self.output_dir = self.root / "generated"

        self.source_dir.mkdir()
        self.output_dir.mkdir()

    # ---------------------------------------------------------
    # BMP generation
    # ---------------------------------------------------------

    def test_generate_bmp(self):
        source = self.source_dir / "test.png"
        destination = self.output_dir / "test.bmp"

        image = Image.new("RGB", (17, 11), (100, 150, 200))
        image.save(source)

        generate_bmp(source, destination)

        self.assertTrue(destination.exists())

        with Image.open(destination) as result:
            self.assertEqual(result.format, "BMP")
            self.assertEqual(result.mode, "RGB")
            self.assertEqual(result.size, (17, 11))
            self.assertEqual(
                result.getpixel((0, 0)),
                (100, 150, 200),
            )

        # BMP file header and 24-bit pixel encoding.
        data = destination.read_bytes()

        self.assertEqual(data[:2], b"BM")
        self.assertEqual(
            int.from_bytes(data[28:30], "little"),
            24,
        )

    # ---------------------------------------------------------
    # ZIP generation
    # ---------------------------------------------------------

    def test_generate_zip(self):
        first = self.source_dir / "example.txt"
        second = self.source_dir / "example.csv"

        first.write_bytes(b"Example text")
        second.write_bytes(b"a,b\n1,2\n")

        destination = self.output_dir / "test.zip"

        generate_zip([first, second], destination)

        self.assertTrue(destination.exists())

        with zipfile.ZipFile(destination) as archive:
            self.assertEqual(
                archive.namelist(),
                ["example.txt", "example.csv"],
            )

            self.assertEqual(
                archive.read("example.txt"),
                b"Example text",
            )

            self.assertEqual(
                archive.read("example.csv"),
                b"a,b\n1,2\n",
            )

            self.assertIsNone(archive.testzip())

    def test_zip_metadata(self):
        source = self.source_dir / "example.txt"
        source.write_bytes(b"Some test content")

        destination = self.output_dir / "test.zip"

        generate_zip([source], destination)

        with zipfile.ZipFile(destination) as archive:
            info = archive.getinfo("example.txt")

            self.assertEqual(
                info.compress_type,
                zipfile.ZIP_DEFLATED,
            )

            self.assertEqual(
                info.date_time,
                (1980, 1, 1, 0, 0, 0),
            )

    # ---------------------------------------------------------
    # Reproducibility
    # ---------------------------------------------------------

    def test_repeatable_generation(self):
        source = self.source_dir / "example.txt"
        source.write_bytes(b"Repeatable test data" * 100)

        first = self.output_dir / "first.zip"
        second = self.output_dir / "second.zip"

        generate_zip([source], first)
        generate_zip([source], second)

        self.assertEqual(
            hash_file(first),
            hash_file(second),
        )

    # ---------------------------------------------------------
    # Output preservation
    # ---------------------------------------------------------

    def test_reject_existing_output(self):
        source = self.source_dir / "example.txt"
        source.write_bytes(b"New content")

        destination = self.output_dir / "existing.zip"
        destination.write_bytes(b"Original content")

        with self.assertRaises(FileExistsError):
            generate_zip([source], destination)

        self.assertEqual(
            destination.read_bytes(),
            b"Original content",
        )


if __name__ == "__main__":
    unittest.main()
