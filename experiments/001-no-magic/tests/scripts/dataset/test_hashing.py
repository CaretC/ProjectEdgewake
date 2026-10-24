
"""Tests for dataset file hashing and verification."""

import hashlib
import tempfile
import unittest

from pathlib import Path

from scripts.dataset.hashing import hash_file, verify_file


class TestHashing(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.path = Path(self.directory.name) / "sample.bin"

    def write_sample(self, content: bytes):
        self.path.write_bytes(content)

    # ---------------------------------------------------------
    # SHA-256 calculation
    # ---------------------------------------------------------

    def test_known_sha256(self):
        self.write_sample(b"abc")

        expected = (
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad"
        )

        self.assertEqual(hash_file(self.path), expected)

    def test_empty_file(self):
        self.write_sample(b"")

        expected = hashlib.sha256(b"").hexdigest()

        self.assertEqual(hash_file(self.path), expected)

    def test_binary_content(self):
        content = bytes(range(256)) * 32
        self.write_sample(content)

        expected = hashlib.sha256(content).hexdigest()

        self.assertEqual(hash_file(self.path), expected)

    def test_large_file(self):
        content = bytes(range(256)) * 8192
        self.write_sample(content)

        expected = hashlib.sha256(content).hexdigest()

        self.assertEqual(hash_file(self.path), expected)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            hash_file(self.path)

    # ---------------------------------------------------------
    # Integrity verification
    # ---------------------------------------------------------

    def test_valid_checksum(self):
        self.write_sample(b"known content")

        expected = hashlib.sha256(
            b"known content"
        ).hexdigest()

        verify_file(self.path, expected)

    def test_invalid_checksum(self):
        self.write_sample(b"known content")

        incorrect = hashlib.sha256(
            b"different content"
        ).hexdigest()

        with self.assertRaises(ValueError):
            verify_file(self.path, incorrect)

    def test_detects_modified_file(self):
        self.write_sample(b"original content")

        expected = hash_file(self.path)

        self.write_sample(b"modified content")

        with self.assertRaises(ValueError):
            verify_file(self.path, expected)


if __name__ == "__main__":
    unittest.main()
