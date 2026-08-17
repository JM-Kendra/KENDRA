import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest
from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument
from docling.datamodel.pipeline_options import TableStructureV2Options

from kendra_api.ingestion.chunking import PageChunker
from kendra_api.ingestion.extraction import (
    DoclingPageTextExtractor,
    PageExtractionPipeline,
    PopplerPageTextExtractor,
    TesseractPageOcr,
    compare_extractions,
)
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import ExtractionMethod, PageRecord
from pdf_fixtures import make_digital_pdf, make_scanned_pdf


def test_docling_model_loader_cli_imports_with_runtime_dependencies() -> None:
    completed = subprocess.run(
        ["docling-tools", "models", "download", "--help"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0, completed.stderr


def test_docling_converter_uses_staged_tableformer_v2_without_internal_ocr() -> None:
    converter = DoclingPageTextExtractor()._default_converter()
    pipeline_options = converter.format_to_options[InputFormat.PDF].pipeline_options

    assert pipeline_options.do_ocr is False
    assert isinstance(
        pipeline_options.table_structure_options, TableStructureV2Options
    )


class DoclingParserTestExtractor:
    """Exercise Docling's actual local PDF parser without downloading ML weights."""

    version = "test-docling-parse"

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        document = InputDocument(
            path_or_stream=path,
            format=InputFormat.PDF,
            backend=DoclingParseDocumentBackend,
            filename=path.name,
        )
        assert document.valid and document.page_count == page_count
        backend = document._backend
        assert backend is not None
        texts: list[str] = []
        try:
            for page in backend.iter_pages():
                try:
                    texts.append("\n".join(cell.text for cell in page.get_text_cells()).strip())
                finally:
                    page.unload()
        finally:
            backend.unload()
        return texts


class NeverOcr:
    version = "never-ocr"

    def extract_page(self, path: Path, page_number: int) -> str:
        raise AssertionError("OCR must not run for a sufficient digital page")


class StaticPageExtractor:
    def __init__(self, pages: list[str], version: str) -> None:
        self.pages = pages
        self.version = version

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        assert page_count == len(self.pages)
        return list(self.pages)


class StaticNativeExtractor:
    def __init__(self, pages: list[str], version: str = "test-native") -> None:
        self.pages = pages
        self.version = version

    def extract_page(self, path: Path, page_number: int) -> str:
        return self.pages[page_number - 1]


class StaticOcr:
    version = "test-tesseract"

    def extract_page(self, path: Path, page_number: int) -> str:
        return f"Scanned circular physical page {page_number} recovered by OCR"


class FakeDoclingDocument:
    def __init__(self) -> None:
        self.seen: list[int] = []

    def export_to_text(self, *, page_no: int, traverse_pictures: bool) -> str:
        assert traverse_pictures is True
        self.seen.append(page_no)
        return f"page {page_no} text"


class FakeDoclingConverter:
    def __init__(self, document: FakeDoclingDocument) -> None:
        self.document = document

    def convert(self, path: Path, **kwargs: object) -> object:
        assert kwargs["max_num_pages"] == 2
        return type("Result", (), {"document": self.document})()


def test_docling_adapter_exports_each_physical_page_in_order(tmp_path: Path) -> None:
    pdf = make_digital_pdf(tmp_path / "digital.pdf", ["one", "two"])
    document = FakeDoclingDocument()
    extractor = DoclingPageTextExtractor(FakeDoclingConverter(document))

    assert extractor.extract_pages(pdf, 2) == ["page 1 text", "page 2 text"]
    assert document.seen == [1, 2]


def test_digital_pdf_preserves_one_based_pages_without_ocr(tmp_path: Path) -> None:
    pdf = make_digital_pdf(
        tmp_path / "digital.pdf",
        ["Digital page one has enough searchable words.", "Digital page two remains separate."],
    )
    pipeline = PageExtractionPipeline(
        DoclingParserTestExtractor(),
        PopplerPageTextExtractor(timeout_seconds=30),
        NeverOcr(),
        minimum_chars=20,
    )

    pages = pipeline.extract(pdf, "ver-1", "run-1", 2)

    assert [page.page_number for page in pages] == [1, 2]
    assert all(
        page.extraction_method in {ExtractionMethod.DOCLING, ExtractionMethod.PDF_TEXT}
        for page in pages
    )
    assert [page.source_pointer.split(";", 1)[0] for page in pages] == [
        "pdf-page:1",
        "pdf-page:2",
    ]
    assert "page one" in pages[0].text
    assert "page two" in pages[1].text


@pytest.mark.skipif(
    shutil.which("pdftoppm") is None or shutil.which("tesseract") is None,
    reason="Poppler and Tesseract are required for the OCR integration fixture",
)
def test_scanned_pdf_uses_real_tesseract_fallback(tmp_path: Path) -> None:
    expected = "SCANNED PAGE REQUIRES TESSERACT OCR FALLBACK"
    pdf = make_scanned_pdf(tmp_path / "scan.pdf", expected)
    pipeline = PageExtractionPipeline(
        DoclingParserTestExtractor(),
        PopplerPageTextExtractor(timeout_seconds=60),
        TesseractPageOcr(timeout_seconds=60),
        minimum_chars=20,
    )

    pages = pipeline.extract(pdf, "ver-scan", "run-scan", 1)

    assert pages[0].page_number == 1
    assert pages[0].extraction_method is ExtractionMethod.TESSERACT
    assert "TESSERACT OCR" in pages[0].text.upper()


def test_twelve_page_scanned_circular_stays_on_ocr_path(tmp_path: Path) -> None:
    pdf = make_scanned_pdf(
        tmp_path / "twelve-page-scan.pdf", "SCANNED CIRCULAR", page_count=12
    )
    pipeline = PageExtractionPipeline(
        StaticPageExtractor([""] * 12, "no-docling-text"),
        StaticNativeExtractor([""] * 12, "no-native-text"),
        StaticOcr(),
        minimum_chars=20,
    )

    pages = pipeline.extract(pdf, "ver-scan", "run-scan", 12)

    assert [page.page_number for page in pages] == list(range(1, 13))
    assert all(page.extraction_method is ExtractionMethod.TESSERACT for page in pages)
    assert all(page.source_pointer.endswith("method:tesseract") for page in pages)


def test_page_15_missing_summary_row_triggers_native_whole_page_fallback() -> None:
    base = "Project row alpha bravo charlie delta echo 2024-001 2,730,755.00"
    docling_pages = [f"Physical page {number} {base}" for number in range(1, 16)]
    native_pages = list(docling_pages)
    native_pages[14] += (
        "\nTotal Allotted Budget of On-going Procurement Activities "
        "175,284,574.00 169,021,829.87"
    )
    pipeline = PageExtractionPipeline(
        StaticPageExtractor(docling_pages, "docling-missing-summary"),
        StaticNativeExtractor(native_pages),
        NeverOcr(),
        minimum_chars=20,
    )

    pages = pipeline.extract(Path("unused.pdf"), "ver", "run", 15)

    assert [page.page_number for page in pages] == list(range(1, 16))
    page_15 = pages[14]
    assert page_15.extraction_method is ExtractionMethod.PDF_TEXT
    assert "175,284,574.00" in page_15.text
    assert "169,021,829.87" in page_15.text
    assert page_15.source_pointer == "pdf-page:15;block:whole-page;method:pdf_text"


def test_candidate_comparison_counts_missing_structured_content() -> None:
    comparison = compare_extractions(
        "Header Project 2024-001 Total 2,730,755.00",
        "Header Project 2024-001 Total 2,730,755.00 Summary 175,284,574.00",
    )

    assert comparison.native_tokens_missing_from_docling == 2
    assert comparison.docling_high_signal_missing_from_native == ()
    assert comparison.docling_lexical_coverage_by_native == 1.0


def test_conflicting_fallback_fails_closed_without_logging_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_marker = "NEVER-LOG-EXTRACTED-CONTENT"
    docling = f"{secret_marker} agreed alpha bravo charlie total 999.00"
    native = f"{secret_marker} agreed alpha bravo charlie total 888.00 extra"
    pipeline = PageExtractionPipeline(
        StaticPageExtractor([docling], "conflicting-docling"),
        StaticNativeExtractor([native]),
        NeverOcr(),
        minimum_chars=20,
    )

    with pytest.raises(IngestionError, match="candidates conflict") as failure:
        pipeline.extract(Path("unused.pdf"), "ver", "run", 1)

    assert failure.value.code == "extraction_conflict"
    assert secret_marker not in caplog.text
    assert secret_marker not in str(failure.value)


def test_repeated_completeness_repair_is_deterministic() -> None:
    docling = "Header Project row alpha bravo charlie 2,730,755.00"
    native = f"{docling} Summary total 175,284,574.00 169,021,829.87"
    pipeline = PageExtractionPipeline(
        StaticPageExtractor([docling], "deterministic-docling"),
        StaticNativeExtractor([native]),
        NeverOcr(),
        minimum_chars=20,
    )

    first = pipeline.extract(Path("unused.pdf"), "ver", "run", 1)
    second = pipeline.extract(Path("unused.pdf"), "ver", "run", 1)

    assert first == second


@pytest.mark.skipif(
    shutil.which("pdftotext") is None,
    reason="Poppler pdftotext is required for the native-layer integration fixture",
)
def test_native_completeness_check_does_not_modify_original(tmp_path: Path) -> None:
    pdf = make_digital_pdf(
        tmp_path / "immutable.pdf", ["Immutable source searchable text 175,284,574.00"]
    )
    before = hashlib.sha256(pdf.read_bytes()).hexdigest()
    pipeline = PageExtractionPipeline(
        DoclingParserTestExtractor(),
        PopplerPageTextExtractor(timeout_seconds=30),
        NeverOcr(),
        minimum_chars=20,
    )

    pages = pipeline.extract(pdf, "ver", "run", 1)

    assert pages[0].page_number == 1
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == before


def test_chunks_stay_on_pages_cover_text_and_have_exact_overlap() -> None:
    pages = [
        PageRecord("ver", "run", 1, "alpha bravo charlie delta echo foxtrot", ExtractionMethod.DOCLING, "ok", 34),
        PageRecord("ver", "run", 2, "golf hotel india juliet kilo lima", ExtractionMethod.TESSERACT, "ok", 28),
    ]
    chunks = PageChunker(size=24, overlap=6).chunk(pages, "a" * 64)

    assert {chunk.page_number for chunk in chunks} == {1, 2}
    for page_number in (1, 2):
        page_chunks = [chunk for chunk in chunks if chunk.page_number == page_number]
        page_text = pages[page_number - 1].text
        assert page_chunks[0].start_offset == 0
        assert page_chunks[-1].end_offset == len(page_text)
        for left, right in zip(page_chunks, page_chunks[1:]):
            assert left.end_offset - right.start_offset == 6
            assert page_text[right.start_offset : left.end_offset] == right.text[:6]
        assert all(chunk.text == page_text[chunk.start_offset : chunk.end_offset] for chunk in page_chunks)
