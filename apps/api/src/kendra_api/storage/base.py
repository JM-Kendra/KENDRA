"""Read-only document-store contract independent of host mount location."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import BinaryIO, Mapping

from kendra_api.readiness import ReadinessProbe


@dataclass(frozen=True, slots=True)
class StoredSource:
    logical_uri: str
    byte_length: int
    media_type: str


class DocumentStore(ReadinessProbe, ABC):
    """Resolve immutable source versions by stable IDs, never caller paths."""

    @abstractmethod
    def open_source(self, document_id: str, version_id: str) -> BinaryIO:
        """Open exact source bytes for reading."""

    @abstractmethod
    def read_source_range(
        self,
        document_id: str,
        version_id: str,
        offset: int,
        length: int,
    ) -> bytes:
        """Read a bounded byte range from an exact source version."""

    @abstractmethod
    def read_manifest(self, document_id: str, version_id: str) -> Mapping[str, object]:
        """Read the durable source-version manifest."""

    @abstractmethod
    def source_info(self, document_id: str, version_id: str) -> StoredSource:
        """Return logical identity and non-secret object metadata."""

    @abstractmethod
    def verify_sha256(self, document_id: str, version_id: str, expected: str) -> bool:
        """Verify exact source bytes against a lowercase SHA-256 value."""
