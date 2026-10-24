
"""Generate experimental file samples from existing source material."""

import zipfile

from pathlib import Path
from PIL import Image


# Fixed ZIP metadata for best-effort reproducibility.
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
ZIP_PERMISSIONS = 0o100644 << 16


def generate_bmp(source: Path, destination: Path) -> None:
    """Convert an image to an uncompressed 24-bit RGB BMP."""

    with Image.open(source) as image:
        rgb = image.convert("RGB")

        # Exclusive creation prevents overwriting existing files.
        with destination.open("xb") as output:
            rgb.save(output, format="BMP")


def generate_zip(
    sources: list[Path],
    destination: Path,
    compresslevel: int = 6,
) -> None:
    """Create a mixed-content DEFLATE archive with fixed metadata."""

    with zipfile.ZipFile(destination, mode="x") as archive:
        for source in sources:
            info = zipfile.ZipInfo(
                filename=source.name,
                date_time=ZIP_TIMESTAMP,
            )

            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = ZIP_PERMISSIONS

            archive.writestr(
                info,
                source.read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=compresslevel,
            )
