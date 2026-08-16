"""Read-only folder-backed document store with a replaceable configured root."""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import BinaryIO, Mapping

from kendra_api.readiness import ProbeResult
from kendra_api.storage.base import DocumentStore, StoredSource


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class LocalDocumentStore(DocumentStore):
    """Map stable IDs to the ADR-002 layout below one configured root."""

    name = "document_store"

    def __init__(self, root: Path) -> None:
        self._root = root.resolve(strict=False)

    @staticmethod
    def _validate_identifier(value: str, field: str) -> str:
        if not _IDENTIFIER.fullmatch(value):
            raise ValueError(f"invalid {field}")
        return value

    def _contained(self, candidate: Path) -> Path:
        resolved = candidate.resolve(strict=False)
        if not resolved.is_relative_to(self._root):
            raise ValueError("resolved source escapes the configured document store")
        return resolved

    def _source_path(self, document_id: str, version_id: str) -> Path:
        document_id = self._validate_identifier(document_id, "document_id")
        version_id = self._validate_identifier(version_id, "version_id")
        return self._contained(
            self._root / "objects" / document_id / version_id / "source.pdf"
        )

    def _manifest_path(self, document_id: str, version_id: str) -> Path:
        document_id = self._validate_identifier(document_id, "document_id")
        version_id = self._validate_identifier(version_id, "version_id")
        return self._contained(
            self._root / "manifests" / document_id / f"{version_id}.json"
        )

    def open_source(self, document_id: str, version_id: str) -> BinaryIO:
        return self._source_path(document_id, version_id).open("rb")

    def read_source_range(
        self,
        document_id: str,
        version_id: str,
        offset: int,
        length: int,
    ) -> bytes:
        if offset < 0 or length <= 0:
            raise ValueError("offset must be nonnegative and length must be positive")
        with self.open_source(document_id, version_id) as source:
            source.seek(offset)
            return source.read(length)

    def read_manifest(self, document_id: str, version_id: str) -> Mapping[str, object]:
        with self._manifest_path(document_id, version_id).open(
            "r", encoding="utf-8"
        ) as manifest:
            parsed = json.load(manifest)
        if not isinstance(parsed, dict):
            raise ValueError("source manifest must contain a JSON object")
        return parsed

    def source_info(self, document_id: str, version_id: str) -> StoredSource:
        path = self._source_path(document_id, version_id)
        return StoredSource(
            logical_uri=(
                f"kendra://repository/documents/{document_id}/versions/{version_id}"
            ),
            byte_length=path.stat().st_size,
            media_type="application/pdf",
        )

    def verify_sha256(self, document_id: str, version_id: str, expected: str) -> bool:
        if not _SHA256.fullmatch(expected):
            raise ValueError(
                "expected checksum must be 64 lowercase hexadecimal characters"
            )
        digest = hashlib.sha256()
        with self.open_source(document_id, version_id) as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest() == expected

    async def check(self) -> ProbeResult:
        ready = self._root.is_dir() and os.access(self._root, os.R_OK | os.X_OK)
        return ProbeResult(
            self.name,
            ready,
            "available" if ready else "unavailable",
        )
