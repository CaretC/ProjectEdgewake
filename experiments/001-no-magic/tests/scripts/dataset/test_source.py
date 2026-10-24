
"""Tests for dataset source definitions and validation."""

import unittest

from dataclasses import FrozenInstanceError

from scripts.dataset.source import DatasetSource


class TestDatasetSource(unittest.TestCase):

    def setUp(self):
        self.valid_source = {
            "id": "test-001",
            "format": "txt",
            "filename": "example.txt",
            "url": "https://example.org/example.txt",
            "sha256": None,
        }

    # ---------------------------------------------------------
    # Valid source definitions
    # ---------------------------------------------------------

    def test_valid_source(self):
        source = DatasetSource.from_dict(self.valid_source)

        self.assertEqual(source.id, "test-001")
        self.assertEqual(source.format, "txt")
        self.assertEqual(source.filename, "example.txt")
        self.assertIsNone(source.sha256)

    def test_optional_fields(self):
        data = {
            **self.valid_source,
            "source_page": "https://example.org",
            "license": "CC0",
            "attribution": "Example Author",
        }

        source = DatasetSource.from_dict(data)

        self.assertEqual(source.license, "CC0")
        self.assertEqual(source.attribution, "Example Author")
        self.assertEqual(
            source.source_page,
            "https://example.org"
        )

    def test_valid_sha256(self):
        data = {
            **self.valid_source,
            "sha256": "a" * 64,
        }

        source = DatasetSource.from_dict(data)

        self.assertEqual(source.sha256, "a" * 64)

    # ---------------------------------------------------------
    # Required field validation
    # ---------------------------------------------------------

    def test_missing_required_fields(self):
        for field in self.valid_source:
            with self.subTest(field=field):
                data = self.valid_source.copy()
                del data[field]

                with self.assertRaises(ValueError):
                    DatasetSource.from_dict(data)

    def test_invalid_required_types(self):
        invalid_values = [None, 123, [], {}, ""]

        for field in ("id", "format", "filename", "url"):
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    data = {
                        **self.valid_source,
                        field: value,
                    }

                    with self.assertRaises(ValueError):
                        DatasetSource.from_dict(data)

    def test_invalid_optional_field_type(self):
        data = {
            **self.valid_source,
            "license": 12345,
        }

        with self.assertRaises(ValueError):
            DatasetSource.from_dict(data)

    # ---------------------------------------------------------
    # Unknown field validation
    # ---------------------------------------------------------

    def test_unknown_fields(self):
        invalid_fields = {
            "purpose": "txt",
            "unexpected": "value",
        }

        for field, value in invalid_fields.items():
            with self.subTest(field=field):
                data = {
                    **self.valid_source,
                    field: value,
                }

                with self.assertRaisesRegex(
                    ValueError, "Unknown source fields"
                ):
                    DatasetSource.from_dict(data)

    # ---------------------------------------------------------
    # Filename validation
    # ---------------------------------------------------------

    def test_unsafe_filenames(self):
        invalid_names = [
            "../secret.txt",
            "../../secret.txt",
            "/tmp/file.txt",
            r"..\secret.txt",
            r"C:\temp\file.txt",
            "CON.txt",
            "NUL",
            "file:name.txt",
            "file.txt.",
            "file.txt ",
            "",
        ]

        for filename in invalid_names:
            with self.subTest(filename=filename):
                data = {
                    **self.valid_source,
                    "filename": filename,
                }

                with self.assertRaises(ValueError):
                    DatasetSource.from_dict(data)

    # ---------------------------------------------------------
    # SHA-256 validation
    # ---------------------------------------------------------

    def test_invalid_sha256_values(self):
        invalid_hashes = [
            "",
            "banana",
            "a" * 63,
            "g" * 64,
            "a" * 65,
            12345,
        ]

        for checksum in invalid_hashes:
            with self.subTest(checksum=checksum):
                data = {
                    **self.valid_source,
                    "sha256": checksum,
                }

                with self.assertRaises(ValueError):
                    DatasetSource.from_dict(data)

    # ---------------------------------------------------------
    # URL validation
    # ---------------------------------------------------------

    def test_invalid_urls(self):
        invalid_urls = [
            "",
            "not-a-url",
            "http://example.org/file.txt",
            "ftp://example.org/file.txt",
            "https://",
            "https:///file.txt",
            "https://user:password@example.org/file.txt",
        ]

        for url in invalid_urls:
            with self.subTest(url=url):
                data = {
                    **self.valid_source,
                    "url": url,
                }

                with self.assertRaises(ValueError):
                    DatasetSource.from_dict(data)

    # ---------------------------------------------------------
    # Object invariants
    # ---------------------------------------------------------

    def test_source_is_immutable(self):
        source = DatasetSource.from_dict(self.valid_source)

        with self.assertRaises(FrozenInstanceError):
            source.filename = "changed.txt"

    def test_direct_construction_is_validated(self):
        data = {
            **self.valid_source,
            "filename": "../escape.txt",
        }

        with self.assertRaises(ValueError):
            DatasetSource(**data)


if __name__ == "__main__":
    unittest.main()
