"""ADR-007 Section 6 regression coverage for ``native-primary-detection-v1``.

Written before implementation, so the contract is defined by the record rather than by
whatever gets built. Fails at import until the policy exists.

Expected implementation surface (ADR-007 Sections 2.1-2.3):

    document_material_tokens(pages: Iterable[str]) -> set[str]
        Distinct digit-bearing tokens across every page of a document, using the ADR-004
        tokenizer unchanged.

    NativePrimaryDetectionPipeline(detector, native, ocr, minimum_chars)
        policy_version == "native-primary-detection-v1". Note the constructor takes no
        agreement threshold: ADR-007 Section 2.3 removes
        KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT, which gated a Docling retention
        path this policy does not have.

Retention (Section 2.1): native above ``minimum_chars``, Tesseract below it, Docling
never. Detection (Section 2.2): document-scope material-token containment only. Per-page
comparison is unsound under Section 1.1 and must not be performed. A Docling material
token absent from the whole retained representation fails the document closed with
``extraction_completeness_conflict``.
"""

import hashlib
from pathlib import Path

import pytest

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.extraction import (
    NativePrimaryDetectionPipeline as Pipeline,
)
from kendra_api.ingestion.extraction import document_material_tokens
from kendra_api.ingestion.models import ExtractionMethod
from pdf_fixtures import make_digital_pdf, make_scanned_pdf

UNUSED = Path("unused.pdf")

PROSE = (
    "Bureau of Internal Revenue procurement monitoring report ongoing activities "
    "project title contractor allotted budget contract cost status remarks"
)


class StaticPages:
    """Stands in for the Docling detector. Never contributes retained text."""

    def __init__(self, pages: list[str], version: str = "test-docling") -> None:
        self.pages = pages
        self.version = version
        self.calls = 0

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        assert page_count == len(self.pages)
        self.calls += 1
        return list(self.pages)


class StaticNative:
    def __init__(self, pages: list[str], version: str = "test-native") -> None:
        self.pages = pages
        self.version = version

    def extract_page(self, path: Path, page_number: int) -> str:
        return self.pages[page_number - 1]


class StaticOcr:
    def __init__(self, pages: list[str], version: str = "test-tesseract") -> None:
        self.pages = pages
        self.version = version

    def extract_page(self, path: Path, page_number: int) -> str:
        return self.pages[page_number - 1]


class NeverOcr:
    version = "never-ocr"

    def extract_page(self, path: Path, page_number: int) -> str:
        raise AssertionError("OCR must not run when the native layer meets the floor")


def build(
    detector: list[str],
    native: list[str],
    ocr: list[str] | None = None,
    *,
    minimum_chars: int = 20,
) -> Pipeline:
    return Pipeline(
        StaticPages(detector),
        StaticNative(native),
        StaticOcr(ocr) if ocr is not None else NeverOcr(),
        minimum_chars,
    )


# --- Section 2.1: Docling is not in the retention path -------------------------------


def test_no_page_is_ever_retained_from_the_detector() -> None:
    """Even where the detector is richer than native, it contributes no retained text."""
    marker = "DOCLING-ONLY-LAYOUT-ARTIFACT"
    detector = [f"{PROSE} {marker} 1,000.00"]
    native = [f"{PROSE} 1,000.00"]

    pages = build(detector, native).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.PDF_TEXT
    assert marker not in pages[0].text


def test_retained_methods_never_include_docling() -> None:
    detector = [f"{PROSE} page {n} 1,000.00" for n in range(1, 4)]
    native = [detector[0], detector[1], ""]
    ocr = ["", "", f"{PROSE} page 3 1,000.00"]

    pages = build(detector, native, ocr).extract(UNUSED, "ver", "run", 3)

    assert [page.extraction_method for page in pages] == [
        ExtractionMethod.PDF_TEXT,
        ExtractionMethod.PDF_TEXT,
        ExtractionMethod.TESSERACT,
    ]
    assert all("method:docling" not in page.source_pointer for page in pages)


def test_character_floor_selects_native_above_and_tesseract_below() -> None:
    detector = [PROSE, PROSE]
    native = [PROSE, "7"]
    ocr = ["", f"{PROSE} recovered"]

    pages = build(detector, native, ocr, minimum_chars=20).extract(UNUSED, "ver", "run", 2)

    assert pages[0].extraction_method is ExtractionMethod.PDF_TEXT
    assert pages[1].extraction_method is ExtractionMethod.TESSERACT


def test_retained_text_is_the_unmodified_native_candidate() -> None:
    native_text = f"  {PROSE}   1,000.00  spacing preserved  "

    pages = build([PROSE], [native_text]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].text == native_text


# --- Section 2.2: detection is document-scope, never per-page ------------------------


def test_document_material_tokens_span_every_page() -> None:
    tokens = document_material_tokens(["alpha 111.00", "bravo 222.00", "charlie"])

    assert tokens == {"11100", "22200"}


def test_detector_token_absent_from_the_whole_document_fails_closed() -> None:
    detector = [f"{PROSE} 111,111.00", f"{PROSE} 999,999.00"]
    native = [f"{PROSE} 111,111.00", f"{PROSE}"]

    with pytest.raises(IngestionError) as failure:
        build(detector, native).extract(UNUSED, "ver", "run", 2)

    assert failure.value.code == "extraction_completeness_conflict"


