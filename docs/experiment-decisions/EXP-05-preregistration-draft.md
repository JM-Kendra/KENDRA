# EXP-05 — Grounding-gate rejection and verified-span fidelity

**Status:** Draft. **Not frozen and not a registration.** It becomes
`evaluation/runs/EXP-05/<run-id>/registration.json` only when every item in *Requires before
freezing* is satisfied and the file is checksummed **before any candidate is run**.
**Drafted:** 2026-08-21
**Gates:** [ADR-010](../adr/010-verified-span-answering.md), proposed. Its Section 4 supplies
the decision conditions verbatim; nothing here may add, remove, reword, or reorder them.
**Identifier:** EXP-05 is already reserved in `ARCHITECTURE.md` — *"Does the two-stage
grounding gate reject unsupported output?"*, deciding *"structured response schema, validation
rules, abstention wording, and fail-closed behavior."* No new identifier is minted.

> **Scope widening, requires approval.** `ARCHITECTURE.md` scopes EXP-05 to the unsupported
> stratum plus synthetic invalid evidence IDs and below-threshold retrievals. ADR-010
> conditions 1, 3 and 4 extend it to the **supported** strata: span fidelity, citation
> precision, and the exclusion of synthesis from a supported status. That widening is recorded
> here rather than assumed, and it is not adopted unilaterally by this draft.

> **Disclosure.** This draft follows the 2026-08-21 live run in which `KND-M5-UN-002` returned
> `supported` for a deliberately unsupported currentness question. That ordering is stated
> plainly, as in ADR-010. The candidate matrix, controlled variables, and scoring rule below
> are argued from the architecture and from what is mechanically checkable; no rule names a
> case, document, word, or question class from that run.

## 1. Question and decision

**EXP-05 — Does the grounding gate reject unsupported output, and does verified-span answering
hold span fidelity and citation precision across all fifty evaluation cases without
synthesis reaching a supported status?**

Produces: acceptance of ADR-010's `verified-span-answering-v1` recorded in a reviewed
`EXP-05.md`, or an explicit rejection selecting nothing.

## 2. Frozen candidate matrix

| Candidate | Answer mode | Selectable |
|---|---|---|
| `A0_PROSE_BASELINE` | ADR-003 as implemented at `666ba8e` — model-authored claims | No — reference only |
| `A1_VERIFIED_SPAN` | ADR-010 §3.1–3.3 — verbatim spans, enforced citation precision, evidence packets for synthesis strata | Yes |

`A0` reproduces the mode whose defect prompted ADR-010 and establishes the baseline column. It
is never selectable.

**Retrieval-only-for-every-stratum is deliberately excluded as a candidate.** A mode that emits
no claims satisfies conditions 1 and 3 vacuously and conditions 2, 4 and 5 trivially, so
admitting it here would let the safest possible answer win by abstaining everywhere. ADR-010
§5 places coverage and usefulness outside this record. Selecting that mode requires its own
preregistration carrying a coverage floor, and it may not be introduced mid-experiment.

## 3. Controlled variables

Source bytes and checksums; the nine-PDF approval manifest; one-based page numbering; the
ADR-007 `native-primary-detection-v1` extraction policy under which the corpus was ingested;
the chunker configuration (1200 / 200); the pinned BGE-M3 embedding model and its digest; the
pinned answer model identity, quantization and digest; decoding temperature 0 with a recorded
seed; the exact generation set, recorded by generation identifier and Qdrant collection name;
container image; CPU and memory limits; per-request timeout; concurrency of one; disabled
outbound networking; and `pipeline_git_revision` set to the real commit rather than the null
OID. Only the answer mode varies.

**`top_k` and the candidate threshold are frozen at the prototype values (8 and 0.5) and are
NOT selected by this experiment.** EXP-02 has never been run. Freezing an unselected value is a
recorded compromise, not a decision: no recall, precision, or sufficiency claim may be drawn
from either number, and this experiment's outcome does not ratify them.

## 4. Input contract

All fifty cases in `evaluation/gold_cases.json`, stratum assignment taken from each case's
`category` field and frozen before the run. No case may be reclassified, re-scoped, excluded,
or moved between strata once the run begins.

**Known gold-set defects and why they do not contaminate this experiment.** Four facts are held
by the page-scoping defect recorded in `gold-case-defect-CD003-CD010.md`, and `KND-M5-CD-001`
carries a numeric-formatting mismatch. Those defects live in `expected_pages` and
`expected_answer_facts`. **No condition in ADR-010 §4 reads either field.** Conditions 2 and 4
read only stratum membership; conditions 1, 3 and 5 are internal consistency checks between an
answer and its own citations. The defect is therefore out of this experiment's scoring path and
is recorded here so that absence is deliberate rather than overlooked.

**This experiment does not establish page correctness.** Whether a citation reopens the correct
physical page is EXP-06's question and is not scored here.

## 5. Scoring rule — frozen

**Span containment is byte-exact.** A claim's text must appear as a contiguous substring of the
stored UTF-8 evidence text of a citation attached to that claim. No whitespace collapsing, no
case folding, no Unicode normalization, no punctuation equivalence, no substring matching
against a *different* citation's excerpt. A span assembled from two non-adjacent fragments of
one excerpt is noncontiguous and fails.

