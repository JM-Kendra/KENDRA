"""Fail-closed PDF intake validation and safe naming."""

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import IntakeManifest, ValidatedPdf


_PDF_HEADER = re.compile(br"%PDF-(?:1\.[0-7]|2\.0)[\r\n]")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_FILENAME_CHARACTER = re.compile(r"[^A-Za-z0-9._-]+")
_DANGEROUS_ACTIONS = {"/JavaScript", "/Launch", "/GoToR", "/SubmitForm", "/ImportData"}


def safe_pdf_filename(original: str) -> str:
    """Return a display-safe basename; it is never used as storage identity."""
    if not original or Path(original).name != original or "\x00" in original:
        raise IngestionError("unsafe_filename", "filename must be a plain basename")
    normalized = unicodedata.normalize("NFKD", original).encode("ascii", "ignore").decode()
    stem = Path(normalized).stem
    stem = _SAFE_FILENAME_CHARACTER.sub("-", stem).strip("._-")[:96]
    if not stem:
        stem = "document"
    return f"{stem}.pdf"


def resolve_intake_path(intake_root: Path, submitted: str | Path) -> Path:
    """Resolve one operator-supplied path without permitting root escape."""
    root = intake_root.resolve(strict=True)
    candidate = Path(submitted)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except (FileNotFoundError, RuntimeError) as exc:
        raise IngestionError("missing_file", "intake PDF does not exist") from exc
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise IngestionError("path_traversal", "intake path escapes the configured root")
    return resolved


def load_intake_manifest(path: Path) -> IntakeManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IngestionError("invalid_manifest", "intake manifest is unreadable") from exc
    if not isinstance(payload, dict):
        raise IngestionError("invalid_manifest", "intake manifest must be an object")
    required = {
        "original_filename",
        "expected_sha256",
        "expected_page_count",
        "approval_scope",
        "provenance_reference",
        "approval_status",
    }
    if set(payload) != required:
        raise IngestionError("invalid_manifest", "intake manifest fields do not match")
    text_fields = required - {"expected_page_count"}
    if any(not isinstance(payload[field], str) for field in text_fields):
        raise IngestionError("invalid_manifest", "intake manifest field types are invalid")
    if (
        isinstance(payload["expected_page_count"], bool)
        or not isinstance(payload["expected_page_count"], int)
    ):
        raise IngestionError("invalid_manifest", "manifest page count is invalid")
    try:
        manifest = IntakeManifest(**payload)
    except TypeError as exc:
        raise IngestionError("invalid_manifest", "intake manifest fields are invalid") from exc
    if (
        manifest.approval_status != "approved"
        or not manifest.approval_scope.strip()
        or not manifest.provenance_reference.strip()
    ):
        raise IngestionError("unapproved_manifest", "manifest is not approved")
    if not _SHA256.fullmatch(manifest.expected_sha256):
        raise IngestionError("invalid_manifest", "manifest checksum is invalid")
    if manifest.expected_page_count <= 0:
        raise IngestionError("invalid_manifest", "manifest page count is invalid")
    safe_pdf_filename(manifest.original_filename)
    return manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _reject_active_content(reader: PdfReader) -> None:
    root: Any = reader.trailer["/Root"].get_object()
    if "/OpenAction" in root or "/AA" in root:
        raise IngestionError("unsupported_pdf", "PDF contains active catalog actions")
    names = root.get("/Names")
    if names is not None:
        names = names.get_object()
    if names and any(key in names for key in ("/JavaScript", "/EmbeddedFiles")):
        raise IngestionError("unsupported_pdf", "PDF contains embedded or active content")
    for page in reader.pages:
        if "/AA" in page:
            raise IngestionError("unsupported_pdf", "PDF contains active page actions")
        for annotation_ref in page.get("/Annots", []):
            annotation = annotation_ref.get_object()
            action = annotation.get("/A")
            if action is not None:
                action = action.get_object()
            if action and action.get("/S") in _DANGEROUS_ACTIONS:
                raise IngestionError("unsupported_pdf", "PDF contains an unsupported action")


def validate_pdf(path: Path, manifest: IntakeManifest, max_bytes: int, max_pages: int) -> ValidatedPdf:
    size = path.stat().st_size
    if size <= 0:
        raise IngestionError("empty_file", "PDF is empty")
    if size > max_bytes:
        raise IngestionError("size_limit", "PDF exceeds the configured byte limit")
    with path.open("rb") as source:
        header = source.read(9)
        source.seek(max(0, size - 2048))
        tail = source.read()
    if not _PDF_HEADER.match(header):
        raise IngestionError("invalid_file_type", "file does not start with a supported PDF header")
    eof = tail.rfind(b"%%EOF")
    if eof < 0 or tail[eof + 5 :].strip(b"\x00\t\n\f\r "):
        raise IngestionError("invalid_file_type", "PDF has no valid terminal EOF marker")
    checksum = _sha256(path)
    if checksum != manifest.expected_sha256:
        raise IngestionError("manifest_mismatch", "PDF checksum does not match the manifest")
    if path.name != manifest.original_filename:
        raise IngestionError("manifest_mismatch", "PDF filename does not match the manifest")
    try:
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted:
            raise IngestionError("unsupported_pdf", "encrypted PDFs are not supported")
        page_count = len(reader.pages)
        _reject_active_content(reader)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError("invalid_file_type", "PDF structure is unreadable") from exc
    if page_count <= 0 or page_count > max_pages:
        raise IngestionError("page_limit", "PDF page count is outside configured limits")
    if page_count != manifest.expected_page_count:
        raise IngestionError("manifest_mismatch", "PDF page count does not match the manifest")
    return ValidatedPdf(
        path=path,
        original_filename=manifest.original_filename,
        safe_filename=safe_pdf_filename(manifest.original_filename),
        sha256=checksum,
        byte_length=size,
        page_count=page_count,
    )