def test_boundary_attribution_produces_no_conflict() -> None:
    """The RR 11-2024 shape: the detector carries page 2's opening onto page 1.

    Native places the token on page 2, where the paper puts it. At document scope the
    token is present, so there is no conflict and no retention change. A per-page
    comparison would reject this page, which is the ADR-005 failure.
    """
    detector = [
        f"{PROSE} and there is no missing information under section 3 d 3 of rr no 7,2024",
        f"{PROSE} effective april 27 2024",
    ]
    native = [
        f"{PROSE} and there is no",
        f"missing information under section 3 d 3 of rr no 7,2024 effective april 27 2024 {PROSE}",
    ]

    pages = build(detector, native).extract(UNUSED, "ver", "run", 2)

    assert [page.extraction_method for page in pages] == [
        ExtractionMethod.PDF_TEXT,
        ExtractionMethod.PDF_TEXT,
    ]
    assert "missing information" in pages[1].text
    assert "missing information" not in pages[0].text


def test_detector_page_attribution_is_never_recorded() -> None:
    detector = ["", f"{PROSE} 111,111.00"]
    native = [f"{PROSE} 111,111.00", PROSE]

    pages = build(detector, native).extract(UNUSED, "ver", "run", 2)

    assert pages[0].source_pointer == "pdf-page:1;block:whole-page;method:pdf_text"
    assert pages[1].source_pointer == "pdf-page:2;block:whole-page;method:pdf_text"


def test_surplus_occurrence_counts_carry_no_decision_weight() -> None:
    detector = [f"{PROSE} 1,850,000.00 1,850,000.00 1,850,000.00"]
    native = [f"{PROSE} 1,850,000.00"]

    pages = build(detector, native).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.PDF_TEXT


def test_tesseract_pages_count_toward_the_retained_representation() -> None:
    """A token the detector sees may be satisfied by an OCR-retained page."""
    detector = [f"{PROSE} 111,111.00", f"{PROSE} 222,222.00"]
    native = [f"{PROSE} 111,111.00", "7"]
    ocr = ["", f"{PROSE} 222,222.00"]

    pages = build(detector, native, ocr).extract(UNUSED, "ver", "run", 2)

    assert pages[1].extraction_method is ExtractionMethod.TESSERACT


def test_conflict_error_and_logs_contain_no_extracted_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    marker = "NEVER-LOG-EXTRACTED-CONTENT"
    detector = [f"{marker} {PROSE} 999,999.00"]
    native = [f"{marker} {PROSE}"]

    with pytest.raises(IngestionError) as failure:
        build(detector, native).extract(UNUSED, "ver", "run", 1)

    assert marker not in str(failure.value)
    assert marker not in caplog.text


# --- Section 6: page identity, determinism, immutability -----------------------------


def test_page_15_totals_are_retained_with_page_15_provenance() -> None:
    detector = [f"{PROSE} physical page {n} 2,730,755.00" for n in range(1, 16)]
    native = list(detector)
    native[14] += " total allotted budget 175,284,574.00 169,021,829.87"

    pages = build(detector, native).extract(UNUSED, "ver", "run", 15)

    page_15 = pages[14]
    assert "175,284,574.00" in page_15.text
    assert "169,021,829.87" in page_15.text
    assert page_15.source_pointer == "pdf-page:15;block:whole-page;method:pdf_text"


def test_physical_pages_remain_contiguous_and_one_based() -> None:
    pages_text = [f"{PROSE} page {n} 1,000.00" for n in range(1, 6)]

    pages = build(pages_text, list(pages_text)).extract(UNUSED, "ver", "run", 5)

    assert [page.page_number for page in pages] == [1, 2, 3, 4, 5]
    assert [page.source_pointer.split(";", 1)[0] for page in pages] == [
        f"pdf-page:{n}" for n in range(1, 6)
    ]


def test_repeated_extraction_is_deterministic() -> None:
    detector = [f"{PROSE} 2,730,755.00"]
    native = [f"{PROSE} 2,730,755.00 175,284,574.00"]
    pipeline = build(detector, native)

    assert pipeline.extract(UNUSED, "ver", "run", 1) == pipeline.extract(
        UNUSED, "ver", "run", 1
    )


def test_twelve_page_scanned_circular_stays_on_the_ocr_path(tmp_path: Path) -> None:
    pdf = make_scanned_pdf(tmp_path / "twelve.pdf", "SCANNED CIRCULAR", page_count=12)
    ocr = [f"{PROSE} scanned physical page {n}" for n in range(1, 13)]

    pages = build([""] * 12, [""] * 12, ocr).extract(pdf, "ver", "run", 12)

    assert [page.page_number for page in pages] == list(range(1, 13))
    assert all(page.extraction_method is ExtractionMethod.TESSERACT for page in pages)
    assert all(page.source_pointer.endswith("method:tesseract") for page in pages)


def test_policy_does_not_modify_the_original_bytes(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "immutable.pdf", ["Immutable source 175,284,574.00"])
    before = hashlib.sha256(pdf.read_bytes()).hexdigest()

    build([PROSE], [f"{PROSE} 175,284,574.00"]).extract(pdf, "ver", "run", 1)

    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == before


# --- Section 2.3: policy identity and the removed threshold --------------------------


def test_policy_version_and_tool_identity() -> None:
    pipeline = build([PROSE], [PROSE])

    assert Pipeline.policy_version == "native-primary-detection-v1"
    assert pipeline.tool_identity.startswith("policy=native-primary-detection-v1;")
    assert "minimum_candidate_agreement" not in pipeline.tool_identity
