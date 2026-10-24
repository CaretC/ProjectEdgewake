"""Dataset source definitions and validation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetSource:
    id: str
    format: str
    purpose: str
    filename: str
    url: str
    sha256: str | None

    source_page: str | None = None
    license: str | None = None
    attribution: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "DatasetSource":
        """Construct a source from an untrusted dictionary."""

        required = (
            "id",
            "format",
            "purpose",
            "filename",
            "url",
            "sha256",
        )

        for field in required:
            if field not in data:
                raise ValueError(
                    f"Missing required source field: {field}"
                )

        for field in required[:-1]:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid source field: {field}"
                )

        checksum = data["sha256"]

        if checksum is not None and not isinstance(checksum, str):
            raise ValueError("sha256 must be a string or null")

        optional = ("source_page", "license", "attribution")

        for field in optional:
            value = data.get(field)

            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"Invalid source field: {field}"
                )

        return cls(
            **{field: data[field] for field in required},
            **{field: data.get(field) for field in optional},
        )