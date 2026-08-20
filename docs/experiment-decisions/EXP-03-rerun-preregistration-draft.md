# EXP-03 rerun — preregistration draft

**Status:** Draft. **Not frozen and not a registration.** It becomes
`evaluation/runs/EXP-03/<run-id>/registration.json` only when the open decision in Section 3
is settled and the file is checksummed before any processing.
**Drafted:** 2026-08-20
**Blocked by:** EXP-01 returning to `passed`. EXP-03 may not resume before that, and this
draft creates no exception to it.
**Preserves:** the existing failure record in [EXP-03.md](EXP-03.md), which is not rewritten.

## 1. Why a rerun is warranted rather than a relabel

The recorded EXP-03 failure is specific: all three candidates failed the conjunctive
table-context gate because "the accepted Docling page strings contain very long fixed-width
Markdown rows and padding," separating row labels from values beyond any window the candidates
could span.

Under ADR-007 the accepted page strings are no longer Docling Markdown. They are Poppler
`pdftotext -layout -nopgbrk` output, which preserves column alignment as whitespace within a
line rather than reflowing cells into Markdown rows. The failing input no longer exists in the
form that produced the failure. That is a genuine change of input, not a reinterpretation of
the old result, and it is the only proper basis for rerunning rather than relabelling.

It is **not** a prediction that the rerun passes. Row labels and values may still fall in
different character windows, and `-layout` output can carry wide inter-column padding of its
own.

## 2. Frozen inputs

| Field | Value |
|---|---|
| `experiment_id` | `EXP-03` |
| `registration_state` | `frozen_before_processing_or_scoring` |
| `input_contract` | Accepted page strings taken **verbatim** from the passing EXP-01 run, no normalization, no page concatenation |
| `exp01_run_id` | the passing EXP-01 run id — **must be a run whose status is `passed`** |
| `pages_input_sha256` | SHA-256 of that run's `pages_primary.jsonl` |
| `source_manifest_sha256` | `a54c6fd4d69f02a68e793384553772a6370de6614dc870a03853ec13407cf82e` |
| `evaluation_dataset_sha256` | the dataset checksum in force at freeze time, per the CD-003/CD-010 memo |
| `execution` | mode container, network none, seed 0, concurrency 1, whole-run timeout carried from the prior registration |
| `hardware` | recorded at freeze time as observed |
| `tools` | Python, `kendra_chunker` identity, hash and identity construction, all as observed |

Chunk identity construction is carried over unchanged from the prior run, including the
`UUIDv5(NAMESPACE_URL, "{version_id}:{physical_page}:{sequence}:{start}:{end}:{content_sha256}:page-char-v1:{target}:{overlap}")`
form and the `exp01-` plus first 32 hex characters version id.

## 3. Open decision — the candidate matrix

**This is the one thing that must be settled before freezing, and it must be settled without
looking at how the new page strings chunk.** Writing the matrix after inspecting the output
would be selecting a candidate to fit its own result.

The matrix should contain both of the following groups.

**Group 1, controlled comparison.** The three previously frozen character-window candidates,
unchanged: `M9_EXISTING_1200_200`, `ALT_COMPACT_900_150`, `ALT_CONTEXT_1600_250`. Rerunning
them on the new input is what isolates the effect of the retention change. If one now passes,
the failure was Docling's representation and not the windowing strategy — a result worth
having on record either way.

**Group 2, layout-aware candidate.** EXP-03's own record requires that "a future run must
preregister a layout-aware table representation or chunking policy." At least one candidate
must therefore not be a blind character window. Its definition is the open decision. A
defensible shape, offered for selection rather than assumed:

- never split within a physical line, so a `-layout` table row stays intact;
- when a page's lines carry a detected column structure, prepend the page's header lines to
  every chunk drawn from that page, recorded as carried context with its own provenance so a
  reviewer can tell carried text from contiguous text;
- otherwise fall back to the character-window behaviour with a declared target and overlap;
- preserve every existing mechanical guarantee: page-bounded, zero cross-page chunks, exact
  half-open offsets, verifiable content checksums, deterministic identity.

Header carry-forward is the part that needs the most scrutiny before it is frozen. It
duplicates source text into multiple chunks, and the citation invariant requires that a
reviewer can always tell which bytes are the chunk's own and which were carried. If that
cannot be represented cleanly in `ChunkRecord`, the candidate should be defined without carry
forward and the gate allowed to fail honestly.

## 4. Criteria — unchanged

EXP-03's existing preregistered criteria apply verbatim. None is added, removed, reworded, or
re-tuned. The pass rule stays conjunctive: a candidate that passes every mechanical gate and
fails table context fails, exactly as all three did.

The reviewer rubric carries over its `mechanical`, `table_context`, `form_context`,
`ocr_context`, `attribution` and `selection` items.

## 5. Required probes — unchanged

The same reviewer probes that produced the recorded failure, so the rerun is comparable:

- `RR17_2024_Procurement_Monitoring_Report.pdf` page 1 — procurement code `2024-001`, end user
  `AHRMD`, Early Procurement `Yes`, ABC `2,730,755.00`, contract cost `2,622,648.24`, all
  within one chunk or one overlapping adjacent pair;
- the same source page 13 — allotted-budget total/MOOE/CO, contract-price total/MOOE/CO, and
  reported total savings required by `KND-M5-LT-008`;
- the same source page 15 — the ongoing-procurement totals required by `KND-M5-DF-013`.

Page 15 is now the sharper test. Its totals were absent from the representation entirely when
EXP-03 last ran; under ADR-007 they are present, so for the first time the probe measures
whether chunking keeps them with their row labels rather than whether they exist at all.

## 6. Harness

Adapt `run_chunking.py` and `context_probe.jq` from
`evaluation/runs/EXP-03/20260817T085707+0800-3ce70b6/`. As with the EXP-01 rerun, the harness
and any scoring script are written and checksummed **before** the run produces output, and
verified unchanged afterwards. Primary and repeat passes, ordered-identity comparison, and the
existing metrics files are all retained.

## 7. Decision rule

Carried over unchanged: a candidate is selected only if it satisfies every mechanical and
interpretability criterion across two deterministic passes. Any missing observation is
inconclusive; any explicit criterion failure is failed. No least-bad selection is permitted,
and no candidate may be added after outputs are visible.

## 8. Scope

This rerun selects a chunk policy or fails. It does not implement retrieval or question
answering, does not pass EXP-02, and does not by itself unblock Milestone 10. It does not
change `evaluation/gold_cases.json` from `initial_expert_review_required`.
