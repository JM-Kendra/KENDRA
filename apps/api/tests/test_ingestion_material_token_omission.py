"""ADR-005 Section 7 regression coverage for ``material-token-omission-v1``.

These tests were written **before** the bounded conflict-taxonomy diagnostic was run, so
that their content could not be shaped by its result. They target a policy that does not
yet exist and therefore fail at import until ADR-005 is accepted under its Section 3
activation condition and implemented.

If ADR-005 is closed as rejected, delete this file rather than relaxing it.

Expected implementation surface (ADR-005 Sections 4.4-4.10):

    material_tokens(text) -> set[str]
        Distinct digit-bearing tokens, using the ADR-004 tokenizer unchanged.

    distinct_token_coverage(candidate_text, other_text) -> float
        |distinct(candidate) & distinct(other)| / |distinct(other)|; 1.0 when other is
        empty.

    MaterialTokenOmissionPipeline
        policy_version == "material-token-omission-v1"; constructor and extract()
        signatures identical to PageExtractionPipeline.

Retainability (Section 4.7): a candidate is retainable only if its material token set
contains the union of the material token sets of every usable candidate observed for that
page, and its distinct-token set covers at least ``minimum_candidate_agreement`` of each
other usable candidate's distinct tokens. Preference order is Docling, native, Tesseract
(Section 4.8). No retainable candidate means a content-free ``extraction_conflict``
(Section 4.10). Candidates are never merged.
"""

import hashlib
from pathlib import Path

import pytest

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.extraction import (
    PageExtractionPipeline,
    distinct_token_coverage,
    material_tokens,
)
from kendra_api.ingestion.extraction import (
    MaterialTokenOmissionPipeline as Pipeline,
)
from kendra_api.ingestion.models import ExtractionMethod
from pdf_fixtures import make_digital_pdf, make_scanned_pdf

UNUSED = Path("unused.pdf")

# Shared prose so distinct-token coverage stays above the 0.90 floor unless a test is
# deliberately exercising that floor.
PROSE = (
    "Bureau of Internal Revenue procurement monitoring report ongoing activities "
    "project title contractor allotted budget contract cost status remarks"
)


class StaticPages:
    def __init__(self, pages: list[str], version: str = "test-docling") -> None:
        self.pages = pages
        self.version = version

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        assert page_count == len(self.pages)
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
        raise AssertionError("OCR must not run when a native text layer is usable")


def build(
    docling: list[str],
    native: list[str],
    ocr: list[str] | None = None,
    *,
    minimum_chars: int = 20,
    agreement: float = 0.90,
) -> Pipeline:
    return Pipeline(
        StaticPages(docling),
        StaticNative(native),
        StaticOcr(ocr) if ocr is not None else NeverOcr(),
        minimum_chars,
        agreement,
    )


# --- Section 4.4-4.5: helpers operate on distinct sets, not occurrence counts ---------


def test_material_tokens_are_distinct_and_digit_bearing() -> None:
    tokens = material_tokens("Total 2,730,755.00 2,730,755.00 alpha bravo 2024-001")

    assert tokens == {"2730755.00", "2024-001"}


def test_distinct_token_coverage_ignores_repetition() -> None:
    repeated = "alpha bravo alpha bravo alpha bravo"

    assert distinct_token_coverage(repeated, "alpha bravo") == 1.0
    assert distinct_token_coverage("alpha", "alpha bravo") == pytest.approx(0.5)


# --- Section 5: the ADR-004 failure mode is gone -------------------------------------


