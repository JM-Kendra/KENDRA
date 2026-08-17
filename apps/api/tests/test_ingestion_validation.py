import json
from pathlib import Path

import pytest

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import DocumentIdentity
from kendra_api.ingestion.storage import LocalDocumentAdmissionStore
from kendra_api.ingestion.validation import (
    load_intake_manifest,
    resolve_intake_path,
    safe_pdf_filename,
    validate_pdf,
)
from pdf_fixtures import make_digital_pdf, manifest_for, sha256


def _identity() -> DocumentIdentity:
    return DocumentIdentity("ing-1", "doc-1", "ver-1", "run-1", "gen-1")


def test_intake_path_rejects_traversal_and_symlink_escape(tmp_path: Path) -> None:
    intake = tmp_path / "intake"
    intake.mkdir()
    outside = make_digital_pdf(tmp_path / "outside.pdf", ["outside test text"])
    (intake / "escape.pdf").symlink_to(outside)

    with pytest.raises(IngestionError, match="escapes"):
        resolve_intake_path(intake, "../outside.pdf")
    with pytest.raises(IngestionError, match="escapes"):
        resolve_intake_path(intake, "escape.pdf")


def test_safe_filename_does_not_preserve_path_components() -> None:
    assert safe_pdf_filename("Policy (Final) 2026.pdf") == "Policy-Final-2026.pdf"
    with pytest.raises(IngestionError, match="basename"):
        safe_pdf_filename("../../source.pdf")


def test_rejects_non_pdf_and_oversized_pdf(tmp_path: Path) -> None:
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"not a pdf")
    fake_manifest = manifest_for(fake, 1)
    with pytest.raises(IngestionError) as invalid:
        validate_pdf(fake, fake_manifest, 1024, 10)
    assert invalid.value.code == "invalid_file_type"

    pdf = make_digital_pdf(tmp_path / "large.pdf", ["bounded content"])
    with pytest.raises(IngestionError) as oversized:
        validate_pdf(pdf, manifest_for(pdf, 1), pdf.stat().st_size - 1, 10)
    assert oversized.value.code == "size_limit"


def test_checksum_is_stable_for_identical_bytes(tmp_path: Path) -> None:
    first = make_digital_pdf(tmp_path / "first.pdf", ["stable checksum content"])
    second = tmp_path / "second.pdf"
    second.write_bytes(first.read_bytes())

    first_validated = validate_pdf(first, manifest_for(first, 1), 1_000_000, 10)
    second_validated = validate_pdf(second, manifest_for(second, 1), 1_000_000, 10)

    assert first_validated.sha256 == second_validated.sha256 == sha256(first)


def test_admission_preserves_original_bytes_and_rejects_internal_traversal(
    tmp_path: Path,
) -> None:
    pdf = make_digital_pdf(tmp_path / "Original Name.pdf", ["immutable original"])
    intake = manifest_for(pdf, 1)
    validated = validate_pdf(pdf, intake, 1_000_000, 10)
    original_bytes = pdf.read_bytes()
    store = LocalDocumentAdmissionStore(tmp_path / "repository")

    stored = store.admit(validated, intake, _identity(), "test-revision")
    admitted = store.source_path("doc-1", "ver-1")

    assert admitted.read_bytes() == original_bytes
    assert store.verify_sha256("doc-1", "ver-1", sha256(pdf))
    assert stored.logical_uri.startswith("kendra://repository/")
    assert store.read_manifest("doc-1", "ver-1")["original_filename"] == pdf.name
    pdf.write_bytes(b"changed intake after admission")
    assert admitted.read_bytes() == original_bytes
    with pytest.raises(ValueError, match="invalid document_id"):
        store.source_path("../outside", "ver-1")


def test_manifest_loader_requires_exact_approved_schema(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "original_filename": "test.pdf",
                "expected_sha256": "0" * 64,
                "expected_page_count": 1,
                "approval_scope": "synthetic",
                "provenance_reference": "pytest",
                "approval_status": "approved",
            }
        ),
        encoding="utf-8",
    )
    assert load_intake_manifest(path).approval_status == "approved"

    malformed = json.loads(path.read_text(encoding="utf-8"))
    malformed["approval_scope"] = 7
    path.write_text(json.dumps(malformed), encoding="utf-8")
    with pytest.raises(IngestionError) as invalid:
        load_intake_manifest(path)
    assert invalid.value.code == "invalid_manifest"
