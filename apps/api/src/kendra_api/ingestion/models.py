"""Immutable ingestion records shared across adapters."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ProcessingState(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class ExtractionMethod(StrEnum):
    DOCLING = "docling"
    TESSERACT = "tesseract"
    VERIFIED_BLANK = "verified_blank"


@dataclass(frozen=True, slots=True)
class IntakeManifest:
    original_filename: str
    expected_sha256: str
    expected_page_count: int
    approval_scope: str
    provenance_reference: str
    approval_status: str = "approved"


@dataclass(frozen=True, slots=True)
class ValidatedPdf:
    path: Path
    original_filename: str
    safe_filename: str
    sha256: str
    byte_length: int
    page_count: int
    media_type: str = "application/pdf"


@dataclass(frozen=True, slots=True)
class DocumentIdentity:
    ingestion_id: str
    document_id: str
    version_id: str
    processing_run_id: str
    generation_id: str


@dataclass(frozen=True, slots=True)
class ExistingVersion:
    document_id: str
    version_id: str
    sha256: str
    state: ProcessingState


@dataclass(frozen=True, slots=True)
class PageRecord:
    version_id: str
    processing_run_id: str
    page_number: int
    text: str
    extraction_method: ExtractionMethod
    quality_result: str
    docling_text_chars: int


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    chunk_id: str
    version_id: str
    source_sha256: str
    processing_run_id: str
    page_number: int
    sequence: int
    start_offset: int
    end_offset: int
    text: str
    extraction_method: ExtractionMethod
    content_sha256: str
    chunker_version: str


@dataclass(frozen=True, slots=True)
class StoredVersion:
    logical_uri: str
    manifest_uri: str


@dataclass(frozen=True, slots=True)
class IngestionResult:
    ingestion_id: str
    document_id: str
    version_id: str
    sha256: str
    state: ProcessingState
    duplicate: bool
    page_count: int
    chunk_count: int
    generation_id: str | None
