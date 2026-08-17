"""Docling-first page extraction with explicit Tesseract fallback."""

import re
import subprocess
import tempfile
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


def _is_structurally_blank(path: Path, page_number: int) -> bool:
    page = PdfReader(path, strict=True).pages[page_number - 1]
    contents = page.get_contents()
    has_content = bool(contents and contents.get_data().strip())
    resources = page.get("/Resources") or {}
    has_xobjects = bool(resources.get("/XObject"))
    return not has_content and not has_xobjects


class PageExtractionPipeline:
    def __init__(self, docling: PageTextExtractor, ocr: PageOcr, minimum_chars: int) -> None:
        self._docling = docling
        self._ocr = ocr
        self._minimum_chars = minimum_chars

    @property
    def tool_identity(self) -> str:
        return f"{self._docling.version};fallback={self._ocr.version}"

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
            if docling_chars >= self._minimum_chars:
                records.append(
                    PageRecord(
                        version_id=version_id,
                        processing_run_id=processing_run_id,
                        page_number=page_number,
                        text=docling_text,
                        extraction_method=ExtractionMethod.DOCLING,
                        quality_result="sufficient_text",
                        docling_text_chars=docling_chars,
                    )
                )
                continue
            if _is_structurally_blank(path, page_number):
                records.append(
                    PageRecord(
                        version_id=version_id,
                        processing_run_id=processing_run_id,
                        page_number=page_number,
                        text="",
                        extraction_method=ExtractionMethod.VERIFIED_BLANK,
                        quality_result="verified_blank",
                        docling_text_chars=docling_chars,
                    )
                )
                continue
            ocr_text = self._ocr.extract_page(path, page_number)
            if _meaningful_char_count(ocr_text) < self._minimum_chars:
                raise IngestionError("unextractable_page", f"page {page_number} has insufficient OCR text")
            records.append(
                PageRecord(
                    version_id=version_id,
                    processing_run_id=processing_run_id,
                    page_number=page_number,
                    text=ocr_text,
                    extraction_method=ExtractionMethod.TESSERACT,
                    quality_result="ocr_sufficient_text",
                    docling_text_chars=docling_chars,
                )
            )
        if [page.page_number for page in records] != list(range(1, page_count + 1)):
            raise IngestionError("page_mapping_failure", "physical page sequence is not contiguous")
        return records
