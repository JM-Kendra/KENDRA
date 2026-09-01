"""Preserved-source access (MVP_SPEC Section 7.5).

`GET /api/v1/documents/{version_id}/content` streams the admitted PDF that a
citation points at. Three properties make this safe to expose:

1. The caller supplies an opaque `version_id` and nothing else. There is no path
   parameter, no filename, and no root override, so a caller cannot address bytes
   the store did not admit.
2. The document identity is resolved server-side through the registry. The
   caller's id is looked up, never trusted as a location.
3. The bytes are checksum-verified against the admitted value before any are
   returned. A mismatch fails closed with no partial stream.

Range requests are supported because a citation's whole purpose is to open one
page of a possibly large PDF in a viewer, and viewers fetch by range.
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from kendra_api.answering.dependencies import get_source_registry
from kendra_api.answering.sources import SourceRegistry
from kendra_api.storage.base import DocumentStore
from kendra_api.storage.local import LocalDocumentStore

router = APIRouter(tags=["documents"])

_STREAM_CHUNK = 64 * 1024
_RANGE = re.compile(r"^bytes=(\d*)-(\d*)$")


def get_document_store(request: Request) -> DocumentStore:
    store = getattr(request.app.state, "document_store", None)
    if store is not None:
        return store
    return LocalDocumentStore(request.app.state.document_store_root)


def _failed(code: str, http_status: int) -> JSONResponse:
    # Content-free by repository rule: a code, never source or query content.
    return JSONResponse(status_code=http_status, content={"error_code": code})


@router.get("/api/v1/documents/{version_id}/content")
async def get_document_content(
    request: Request,
    version_id: Annotated[str, Path(min_length=1, max_length=128)],
    range_header: Annotated[str | None, Header(alias="Range")] = None,
    registry: SourceRegistry = Depends(get_source_registry),
    store: DocumentStore = Depends(get_document_store),
) -> Response:
    record = await registry.resolve(version_id)
    if record is None:
        # Not admitted, not ready, or not a known version. Indistinguishable on
        # purpose: the response must not confirm which.
        return _failed("source_not_found", 404)

    try:
        info = store.source_info(record.document_id, record.version_id)
        checksum_ok = store.verify_sha256(
            record.document_id, record.version_id, record.sha256
        )
    except (ValueError, OSError):
        return _failed("source_unavailable", 503)

    if not checksum_ok:
        # The registry and the bytes disagree. Never stream either one.
        return _failed("source_checksum_mismatch", 503)

    total = info.byte_length
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'inline; filename="{record.filename}"',
        "X-Content-Type-Options": "nosniff",
    }

    if range_header:
        parsed = _RANGE.match(range_header.strip())
        if parsed is None:
            return _failed("invalid_range", 416)
        raw_start, raw_end = parsed.groups()
        if raw_start == "" and raw_end == "":
            return _failed("invalid_range", 416)
        if raw_start == "":  # suffix range: last N bytes
            length = min(int(raw_end), total)
            start = total - length
            end = total - 1
        else:
            start = int(raw_start)
            end = int(raw_end) if raw_end else total - 1
            end = min(end, total - 1)
        if start > end or start >= total:
            return Response(
                status_code=416, headers={"Content-Range": f"bytes */{total}"}
            )
        try:
            payload = store.read_source_range(
                record.document_id, record.version_id, start, end - start + 1
            )
        except (ValueError, OSError):
            return _failed("source_unavailable", 503)
        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        return Response(
            content=payload,
            status_code=206,
            media_type=info.media_type,
            headers=headers,
        )

    def _stream():
        with store.open_source(record.document_id, record.version_id) as source:
            while True:
                block = source.read(_STREAM_CHUNK)
                if not block:
                    break
                yield block

    headers["Content-Length"] = str(total)
    return StreamingResponse(_stream(), media_type=info.media_type, headers=headers)
