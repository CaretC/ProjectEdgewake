
"""Dataset source definitions and validation."""

import re

from dataclasses import dataclass
from urllib.parse import urlsplit


def _validate_filename(filename: str) -> None:
    """Require a safe, portable filename without directory components."""

    if not filename or filename != filename.strip():
        raise ValueError("Source filename cannot be empty or padded")

    if filename in (".", ".."):
        raise ValueError("Source filename cannot be a directory")

    # Reject path separators, Windows-invalid characters and controls.
    invalid_characters = '<>:"/\\|?*'

    if (
        any(char in invalid_characters for char in filename)
        or any(ord(char) < 32 or ord(char) == 127 for char in filename)
        or filename.endswith((".", " "))
    ):
        raise ValueError(f"Unsafe source filename: {filename}")

    # Windows device names are reserved even when extended.
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }

    stem = filename.split(".")[0].upper()

    if stem in reserved:
        raise ValueError(f"Reserved source filename: {filename}")


def _validate_sha256(checksum: str | None) -> None:
    """Require a 64-character hexadecimal SHA-256 or None."""

    if checksum is None:
        return

    if (
        not isinstance(checksum, str)
        or re.fullmatch(r"[0-9a-fA-F]{64}", checksum) is None
    ):
        raise ValueError(
            "SHA-256 must contain 64 hexadecimal characters or be null"
        )


def _validate_url(url: str) -> None:
    """Require an HTTPS URL with a host and no credentials."""

    if any(char.isspace() or ord(char) < 32 for char in url):
        raise ValueError(f"Invalid source URL: {url}")

    try:
        parsed = urlsplit(url)

        valid = (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )

        # Accessing port also checks for invalid port values.
        port = parsed.port

    except ValueError as error:
        raise ValueError(f"Invalid source URL: {url}") from error

    if not valid or port == 0:
        raise ValueError(f"Invalid HTTPS source URL: {url}")


@dataclass(frozen=True, slots=True)
class DatasetSource:
    """A validated, immutable description of a dataset source."""

    id: str
    format: str
    filename: str
    url: str
    sha256: str | None

    source_page: str | None = None
    license: str | None = None
    attribution: str | None = None

    def __post_init__(self) -> None:
        """Enforce invariants regardless of construction method."""

        required_strings = (
            "id",
            "format",
            "filename",
            "url",
        )

        for field in required_strings:
            value = getattr(self, field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid source field: {field}")

        optional_strings = (
            "source_page",
            "license",
            "attribution",
        )

        for field in optional_strings:
            value = getattr(self, field)

            if value is not None and not isinstance(value, str):
                raise ValueError(f"Invalid source field: {field}")

        _validate_filename(self.filename)
        _validate_sha256(self.sha256)
        _validate_url(self.url)

    @classmethod
    def from_dict(cls, data: dict) -> "DatasetSource":
        """Construct a validated source from manifest data."""

        if not isinstance(data, dict):
            raise ValueError("Source definition must be an object")

        required = (
            "id",
            "format",
            "filename",
            "url",
            "sha256",
        )

        optional = (
            "source_page",
            "license",
            "attribution",
        )

        # Ensure all required fields are present.
        for field in required:
            if field not in data:
                raise ValueError(
                    f"Missing required source field: {field}"
                )

        # Reject unknown or obsolete fields.
        allowed = set(required) | set(optional)
        unknown = set(data) - allowed

        if unknown:
            raise ValueError(
                f"Unknown source fields: {sorted(unknown)}"
            )

        # Construct the immutable source object.
        # __post_init__ performs field-level validation.
        return cls(
            **{field: data[field] for field in required},
            **{field: data.get(field) for field in optional},
        )
