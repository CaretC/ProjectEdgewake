
"""Tests for the dataset downloader entry point."""

import io
import unittest

from contextlib import redirect_stdout
from unittest.mock import patch

from scripts.dataset.download_sources import main
from scripts.dataset.source import DatasetSource


class TestDownloader(unittest.TestCase):

    def test_main_loads_and_reports_sources(self):
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
            return_value=[source]
        ) as mock_loader:
            with redirect_stdout(output):
                main()

        mock_loader.assert_called_once()

        result = output.getvalue()

        self.assertIn("Loaded 1 dataset sources", result)
        self.assertIn("test-001", result)
        self.assertIn("example.txt", result)


if __name__ == "__main__":
    unittest.main()
