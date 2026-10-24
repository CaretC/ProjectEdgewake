
"""Tests for dataset source definitions."""

import unittest

from dataclasses import FrozenInstanceError

from scripts.dataset.source import DatasetSource


class TestDatasetSource(unittest.TestCase):

    def setUp(self):
        self.valid_source = {
            "id": "test-001",
            "format": "txt",
            "purpose": "txt",
            "filename": "example.txt",
            "url": "https://example.org/example.txt",
            "sha256": None,
        }

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

    def test_missing_required_fields(self):
        for field in self.valid_source:
            with self.subTest(field=field):
                data = self.valid_source.copy()
                del data[field]

                with self.assertRaises(ValueError):
                    DatasetSource.from_dict(data)

    def test_invalid_required_types(self):
        invalid_values = [None, 123, [], {}, ""]

        for field in ("id", "format", "purpose", "filename", "url"):
            for value in invalid_values:
                with self.subTest(field=field, value=value):
                    data = {
                        **self.valid_source,
                        field: value,
                    }

                    with self.assertRaises(ValueError):
                        DatasetSource.from_dict(data)

    def test_invalid_sha256_type(self):
        data = {
            **self.valid_source,
            "sha256": 12345,
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

    def test_source_is_immutable(self):
        source = DatasetSource.from_dict(self.valid_source)

        with self.assertRaises(FrozenInstanceError):
            source.filename = "changed.txt"


if __name__ == "__main__":
    unittest.main()
