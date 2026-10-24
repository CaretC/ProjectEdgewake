
"""Tests for source acquisition and integrity handling."""

import hashlib
import io
import tempfile
import unittest

from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from scripts.dataset.source import DatasetSource
from scripts.dataset.download_sources import (
    SOURCE_DIR,
    HTTPSRedirectHandler,
    acquire_sources,
    main,
)


class TestSourceAcquisition(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.source_dir = Path(self.directory.name)

        self.sample = b"No Magic experimental data"
        self.checksum = hashlib.sha256(self.sample).hexdigest()

    def make_source(self, sha256=None, filename="example.txt"):
        return DatasetSource(
            id="test-001",
            format="txt",
            purpose="txt",
            filename=filename,
            url="https://example.org/example.txt",
            sha256=sha256,
        )

    # ---------------------------------------------------------
    # New downloads
    # ---------------------------------------------------------

    @patch("scripts.dataset.download_sources._open_source")
    def test_download_unpinned_source(self, mock_open):
        mock_open.return_value = io.BytesIO(self.sample)

        source = self.make_source()

        acquire_sources([source], self.source_dir)

        destination = self.source_dir / source.filename

        self.assertTrue(destination.exists())
        self.assertEqual(destination.read_bytes(), self.sample)
        mock_open.assert_called_once_with(source.url)

    @patch("scripts.dataset.download_sources._open_source")
    def test_download_with_valid_checksum(self, mock_open):
        mock_open.return_value = io.BytesIO(self.sample)

        source = self.make_source(sha256=self.checksum)

        acquire_sources([source], self.source_dir)

        destination = self.source_dir / source.filename

        self.assertEqual(destination.read_bytes(), self.sample)
        mock_open.assert_called_once_with(source.url)

    @patch("scripts.dataset.download_sources._open_source")
    def test_reject_download_with_wrong_checksum(self, mock_open):
        mock_open.return_value = io.BytesIO(b"incorrect data")

        source = self.make_source(sha256=self.checksum)

        with self.assertRaises(ValueError):
            acquire_sources([source], self.source_dir)

        destination = self.source_dir / source.filename

        self.assertFalse(destination.exists())

        # Failed verification must leave no temporary files.
        self.assertEqual(list(self.source_dir.iterdir()), [])

    # ---------------------------------------------------------
    # Existing source files
    # ---------------------------------------------------------

    @patch("scripts.dataset.download_sources._open_source")
    def test_skip_existing_verified_source(self, mock_open):
        destination = self.source_dir / "example.txt"
        destination.write_bytes(self.sample)

        source = self.make_source(sha256=self.checksum)

        acquire_sources([source], self.source_dir)

        mock_open.assert_not_called()
        self.assertEqual(destination.read_bytes(), self.sample)

    @patch("scripts.dataset.download_sources._open_source")
    def test_reject_existing_checksum_mismatch(self, mock_open):
        destination = self.source_dir / "example.txt"
        destination.write_bytes(b"modified data")

        source = self.make_source(sha256=self.checksum)

        with self.assertRaises(ValueError):
            acquire_sources([source], self.source_dir)

        mock_open.assert_not_called()
        self.assertEqual(destination.read_bytes(), b"modified data")

    @patch("scripts.dataset.download_sources._open_source")
    def test_preserve_existing_unpinned_source(self, mock_open):
        destination = self.source_dir / "example.txt"
        destination.write_bytes(self.sample)

        source = self.make_source(sha256=None)

        acquire_sources([source], self.source_dir)

        mock_open.assert_not_called()
        self.assertEqual(destination.read_bytes(), self.sample)

    # ---------------------------------------------------------
    # Explicit replacement
    # ---------------------------------------------------------

    @patch("scripts.dataset.download_sources._open_source")
    def test_replace_unpinned_source(self, mock_open):
        destination = self.source_dir / "example.txt"
        destination.write_bytes(b"old content")

        mock_open.return_value = io.BytesIO(self.sample)

        source = self.make_source(sha256=None)

        acquire_sources(
            [source],
            self.source_dir,
            replace=True,
        )

        self.assertEqual(destination.read_bytes(), self.sample)
        mock_open.assert_called_once_with(source.url)

    @patch("scripts.dataset.download_sources._open_source")
    def test_cannot_replace_pinned_source(self, mock_open):
        destination = self.source_dir / "example.txt"
        destination.write_bytes(b"old content")

        source = self.make_source(sha256=self.checksum)

        with self.assertRaisesRegex(
            ValueError, "Cannot replace pinned source"
        ):
            acquire_sources(
                [source],
                self.source_dir,
                replace=True,
            )

        mock_open.assert_not_called()
        self.assertEqual(destination.read_bytes(), b"old content")

    # ---------------------------------------------------------
    # Preflight validation
    # ---------------------------------------------------------

    @patch("scripts.dataset.download_sources._open_source")
    def test_preflight_before_downloading(self, mock_open):
        first = self.make_source(
            filename="new.txt",
            sha256=None,
        )

        second = self.make_source(
            filename="existing.txt",
            sha256=self.checksum,
        )

        existing = self.source_dir / "existing.txt"
        existing.write_bytes(b"incorrect data")

        with self.assertRaises(ValueError):
            acquire_sources(
                [first, second],
                self.source_dir,
            )

        # Detect the mismatch before starting any downloads.
        mock_open.assert_not_called()

        self.assertFalse(
            (self.source_dir / "new.txt").exists()
        )

    # ---------------------------------------------------------
    # Interrupted downloads
    # ---------------------------------------------------------

    @patch("scripts.dataset.download_sources._open_source")
    def test_interrupted_download(self, mock_open):

        class BrokenStream(io.BytesIO):
            """Return partial data before simulating a failure."""

            def __init__(self):
                super().__init__(b"partial content")
                self.read_count = 0

            def read(self, size=-1):
                self.read_count += 1

                if self.read_count > 1:
                    raise OSError("Simulated connection failure")

                return super().read(size)

        mock_open.return_value = BrokenStream()

        source = self.make_source()

        with self.assertRaisesRegex(
            OSError, "Simulated connection failure"
        ):
            acquire_sources([source], self.source_dir)

        # No destination or temporary files should remain.
        self.assertEqual(list(self.source_dir.iterdir()), [])

    @patch("scripts.dataset.download_sources._open_source")
    def test_interrupted_replacement_preserves_original(self, mock_open):

        class BrokenStream(io.BytesIO):

            def read(self, size=-1):
                raise OSError("Simulated connection failure")

        destination = self.source_dir / "example.txt"
        destination.write_bytes(b"original content")

        mock_open.return_value = BrokenStream()

        source = self.make_source(sha256=None)

        with self.assertRaises(OSError):
            acquire_sources(
                [source],
                self.source_dir,
                replace=True,
            )

        # Original content must survive a failed replacement.
        self.assertEqual(
            destination.read_bytes(),
            b"original content",
        )

        # No abandoned temporary files.
        self.assertEqual(
            list(self.source_dir.iterdir()),
            [destination],
        )

    # ---------------------------------------------------------
    # HTTPS redirect validation
    # ---------------------------------------------------------

    def test_rejects_http_redirect(self):
        handler = HTTPSRedirectHandler()

        request = Request(
            "https://example.org/example.txt"
        )

        with self.assertRaises(HTTPError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "http://example.org/example.txt",
            )


class TestDownloaderEntryPoint(unittest.TestCase):

    # ---------------------------------------------------------
    # Application orchestration
    # ---------------------------------------------------------

    def test_main_loads_and_acquires_sources(self):
        source = DatasetSource(
            id="test-001",
            format="txt",
            purpose="txt",
            filename="example.txt",
            url="https://example.org/example.txt",
            sha256=None,
        )

        output = io.StringIO()

        with patch(
            "scripts.dataset.download_sources.load_manifest",
            return_value=[source],
        ) as mock_loader, patch(
            "scripts.dataset.download_sources.acquire_sources"
        ) as mock_acquire:

            with redirect_stdout(output):
                main()

        mock_loader.assert_called_once()

        mock_acquire.assert_called_once_with(
            [source],
            SOURCE_DIR,
            replace=False,
        )

        result = output.getvalue()

        self.assertIn("Loaded 1 dataset sources", result)
        self.assertIn("test-001", result)
        self.assertIn("example.txt", result)


if __name__ == "__main__":
    unittest.main()