This strictness is deliberate. The EXP-07 truth-set work established that a permissive matcher
manufactures agreement, and the EXP-01 scorer defect — a join blob built in first-occurrence
order that can match a token as a substring of a corrupted one — is exactly what a loose rule
produces. That defect must be repaired **in this registration**, before results are visible, or
its scorer must not be reused here at all.

**Per-condition measurement:**

1. **Span fidelity.** For every supported answer, for every claim: containment holds against at
   least one of that claim's own citations. Any failure anywhere across the fifty cases fails
   condition 1. Zero exemptions, zero hand-classified acceptable paraphrase.
2. **Unsupported stratum.** Each of the ten `deliberately_unsupported` cases returns
   `status: insufficient_evidence`, `answer` byte-identical to the 51-character contract
   string, `claims == []`, and `citations == []`. **`conflicting_evidence`,
   `source_unavailable`, and `system_error` on an unsupported case each fail condition 2**;
   a typed failure is not an abstention and may not be counted as one.
3. **Citation precision.** For every (claim, citation) pair in every supported answer, that
   citation's excerpt contains that claim's span. A citation attached to a claim it does not
   contain is a violation. Required: zero violations.
4. **No synthesis in a supported status.** Every `cross_document_comparison` case returns
   either an evidence packet or `insufficient_evidence`. Any such case returning `supported`
   with a generated connective claim fails condition 4 outright.
5. **Reproducibility.** Two consecutive executions under one recorded configuration and seed
   produce, for all fifty cases, identical `status`, identical claim texts, and identical
   citation sets compared as `(version_id, page, chunk_id, excerpt)`. Any difference fails.
   The run is not averaged, retried, or best-of-N selected, and a differing pair is not
   resolved by a third run.

**Synthetic fail-closed injections**, carried over from `ARCHITECTURE.md`'s EXP-05 method and
run alongside the fifty cases: unknown evidence IDs, evidence from a non-active generation,
checksum-mismatched candidates, below-threshold retrievals, a missing original, malformed and
non-JSON model output, and document-borne instruction fixtures. Each must produce its typed
non-supported status with zero citations. Any injection that yields a supported answer fails
the experiment independently of conditions 1–5.

## 6. Decision rule — frozen

**Select `A1_VERIFIED_SPAN` only if all five ADR-010 §4 conditions hold and every synthetic
injection fails closed.** There is no partial credit, no provisional acceptance, no
per-condition waiver, and no candidate is selected on a subset of strata.

If any condition fails, select nothing and apply ADR-010 §8: close ADR-010 as rejected, state
which condition failed and on which cases, and leave ADR-003's answer mode in force. Do not
soften a condition and rerun. Do not carry a partial result forward.

No part of Section 5 or 6 may be reworded once the first candidate has run.

## 7. What selection does and does not mean

Selection would establish that the answering surface cannot emit a claim its own cited text
does not contain, and that unsupported questions fail closed. It would establish nothing else.

It does **not** establish:

- that a faithfully quoted span answers the question asked — ADR-010 §3.4 records this residual;
- that citations reopen the correct physical page — EXP-06;
- retrieval recall, `top_k`, or the candidate threshold — EXP-02, never run;
- OCR fidelity — a verbatim span quoted from corrupted OCR text is still corrupted; SF-01,
  MF-01 and the 8.8% substitution rate remain open under ADR-008 and ADR-009;
- answer usefulness or coverage — explicitly outside scope per ADR-010 §5;
- that EXP-01 has passed, or that EXP-03 or Milestone 10 may proceed. All three remain blocked
  regardless of this experiment's outcome.

## 8. Failure behavior

A failed run is recorded, not repaired. The failing condition, the cases that failed it, and
the exact configuration are written into `EXP-05.md`. `A0_PROSE_BASELINE` is never selected as
a fallback: it is the configuration whose defect prompted the record.

If the run cannot complete — model unavailable, timeout, corpus unreachable — the attempt is
recorded as incomplete with its cause. An incomplete run is not a failure of the candidate and
is not evidence for it either.

## Requires before freezing

1. **ADR-010's activation conditions unchanged** since drafting, and the record still in
   `Proposed` status. If any condition has been reworded, this draft is void.
2. **The MVP_SPEC unfreeze recorded** per ADR-010 §9. Requiring verbatim spans and returning
   evidence packets alters an observable acceptance requirement and an API field meaning, so a
   clarification is not sufficient.
3. **The scope widening above approved** by the reviewer.
4. **ADR-010 §6 regression tests written and committed** before the run, so their content
   cannot be shaped by its result.
5. **`A1_VERIFIED_SPAN` implemented.** ADR-010 changed no code. There is currently nothing to
   run as candidate A1.
6. **The EXP-01 scorer defect repaired in this registration**, or a fresh scorer written for
   the containment rule in Section 5.
7. **Reviewer acknowledgement that `top_k` and the threshold are frozen unselected**, with
   EXP-02 still outstanding.
