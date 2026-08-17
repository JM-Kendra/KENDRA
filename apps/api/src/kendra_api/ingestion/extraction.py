"""Page extraction with independent completeness detection and safe fallback."""

import collections
import re
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from pypdf import PdfReader

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import ExtractionMethod, PageRecord


class PageTextExtractor(Protocol):
    version: str

    def extract_pages(self, path: Path, page_count: int) -> list[str]: ...


class PageOcr(Protocol):
    version: str

    def extract_page(self, path: Path, page_number: int) -> str: ...


class NativePageTextExtractor(Protocol):
    version: str

    def extract_page(self, path: Path, page_number: int) -> str: ...


class DoclingPageTextExtractor:
    """Use Docling layout extraction while exporting one physical page at a time."""

    version = "docling-2.117.0"

    def __init__(
        self,
        converter: object | None = None,
        max_bytes: int = 50 * 1024 * 1024,
        artifacts_path: Path | None = None,
    ) -> None:
        self._converter = converter
        self._max_bytes = max_bytes
        self._artifacts_path = artifacts_path

    def _default_converter(self) -> object:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import (
            PdfPipelineOptions,
            TableStructureV2Options,
        )
        from docling.document_converter import DocumentConverter, PdfFormatOption

        options = PdfPipelineOptions()
        options.do_ocr = False
        options.do_table_structure = True
        options.table_structure_options = TableStructureV2Options()
        options.artifacts_path = self._artifacts_path
        return DocumentConverter(
            allowed_formats=[InputFormat.PDF],
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)},
        )

    def extract_pages(self, path: Path, page_count: int) -> list[str]:
        converter = self._converter or self._default_converter()
        try:
            result = converter.convert(
                path,
                raises_on_error=True,
                max_num_pages=page_count,
                max_file_size=self._max_bytes,
            )
            document = result.document
            pages = [
                document.export_to_text(page_no=number, traverse_pictures=True).strip()
                for number in range(1, page_count + 1)
            ]
        except Exception as exc:
            raise IngestionError("docling_failure", "Docling could not parse the PDF") from exc
        if len(pages) != page_count:
            raise IngestionError("page_mapping_failure", "Docling page mapping is incomplete")
        return pages


