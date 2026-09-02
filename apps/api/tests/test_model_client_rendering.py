"""EXP-13 (docs/experiment-decisions/EXP-13-preregistration.md) — evidence
rendering modes and the label-leak check.

`render_evidence` (the default, `KENDRA_EVIDENCE_RENDERING=current`) must stay
byte-identical to its pre-EXP-13 output. `render_evidence_with_labels`
(`R1_LABELED`, `labeled`) is the only new rendering path, and is never
selected by default. `detect_label_leak` implements the frozen spec's
Section 7 rule: no claim may echo the document label or page the labeled
rendering adds.
"""

from __future__ import annotations

import json

import httpx
import pytest

from kendra_api.answering.model_client import (
    OllamaAnswerModel,
    detect_label_leak,
    render_evidence,
    render_evidence_with_labels,
)
from kendra_api.answering.models import Evidence

pytestmark = pytest.mark.milestone12


def _evidence(evidence_id="ev-1", filename="RR_11_2024_Invoicing_Amendments.pdf", page=1, text="Some quoted chunk text."):
    return Evidence(
        evidence_id=evidence_id,
        text=text,
        document_id="doc-1",
        version_id="ver-1",
        filename=filename,
        page=page,
        chunk_id="chunk-1",
        source_sha256="0" * 64,
        processing_run_id="run-1",
        extraction_method="pdf_text",
        generation_id="gen-1",
    )


# --------------------------------------------------------------------------------------
# render_evidence (current, default) is unchanged.
# --------------------------------------------------------------------------------------


def test_render_evidence_current_mode_is_byte_identical_to_pre_exp13_output():
    items = [
        _evidence(evidence_id="ev-1", text="First chunk."),
        _evidence(evidence_id="ev-2", text="Second chunk."),
    ]

    output = render_evidence(items)

    assert output == (
        '<evidence id="ev-1">\nFirst chunk.\n</evidence>\n'
        '<evidence id="ev-2">\nSecond chunk.\n</evidence>'
    )
    # No document identity of any kind, confirmed directly (not just "no new field").
    assert "RR_11_2024" not in output
    assert "page" not in output.lower()


# --------------------------------------------------------------------------------------
# render_evidence_with_labels (R1_LABELED, experimental).
# --------------------------------------------------------------------------------------


def test_render_evidence_with_labels_adds_filename_and_page():
    items = [_evidence(evidence_id="ev-1", filename="RMC_77_2024_Invoicing_QA_OCR.pdf", page=9, text="Chunk text.")]

    output = render_evidence_with_labels(items)

    assert output == (
        '<evidence id="ev-1" document="RMC_77_2024_Invoicing_QA_OCR.pdf" page="9">\n'
        "Chunk text.\n</evidence>"
    )


def test_render_evidence_with_labels_uses_only_existing_evidence_fields():
    # Requires-before-freezing item 1's resolution: the label is exactly
    # Evidence.filename/.page, not a new human-title mapping.
    item = _evidence(filename="RR_11_2024_Invoicing_Amendments.pdf", page=3)

    output = render_evidence_with_labels([item])

    assert f'document="{item.filename}"' in output
    assert f'page="{item.page}"' in output


# --------------------------------------------------------------------------------------
# OllamaAnswerModel selects the rendering by mode; default is unchanged.
# --------------------------------------------------------------------------------------


async def _generate_and_capture_prompt(*, rendering_mode: str | None, evidence: list[Evidence]) -> str:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["prompt"] = json.loads(request.content)["prompt"]
        return httpx.Response(
            200,
            json={"response": json.dumps({"status": "insufficient_evidence", "claims": [], "limitations": []})},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://ollama")
    kwargs = {"base_url": "http://ollama", "model": "qwen2.5:7b-instruct", "client": client}
    if rendering_mode is not None:
        kwargs["rendering_mode"] = rendering_mode
    model = OllamaAnswerModel(**kwargs)

    await model.generate("question?", evidence)
    await client.aclose()
    return captured["prompt"]


async def test_default_rendering_mode_is_current():
    item = _evidence(filename="RR_11_2024_Invoicing_Amendments.pdf", page=1, text="Chunk.")

    prompt = await _generate_and_capture_prompt(rendering_mode=None, evidence=[item])

    assert '<evidence id="ev-1">\nChunk.\n</evidence>' in prompt
    assert "document=" not in prompt


async def test_labeled_rendering_mode_is_selected_explicitly():
    item = _evidence(filename="RR_11_2024_Invoicing_Amendments.pdf", page=1, text="Chunk.")

    prompt = await _generate_and_capture_prompt(rendering_mode="labeled", evidence=[item])

    assert 'document="RR_11_2024_Invoicing_Amendments.pdf"' in prompt
    assert 'page="1"' in prompt


def test_invalid_rendering_mode_is_rejected():
    with pytest.raises(ValueError, match="rendering_mode"):
        OllamaAnswerModel(base_url="http://ollama", model="qwen2.5:7b-instruct", rendering_mode="verbose")


# --------------------------------------------------------------------------------------
# detect_label_leak (Section 7's label-leak rule).
# --------------------------------------------------------------------------------------


def test_detect_label_leak_finds_a_leaked_filename():
    item = _evidence(filename="RMC_77_2024_Invoicing_QA_OCR.pdf", page=9)
    claim_text = "Per RMC_77_2024_Invoicing_QA_OCR.pdf, the deadline is December 31, 2024."

    leaked = detect_label_leak(claim_text, [item])

    assert "RMC_77_2024_Invoicing_QA_OCR.pdf" in leaked


def test_detect_label_leak_finds_a_leaked_page_reference():
    item = _evidence(filename="RR_11_2024_Invoicing_Amendments.pdf", page=3)
    claim_text = "As stated on page 3, adjustments are due by December 31, 2024."

    leaked = detect_label_leak(claim_text, [item])

    assert "page 3" in leaked


def test_detect_label_leak_is_case_insensitive_for_page_references():
    item = _evidence(page=3)
    claim_text = "See Page 3 for details."

    leaked = detect_label_leak(claim_text, [item])

    assert "page 3" in leaked


def test_detect_label_leak_finds_nothing_in_a_clean_claim():
    item = _evidence(filename="RR_11_2024_Invoicing_Amendments.pdf", page=3)
    claim_text = "Adjustments shall be undertaken on or before December 31, 2024."

    leaked = detect_label_leak(claim_text, [item])

    assert leaked == []


def test_detect_label_leak_against_multiple_evidence_items_checks_every_one():
    items = [
        _evidence(evidence_id="ev-1", filename="RR_11_2024_Invoicing_Amendments.pdf", page=1),
        _evidence(evidence_id="ev-2", filename="RMC_77_2024_Invoicing_QA_OCR.pdf", page=9),
    ]
    claim_text = "This combines RR_11_2024_Invoicing_Amendments.pdf with the other source."

    leaked = detect_label_leak(claim_text, items)

    assert "RR_11_2024_Invoicing_Amendments.pdf" in leaked
    assert "RMC_77_2024_Invoicing_QA_OCR.pdf" not in leaked
