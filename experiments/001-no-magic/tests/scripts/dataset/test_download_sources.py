import json
import tempfile
import unittest
from pathlib import Path

from scripts.dataset.download_sources import load_manifest


class TestManifest(unittest.TestCase):

    def test_valid_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"

            manifest = {
                "sources": [
                    {
                        "id": "test-001",
                        "format": "txt",
                        "purpose": "txt",
                        "filename": "example.txt",
                        "url": "https://example.org/example.txt",
                        "sha256": None,
                    }
                ]
            }

            path.write_text(json.dumps(manifest), encoding="utf-8")

            sources = load_manifest(path)

            self.assertEqual(len(sources), 1)
            self.assertEqual(sources[0]["id"], "test-001")


if __name__ == "__main__":
    unittest.main()