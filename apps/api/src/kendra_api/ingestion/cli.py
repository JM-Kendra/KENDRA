"""Trusted-operator command for one approved local PDF and intake manifest."""

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

from kendra_api.config import Settings
from kendra_api.connections.postgres import PostgresConnection
from kendra_api.connections.qdrant import QdrantConnection
from kendra_api.ingestion.chunking import PageChunker
from kendra_api.ingestion.embedding import OllamaBgeM3Embedder
from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.extraction import (
    DoclingPageTextExtractor,
    NativePrimaryDetectionPipeline,
    PageExtractionPipeline,
    PopplerPageTextExtractor,
    TesseractPageOcr,
)
from kendra_api.ingestion.pipeline import IngestionPipeline
from kendra_api.ingestion.registry import PostgresRegistry
from kendra_api.ingestion.storage import LocalDocumentAdmissionStore
from kendra_api.ingestion.validation import load_intake_manifest, resolve_intake_path
from kendra_api.ingestion.vector_store import QdrantVectorGenerationStore
from kendra_api.source_revision import resolve_source_revision


def _extractor(settings: Settings) -> PageExtractionPipeline | NativePrimaryDetectionPipeline:
    docling = DoclingPageTextExtractor(
        max_bytes=settings.pdf_max_bytes,
        artifacts_path=settings.docling_artifacts_path,
    )
    native = PopplerPageTextExtractor(settings.ingestion_tool_timeout_seconds)
    ocr = TesseractPageOcr(settings.ingestion_tool_timeout_seconds)
    if settings.extraction_completeness_policy == NativePrimaryDetectionPipeline.policy_version:
        # ADR-007 §2.3: this policy does not use the candidate-agreement threshold.
        return NativePrimaryDetectionPipeline(
            docling, native, ocr, settings.minimum_page_text_chars
        )
    return PageExtractionPipeline(
        docling,
        native,
        ocr,
        settings.minimum_page_text_chars,
        settings.extraction_candidate_minimum_agreement,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest one approved PDF into Kendra without enabling question answering."
    )
    parser.add_argument("pdf", help="PDF path relative to KENDRA_INGESTION_INTAKE_ROOT")
    parser.add_argument("--manifest", required=True, help="Approved JSON intake manifest")
    return parser


async def _run(pdf: str, manifest_arg: str) -> None:
    settings = Settings()  # type: ignore[call-arg]
    pdf_path = resolve_intake_path(settings.ingestion_intake_root, pdf)
    manifest_path = resolve_intake_path(settings.ingestion_intake_root, manifest_arg)
    manifest = load_intake_manifest(manifest_path)
    qdrant = QdrantConnection(settings)
    embedder = OllamaBgeM3Embedder(
        str(settings.ollama_url),
        settings.embedding_model,
        settings.embedding_batch_size,
        settings.ingestion_tool_timeout_seconds,
    )
    pipeline = IngestionPipeline(
        registry=PostgresRegistry(PostgresConnection(settings)),
        storage=LocalDocumentAdmissionStore(settings.document_store_root),
        extractor=_extractor(settings),
        chunker=PageChunker(settings.chunk_size_chars, settings.chunk_overlap_chars),
        embedder=embedder,
        vectors=QdrantVectorGenerationStore(
            qdrant.client, settings.qdrant_collection_prefix
        ),
        max_bytes=settings.pdf_max_bytes,
        max_pages=settings.pdf_max_pages,
        pipeline_revision=resolve_source_revision().revision,
    )
    try:
        result = await pipeline.ingest(pdf_path, manifest)
        print(json.dumps(asdict(result), default=str, sort_keys=True))
    finally:
        await embedder.close()
        await qdrant.close()


def main() -> None:
    args = _parser().parse_args()
    try:
        asyncio.run(_run(args.pdf, args.manifest))
    except IngestionError as exc:
        print(json.dumps({"state": "failed", "error_code": exc.code}), file=sys.stderr)
        raise SystemExit(2) from None
    except Exception:
        print(
            json.dumps({"state": "failed", "error_code": "unexpected_failure"}),
            file=sys.stderr,
        )
        raise SystemExit(3) from None


if __name__ == "__main__":
    main()
