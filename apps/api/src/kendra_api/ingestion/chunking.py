"""Deterministic character-offset chunks that never cross a PDF page."""

import hashlib
import uuid

from kendra_api.ingestion.models import ChunkRecord, PageRecord


CHUNKER_VERSION = "page-char-v1"


class PageChunker:
    def __init__(self, size: int, overlap: int) -> None:
        if size <= 0 or overlap <= 0 or overlap >= size:
            raise ValueError("chunk size must be positive and overlap must be in (0, size)")
        self._size = size
        self._overlap = overlap

    def chunk(self, pages: list[PageRecord], source_sha256: str) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        for page in pages:
            if not page.text:
                continue
            start = 0
            sequence = 0
            while start < len(page.text):
                maximum_end = min(len(page.text), start + self._size)
                end = maximum_end
                if maximum_end < len(page.text):
                    boundary = page.text.rfind(" ", start + self._overlap + 1, maximum_end)
                    if boundary > start:
                        end = boundary + 1
                text = page.text[start:end]
                content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
                identity = (
                    f"{page.version_id}:{page.page_number}:{sequence}:{start}:{end}:"
                    f"{content_sha256}:{CHUNKER_VERSION}:{self._size}:{self._overlap}"
                )
                chunk_id = str(uuid.uuid5(uuid.NAMESPACE_URL, identity))
                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        version_id=page.version_id,
                        source_sha256=source_sha256,
                        processing_run_id=page.processing_run_id,
                        page_number=page.page_number,
                        sequence=sequence,
                        start_offset=start,
                        end_offset=end,
                        text=text,
                        extraction_method=page.extraction_method,
                        content_sha256=content_sha256,
                        chunker_version=(
                            f"{CHUNKER_VERSION};size={self._size};overlap={self._overlap}"
                        ),
                    )
                )
                if end == len(page.text):
                    break
                next_start = end - self._overlap
                if next_start <= start:
                    next_start = end
                start = next_start
                sequence += 1
        return chunks