class PopplerPageTextExtractor:
    """Read one native PDF text layer with a stable physical-page boundary."""

    def __init__(self, timeout_seconds: int) -> None:
        self._timeout = timeout_seconds
        try:
            completed = subprocess.run(
                ["pdftotext", "-v"],
                check=True,
                capture_output=True,
                text=True,
                timeout=min(timeout_seconds, 10),
            )
            output = completed.stderr or completed.stdout
            binary_version = output.splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            binary_version = "pdftotext-unavailable"
        self.version = f"{binary_version};layout=true;nopgbrk=true"

    def extract_page(self, path: Path, page_number: int) -> str:
        try:
            completed = subprocess.run(
                [
                    "pdftotext",
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-layout",
                    "-nopgbrk",
                    str(path),
                    "-",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise IngestionError(
                "native_text_failure",
                f"native text extraction failed for page {page_number}",
            ) from exc
        return completed.stdout.strip()


class TesseractPageOcr:
    def __init__(self, timeout_seconds: int, language: str = "eng", dpi: int = 300) -> None:
        self._timeout = timeout_seconds
        self._language = language
        self._dpi = dpi
        try:
            completed = subprocess.run(
                ["tesseract", "--version"],
                check=True,
                capture_output=True,
                text=True,
                timeout=min(timeout_seconds, 10),
            )
            binary_version = completed.stdout.splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            binary_version = "tesseract-unavailable"
        self.version = f"{binary_version};language={language};dpi={dpi}"

    def extract_page(self, path: Path, page_number: int) -> str:
        with tempfile.TemporaryDirectory(prefix="kendra-ocr-") as directory:
            prefix = Path(directory) / "page"
            try:
                subprocess.run(
                    [
                        "pdftoppm",
                        "-f",
                        str(page_number),
                        "-l",
                        str(page_number),
                        "-singlefile",
                        "-png",
                        "-r",
                        str(self._dpi),
                        str(path),
                        str(prefix),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=self._timeout,
                )
                completed = subprocess.run(
                    [
                        "tesseract",
                        str(prefix.with_suffix(".png")),
                        "stdout",
                        "-l",
                        self._language,
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=self._timeout,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise IngestionError("ocr_failure", f"OCR failed for page {page_number}") from exc
        return completed.stdout.strip()


def _meaningful_char_count(text: str) -> int:
    return len(re.sub(r"[^\w]", "", text, flags=re.UNICODE))


_TOKEN_PATTERN = re.compile(r"\w+(?:[.,:/-]\w+)*", flags=re.UNICODE)


def _comparison_tokens(text: str) -> collections.Counter[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return collections.Counter(
        re.sub(r"[^\w]", "", token, flags=re.UNICODE)
        for token in _TOKEN_PATTERN.findall(normalized)
        if re.sub(r"[^\w]", "", token, flags=re.UNICODE)
    )


def _high_signal_tokens(tokens: collections.Counter[str]) -> set[str]:
    return {token for token in tokens if any(character.isdigit() for character in token)}


@dataclass(frozen=True, slots=True)
class CompletenessComparison:
    native_tokens_missing_from_docling: int
    docling_tokens_missing_from_native: int
    docling_lexical_coverage_by_native: float
    docling_high_signal_missing_from_native: tuple[str, ...]


def compare_extractions(docling_text: str, native_text: str) -> CompletenessComparison:
    """Compare token multiplicity after deterministic Unicode/punctuation folding."""

    docling = _comparison_tokens(docling_text)
    native = _comparison_tokens(native_text)
    native_missing = native - docling
    docling_missing = docling - native
    docling_total = sum(docling.values())
    covered = docling - docling_missing
    coverage = sum(covered.values()) / docling_total if docling_total else 1.0
    high_signal_missing = tuple(sorted(_high_signal_tokens(docling_missing)))
    return CompletenessComparison(
        native_tokens_missing_from_docling=sum(native_missing.values()),
        docling_tokens_missing_from_native=sum(docling_missing.values()),
        docling_lexical_coverage_by_native=coverage,
        docling_high_signal_missing_from_native=high_signal_missing,
    )


def _is_structurally_blank(path: Path, page_number: int) -> bool:
    page = PdfReader(path, strict=True).pages[page_number - 1]
    contents = page.get_contents()
    has_content = bool(contents and contents.get_data().strip())
    resources = page.get("/Resources") or {}
    has_xobjects = bool(resources.get("/XObject"))
    return not has_content and not has_xobjects


class PageExtractionPipeline:
    """Apply the frozen ``native-page-token-coverage-v1`` completeness policy."""

    policy_version = "native-page-token-coverage-v1"

    def __init__(
        self,
        docling: PageTextExtractor,
        native: NativePageTextExtractor,
        ocr: PageOcr,
        minimum_chars: int,
        minimum_candidate_agreement: float = 0.90,
    ) -> None:
        self._docling = docling
        self._native = native
        self._ocr = ocr
        self._minimum_chars = minimum_chars
        self._minimum_candidate_agreement = minimum_candidate_agreement
        if not 0.0 <= minimum_candidate_agreement <= 1.0:
            raise ValueError("minimum candidate agreement must be between zero and one")

    @property
    def tool_identity(self) -> str:
        return (
            f"policy={self.policy_version};docling={self._docling.version};"
            f"native={self._native.version};fallback={self._ocr.version};"
            f"minimum_chars={self._minimum_chars};"
            f"minimum_candidate_agreement={self._minimum_candidate_agreement:.2f}"
        )

    @staticmethod
    def _pointer(page_number: int, method: ExtractionMethod) -> str:
        return f"pdf-page:{page_number};block:whole-page;method:{method.value}"

    def _record(
        self,
        *,
        version_id: str,
        processing_run_id: str,
        page_number: int,
        text: str,
        method: ExtractionMethod,
        quality_result: str,
        docling_chars: int,
    ) -> PageRecord:
        return PageRecord(
            version_id=version_id,
            processing_run_id=processing_run_id,
            page_number=page_number,
            text=text,
            extraction_method=method,
            quality_result=quality_result,
            docling_text_chars=docling_chars,
            source_pointer=self._pointer(page_number, method),
        )

    def extract(
        self,
        path: Path,
        version_id: str,
        processing_run_id: str,
        page_count: int,
    ) -> list[PageRecord]:
        docling_pages = self._docling.extract_pages(path, page_count)
        if len(docling_pages) != page_count:
            raise IngestionError("page_mapping_failure", "page count changed during extraction")
        records: list[PageRecord] = []
        for page_number, docling_text in enumerate(docling_pages, start=1):
            docling_chars = _meaningful_char_count(docling_text)
            native_text = self._native.extract_page(path, page_number)
            native_chars = _meaningful_char_count(native_text)
            if native_chars >= self._minimum_chars:
                comparison = compare_extractions(docling_text, native_text)
                if comparison.native_tokens_missing_from_docling == 0:
                    records.append(
                        self._record(
                            version_id=version_id,
                            processing_run_id=processing_run_id,
                            page_number=page_number,
                            text=docling_text,
                            method=ExtractionMethod.DOCLING,
                            quality_result="native_completeness_confirmed",
                            docling_chars=docling_chars,
                        )
                    )
                    continue
                if (
                    comparison.docling_high_signal_missing_from_native
                    or comparison.docling_lexical_coverage_by_native
                    < self._minimum_candidate_agreement
                ):
                    raise IngestionError(
                        "extraction_conflict",
                        f"extraction candidates conflict on page {page_number}",
                    )
                records.append(
                    self._record(
                        version_id=version_id,
                        processing_run_id=processing_run_id,
                        page_number=page_number,
                        text=native_text,
                        method=ExtractionMethod.PDF_TEXT,
                        quality_result="native_replaced_incomplete_docling",
                        docling_chars=docling_chars,
                    )
                )
                continue
            if docling_chars < self._minimum_chars and _is_structurally_blank(path, page_number):
                records.append(
                    self._record(
                        version_id=version_id,
                        processing_run_id=processing_run_id,
                        page_number=page_number,
                        text="",
                        method=ExtractionMethod.VERIFIED_BLANK,
                        quality_result="verified_blank",
                        docling_chars=docling_chars,
                    )
                )
                continue
            ocr_text = self._ocr.extract_page(path, page_number)
            if _meaningful_char_count(ocr_text) < self._minimum_chars:
                raise IngestionError("unextractable_page", f"page {page_number} has insufficient OCR text")
            if docling_chars >= self._minimum_chars:
                comparison = compare_extractions(docling_text, ocr_text)
                if (
                    comparison.docling_high_signal_missing_from_native
                    or comparison.docling_lexical_coverage_by_native
                    < self._minimum_candidate_agreement
                ):
                    raise IngestionError(
                        "extraction_conflict",
                        f"Docling and OCR conflict on page {page_number}",
                    )
            records.append(
                self._record(
                    version_id=version_id,
                    processing_run_id=processing_run_id,
                    page_number=page_number,
                    text=ocr_text,
                    method=ExtractionMethod.TESSERACT,
                    quality_result="ocr_sufficient_text",
                    docling_chars=docling_chars,
                )
            )
        if [page.page_number for page in records] != list(range(1, page_count + 1)):
            raise IngestionError("page_mapping_failure", "physical page sequence is not contiguous")
        return records
