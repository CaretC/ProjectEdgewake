
"""Tests for dataset manifest loading and validation."""

import json
import tempfile
import unittest

from pathlib import Path

from scripts.dataset.manifest import load_manifest
from scripts.dataset.source import DatasetSource


class TestManifest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.path = Path(self.directory.name) / "sources.json"

        self.valid_source = {
            "id": "test-001",
            "format": "txt",
            "purpose": "txt",
            "filename": "example.txt",
            "url": "https://example.org/example.txt",
            "sha256": None,
        }

    def write_manifest(self, manifest):
        self.path.write_text(
            json.dumps(manifest),
            encoding="utf-8"
        )

    # ---------------------------------------------------------
    # Valid manifest definitions
    # ---------------------------------------------------------

    def test_valid_manifest(self):
        self.write_manifest({
            "sources": [self.valid_source]
        })

        sources = load_manifest(self.path)

        self.assertEqual(len(sources), 1)
        self.assertIsInstance(sources[0], DatasetSource)
        self.assertEqual(sources[0].id, "test-001")

    def test_empty_sources(self):
        self.write_manifest({
            "sources": []
        })

        sources = load_manifest(self.path)

        self.assertEqual(sources, [])

    def test_multiple_sources(self):
        second = {
            **self.valid_source,
            "id": "test-002",
            "filename": "another.txt",
        }

        self.write_manifest({
            "sources": [self.valid_source, second]
        })

        sources = load_manifest(self.path)

        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[1].id, "test-002")

    # ---------------------------------------------------------
    # Manifest structure validation
    # ---------------------------------------------------------

    def test_invalid_manifest_root(self):
        self.write_manifest([])

        with self.assertRaises(ValueError):
            load_manifest(self.path)

    def test_missing_sources(self):
        self.write_manifest({})

        with self.assertRaises(ValueError):
            load_manifest(self.path)

    def test_sources_not_list(self):
        self.write_manifest({
            "sources": "invalid"
        })

        with self.assertRaises(ValueError):
            load_manifest(self.path)

    def test_invalid_source_entry(self):
        self.write_manifest({
            "sources": ["not-an-object"]
        })

        with self.assertRaises(ValueError):
            load_manifest(self.path)

    def test_invalid_source_definition(self):
        self.write_manifest({
            "sources": [{"id": "incomplete"}]
        })

        with self.assertRaises(ValueError):
            load_manifest(self.path)

    def test_malformed_json(self):
        self.path.write_text(
            '{"sources": [',
            encoding="utf-8"
        )

        with self.assertRaises(json.JSONDecodeError):
            load_manifest(self.path)

    # ---------------------------------------------------------
    # Collection-level validation
    # ---------------------------------------------------------

    def test_duplicate_source_ids(self):
        second = {
            **self.valid_source,
            "filename": "another.txt",
        }

        self.write_manifest({
            "sources": [self.valid_source, second]
        })

        with self.assertRaisesRegex(
            ValueError, "Duplicate source ID"
        ):
            load_manifest(self.path)

    def test_duplicate_source_ids_case_insensitive(self):
        second = {
            **self.valid_source,
            "id": "TEST-001",
            "filename": "another.txt",
        }

        self.write_manifest({
            "sources": [self.valid_source, second]
        })

        with self.assertRaisesRegex(
            ValueError, "Duplicate source ID"
        ):
            load_manifest(self.path)

    def test_duplicate_filenames(self):
        second = {
            **self.valid_source,
            "id": "test-002",
        }

        self.write_manifest({
            "sources": [self.valid_source, second]
        })

        with self.assertRaisesRegex(
            ValueError, "Duplicate filename"
        ):
            load_manifest(self.path)

    def test_duplicate_filenames_case_insensitive(self):
        second = {
            **self.valid_source,
            "id": "test-002",
            "filename": "EXAMPLE.TXT",
        }

        self.write_manifest({
            "sources": [self.valid_source, second]
        })

        with self.assertRaisesRegex(
            ValueError, "Duplicate filename"
        ):
            load_manifest(self.path)


if __name__ == "__main__":
    unittest.main()