def test_surplus_copies_of_a_shared_material_token_no_longer_fail() -> None:
    """A candidate holding extra copies of a value both observers saw is not a conflict.

    This is the exact shape that rejected all three documents under ADR-004: TableFormer
    span replication produced surplus occurrences, and multiset subtraction scored them
    identically to a genuinely absent value.
    """
    docling = f"{PROSE} 175,284,574.00 175,284,574.00 175,284,574.00 169,021,829.87"
    native = f"{PROSE} 175,284,574.00 169,021,829.87"

    pages = build([docling], [native]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.DOCLING
    assert pages[0].source_pointer == "pdf-page:1;block:whole-page;method:docling"


# --- Section 7: page-15 retention with provenance ------------------------------------


def test_docling_omitting_a_material_token_yields_the_native_page() -> None:
    docling_pages = [f"{PROSE} physical page {number} 2,730,755.00" for number in range(1, 16)]
    native_pages = list(docling_pages)
    native_pages[14] += (
        " Total Allotted Budget of On-going Procurement Activities "
        "175,284,574.00 169,021,829.87"
    )

    pages = build(docling_pages, native_pages).extract(UNUSED, "ver", "run", 15)

    page_15 = pages[14]
    assert page_15.extraction_method is ExtractionMethod.PDF_TEXT
    assert "175,284,574.00" in page_15.text
    assert "169,021,829.87" in page_15.text
    assert page_15.source_pointer == "pdf-page:15;block:whole-page;method:pdf_text"


def test_page_15_totals_are_not_reachable_by_merging_candidates() -> None:
    """The retained block is one whole candidate. Docling-only content must not survive."""
    marker = "DOCLING-ONLY-LAYOUT-ARTIFACT"
    docling = f"{PROSE} {marker} 2,730,755.00"
    native = f"{PROSE} 2,730,755.00 175,284,574.00 169,021,829.87"

    pages = build([docling], [native]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.PDF_TEXT
    assert marker not in pages[0].text


# --- Section 4.10: fail closed on genuine disagreement -------------------------------


def test_mutual_material_omission_fails_closed() -> None:
    """Each candidate holds a material token the other lacks. Neither covers the union."""
    docling = f"{PROSE} 111,111.00"
    native = f"{PROSE} 222,222.00"

    with pytest.raises(IngestionError) as failure:
        build([docling], [native]).extract(UNUSED, "ver", "run", 1)

    assert failure.value.code == "extraction_conflict"


def test_distinct_token_coverage_floor_still_rejects_fragment_candidates() -> None:
    """A native fragment carrying a new material token is still not retainable.

    Docling fails the union test; native satisfies it but covers far too little of
    Docling's distinct vocabulary to be an acceptable whole-page representation. This is
    the RMC 03-2024 shape and it must keep failing.
    """
    docling = f"{PROSE} 111,111.00"
    native = "111,111.00 222,222.00"

    with pytest.raises(IngestionError) as failure:
        build([docling], [native]).extract(UNUSED, "ver", "run", 1)

    assert failure.value.code == "extraction_conflict"


def test_conflict_error_and_logs_contain_no_extracted_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    marker = "NEVER-LOG-EXTRACTED-CONTENT"
    docling = f"{marker} {PROSE} 111,111.00"
    native = f"{marker} {PROSE} 222,222.00"

    with pytest.raises(IngestionError) as failure:
        build([docling], [native]).extract(UNUSED, "ver", "run", 1)

    assert marker not in str(failure.value)
    assert marker not in caplog.text


# --- Section 4.7-4.9: three-candidate union and preference ---------------------------


def test_union_includes_the_ocr_candidate_when_native_is_unusable() -> None:
    docling = f"{PROSE} 111,111.00"
    ocr = f"{PROSE} 111,111.00 222,222.00"

    pages = build([docling], [""], [ocr]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.TESSERACT
    assert "222,222.00" in pages[0].text


def test_ocr_missing_a_docling_material_token_fails_closed() -> None:
    docling = f"{PROSE} 111,111.00"
    ocr = f"{PROSE} 222,222.00"

    with pytest.raises(IngestionError) as failure:
        build([docling], [""], [ocr]).extract(UNUSED, "ver", "run", 1)

    assert failure.value.code == "extraction_conflict"


def test_unusable_native_contributes_nothing_to_the_union() -> None:
    """An unusable native layer is not an observation and cannot create a conflict."""
    docling = f"{PROSE} 111,111.00"

    pages = build([docling], ["7"], [f"{PROSE} 111,111.00"]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.TESSERACT


def test_docling_is_preferred_when_both_candidates_are_retainable() -> None:
    shared = f"{PROSE} 175,284,574.00 169,021,829.87"

    pages = build([shared], [shared]).extract(UNUSED, "ver", "run", 1)

    assert pages[0].extraction_method is ExtractionMethod.DOCLING


# --- Section 7: page identity, determinism, OCR stratum, immutability ----------------


def test_physical_pages_remain_contiguous_and_one_based() -> None:
    docling = [f"{PROSE} page {number} 1,000.00" for number in range(1, 6)]

    pages = build(docling, list(docling)).extract(UNUSED, "ver", "run", 5)

    assert [page.page_number for page in pages] == [1, 2, 3, 4, 5]
    assert [page.source_pointer.split(";", 1)[0] for page in pages] == [
        f"pdf-page:{number}" for number in range(1, 6)
    ]


def test_repeated_extraction_is_deterministic() -> None:
    docling = f"{PROSE} 2,730,755.00"
    native = f"{docling} 175,284,574.00 169,021,829.87"
    pipeline = build([docling], [native])

    assert pipeline.extract(UNUSED, "ver", "run", 1) == pipeline.extract(
        UNUSED, "ver", "run", 1
    )


def test_twelve_page_scanned_circular_stays_on_the_ocr_path(tmp_path: Path) -> None:
    pdf = make_scanned_pdf(tmp_path / "twelve-page-scan.pdf", "SCANNED CIRCULAR", page_count=12)
    ocr = [f"{PROSE} scanned physical page {number}" for number in range(1, 13)]

    pages = build([""] * 12, [""] * 12, ocr).extract(pdf, "ver", "run", 12)

    assert [page.page_number for page in pages] == list(range(1, 13))
    assert all(page.extraction_method is ExtractionMethod.TESSERACT for page in pages)
    assert all(page.source_pointer.endswith("method:tesseract") for page in pages)


def test_policy_does_not_modify_the_original_bytes(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "immutable.pdf", ["Immutable source text 175,284,574.00"])
    before = hashlib.sha256(pdf.read_bytes()).hexdigest()
    docling = f"{PROSE} 175,284,574.00"

    build([docling], [docling]).extract(pdf, "ver", "run", 1)

    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == before


# --- Section 4.2: ADR-004 containment stays selectable -------------------------------


def test_policy_versions_are_distinct_and_containment_remains_available() -> None:
    assert Pipeline.policy_version == "material-token-omission-v1"
    assert PageExtractionPipeline.policy_version == "native-page-token-coverage-v1"


def test_tool_identity_records_the_active_policy() -> None:
    identity = build([PROSE], [PROSE]).tool_identity

    assert identity.startswith("policy=material-token-omission-v1;")
    assert "minimum_candidate_agreement=0.90" in identity
