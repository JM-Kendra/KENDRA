"""Contract for GET /api/v1/documents/{version_id}/content (MVP_SPEC 7.5).

Marked `milestone10` so the tracked backend baseline keeps its documented count.
This endpoint exists to make a Milestone 10 citation openable, and shares that
work's unaccepted status.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import httpx
import pytest

from kendra_api.answering.dependencies import get_source_registry
from kendra_api.answering.models import SourceRecord
from kendra_api.answering.sources import InMemorySourceRegistry
from kendra_api.config import Settings
from kendra_api.documents import get_document_store
from kendra_api.main import create_app
from kendra_api.storage.local import LocalDocumentStore

pytestmark = pytest.mark.milestone10

DOCUMENT_ID = "doc-content-1"
VERSION_ID = "ver-content-1"
FILENAME = "SYNTHETIC_FIXTURE.pdf"
# Synthetic bytes. No real document content appears in this file.
BODY = b"%PDF-1.7\n" + bytes(range(256)) * 8 + b"\n%%EOF\n"
DIGEST = hashlib.sha256(BODY).hexdigest()


@pytest.fixture
def wired(tmp_path: Path):
    source_dir = tmp_path / "objects" / DOCUMENT_ID / VERSION_ID
    source_dir.mkdir(parents=True)
    (source_dir / "source.pdf").write_bytes(BODY)

    app = create_app(
        Settings(_env_file=None, postgres_password="contract-test"),  # type: ignore[call-arg]
        probes=[],
    )
    registry = InMemorySourceRegistry(
        [
            SourceRecord(
                document_id=DOCUMENT_ID,
                version_id=VERSION_ID,
                filename=FILENAME,
                sha256=DIGEST,
                page_count=3,
            )
        ],
        active_generation_id="gen-active",
    )
    store = LocalDocumentStore(tmp_path)
    app.dependency_overrides[get_source_registry] = lambda: registry
    app.dependency_overrides[get_document_store] = lambda: store
    try:
        yield app, registry, store
    finally:
        app.dependency_overrides.clear()


def _client(app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    )


async def test_admitted_version_streams_exact_preserved_bytes(wired):
    app, _registry, _store = wired
    async with _client(app) as client:
        response = await client.get(f"/api/v1/documents/{VERSION_ID}/content")

    assert response.status_code == 200
    assert response.content == BODY, "streamed bytes differ from the preserved source"
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-length"] == str(len(BODY))
    assert FILENAME in response.headers["content-disposition"]


async def test_unknown_version_fails_closed_without_leaking_detail(wired):
    app, _registry, _store = wired
    async with _client(app) as client:
        response = await client.get("/api/v1/documents/ver-not-admitted/content")

    assert response.status_code == 404
    body = response.json()
    assert set(body) == {"error_code"}, "error body must carry a code and nothing else"
    assert FILENAME not in response.text


async def test_checksum_mismatch_streams_nothing(wired):
    """The registry and the stored bytes disagree: return no bytes at all."""
    app, _registry, _store = wired
    source = Path(_store._root) / "objects" / DOCUMENT_ID / VERSION_ID / "source.pdf"
    source.write_bytes(BODY + b"tampered")

    async with _client(app) as client:
        response = await client.get(f"/api/v1/documents/{VERSION_ID}/content")

    assert response.status_code == 503
    assert response.json()["error_code"] == "source_checksum_mismatch"
    assert b"tampered" not in response.content


async def test_range_request_returns_partial_content(wired):
    app, _registry, _store = wired
    async with _client(app) as client:
        response = await client.get(
            f"/api/v1/documents/{VERSION_ID}/content", headers={"Range": "bytes=0-9"}
        )

    assert response.status_code == 206
    assert response.content == BODY[:10]
    assert response.headers["content-range"] == f"bytes 0-9/{len(BODY)}"


async def test_open_ended_and_suffix_ranges_resolve(wired):
    app, _registry, _store = wired
    total = len(BODY)
    async with _client(app) as client:
        open_ended = await client.get(
            f"/api/v1/documents/{VERSION_ID}/content", headers={"Range": "bytes=10-"}
        )
        suffix = await client.get(
            f"/api/v1/documents/{VERSION_ID}/content", headers={"Range": "bytes=-16"}
        )

    assert open_ended.status_code == 206
    assert open_ended.content == BODY[10:]
    assert suffix.status_code == 206
    assert suffix.content == BODY[-16:]
    assert suffix.headers["content-range"] == f"bytes {total - 16}-{total - 1}/{total}"


async def test_unsatisfiable_range_is_rejected(wired):
    app, _registry, _store = wired
    async with _client(app) as client:
        response = await client.get(
            f"/api/v1/documents/{VERSION_ID}/content",
            headers={"Range": f"bytes={len(BODY) + 10}-"},
        )

    assert response.status_code == 416


@pytest.mark.parametrize(
    "hostile",
    ["../../etc/passwd", "..%2f..%2fetc%2fpasswd", "ver-1/../../../secret"],
    ids=["traversal", "encoded-traversal", "nested-traversal"],
)
async def test_caller_cannot_address_bytes_outside_the_store(wired, hostile):
    """The caller supplies an opaque id, never a location."""
    app, _registry, _store = wired
    async with _client(app) as client:
        response = await client.get(f"/api/v1/documents/{hostile}/content")

    assert response.status_code in (404, 422), response.status_code
    assert b"root:" not in response.content


async def test_a_version_the_registry_does_not_resolve_is_never_served(wired):
    """Bytes present on disk are not sufficient; admission is what authorizes."""
    app, _registry, store = wired
    orphan_dir = Path(store._root) / "objects" / "doc-orphan" / "ver-orphan"
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "source.pdf").write_bytes(b"%PDF-1.7\norphaned\n%%EOF\n")

    async with _client(app) as client:
        response = await client.get("/api/v1/documents/ver-orphan/content")

    assert response.status_code == 404
    assert b"orphaned" not in response.content
