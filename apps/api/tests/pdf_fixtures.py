"""Runtime-generated public/synthetic PDF fixtures; no PDF bytes are tracked."""

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from kendra_api.ingestion.models import IntakeManifest


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_for(path: Path, page_count: int) -> IntakeManifest:
    return IntakeManifest(
        original_filename=path.name,
        expected_sha256=sha256(path),
        expected_page_count=page_count,
        approval_scope="synthetic-test-only",
        provenance_reference="pytest-generated-fixture",
    )


def make_digital_pdf(path: Path, page_texts: list[str]) -> Path:
    document = canvas.Canvas(str(path), pagesize=(612, 792), pageCompression=0)
    for page_number, text in enumerate(page_texts, start=1):
        document.setFont("Helvetica", 16)
        document.drawString(72, 720, f"Physical page {page_number}")
        document.setFont("Helvetica", 12)
        document.drawString(72, 680, text)
        document.showPage()
    document.save()
    return path


def make_scanned_pdf(path: Path, text: str, page_count: int = 1) -> Path:
    image = Image.new("RGB", (2400, 1000), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", 76)
    draw.text((120, 350), text, fill="black", font=font)
    document = canvas.Canvas(str(path), pagesize=(612, 792), pageCompression=0)
    for _ in range(page_count):
        document.drawImage(ImageReader(image), 24, 260, width=564, height=235)
        document.showPage()
    document.save()
    return path
