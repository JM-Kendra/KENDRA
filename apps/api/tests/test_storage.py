import hashlib
import json
from pathlib import Path

import pytest

from kendra_api.storage.base import DocumentStore
from kendra_api.storage.local import LocalDocumentStore


def _write_version(root: Path, content: bytes) -> None:
    source = root / "objects" / "doc-1" / "version-1" / "source.pdf"
    manifest = root / "manifests" / "doc-1" / "version-1.json"
    source.parent.mkdir(parents=True)
    manifest.parent.mkdir(parents=True)
    source.write_bytes(content)
    manifest.write_text(json.dumps({"document_id": "doc-1"}), encoding="utf-8")


def test_local_root_can_be_replaced_without_changing_store_calls(tmp_path: Path) -> None:
    first_root = tmp_path / "local"
    second_root = tmp_path / "nas-mount"
    _write_version(first_root, b"first-source")
    _write_version(second_root, b"second-source")

    stores: list[DocumentStore] = [
        LocalDocumentStore(first_root),
        LocalDocumentStore(second_root),
    ]

    assert [
        store.read_source_range("doc-1", "version-1", 0, 6) for store in stores
    ] == [b"first-", b"second"]
    assert stores[0].source_info("doc-1", "version-1").logical_uri == stores[
        1
    ].source_info("doc-1", "version-1").logical_uri


def test_local_store_reads_manifest_and_verifies_checksum(tmp_path: Path) -> None:
    content = b"synthetic-pdf-bytes"
    _write_version(tmp_path, content)
    store = LocalDocumentStore(tmp_path)

    assert store.read_manifest("doc-1", "version-1") == {"document_id": "doc-1"}
    assert store.verify_sha256(
        "doc-1", "version-1", hashlib.sha256(content).hexdigest()
    )


def test_local_store_rejects_caller_paths(tmp_path: Path) -> None:
    store = LocalDocumentStore(tmp_path)

    with pytest.raises(ValueError, match="invalid document_id"):
        store.open_source("../outside", "version-1")
