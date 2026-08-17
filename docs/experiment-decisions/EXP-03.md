# EXP-03 — Page-bounded chunking decision

**Status:** `failed`
**Run ID:** `20260817T085707+0800-3ce70b6`
**Application Git revision:** `3ce70b6604484dff0e040f87aa432e255431621d`
**Source-manifest SHA-256:** `a54c6fd4d69f02a68e793384553772a6370de6614dc870a03853ec13407cf82e`
**Evaluation-dataset SHA-256:** `a19ca426e1981a6e2ea90c7a205a52d21635947fb041b11e5f4965c4aed2f9f4`

## Decision

No chunk policy is selected. All three frozen candidates passed every mechanical and determinism gate, and all preserved form, OCR, and source-attribution context. All three failed the conjunctive table-context gate on required procurement-table observations. EXP-03 therefore failed; this is not a least-bad selection and the criterion is not weakened.

Do not begin EXP-02 or Milestone 10. A future run must preregister a layout-aware table representation or chunking policy and rerun EXP-03 while preserving this failure record.

## Frozen candidates

All candidates used the accepted EXP-01 page strings verbatim, without normalization or page concatenation. They preferred the last ASCII space after `start + overlap` and before the target end, used zero-based half-open Unicode offsets, preserved manifest document/page/sequence order, hashed exact UTF-8 chunk text with SHA-256, and generated IDs as:

`UUIDv5(uuid.NAMESPACE_URL, f"{version_id}:{physical_page}:{sequence}:{start_offset}:{end_offset}:{content_sha256}:page-char-v1:{target_size}:{overlap}")`

The stable experiment version ID was `exp01-` plus the first 32 lowercase hexadecimal characters of the source checksum.

| Candidate | Target characters | Positive overlap | Mechanical result | Interpretability result | Selected |
|---|---:|---:|---|---|---|
| `M9_EXISTING_1200_200` | 1,200 | 200 | Pass | Fail — table context | No |
| `ALT_COMPACT_900_150` | 900 | 150 | Pass | Fail — table context | No |
| `ALT_CONTEXT_1600_250` | 1,600 | 250 | Pass | Fail — table context | No |

## Measurements

| Measurement | `1200/200` | `900/150` | `1600/250` |
|---|---:|---:|---:|
| Pages processed | 41 | 41 | 41 |
| Chunks | 1,495 | 1,982 | 1,104 |
| Split pages | 41 | 41 | 39 |
| Cross-page chunks | 0 | 0 | 0 |
| Uncovered characters | 0 | 0 | 0 |
| Missing positive overlaps | 0 | 0 | 0 |
| Invalid offsets/checksums | 0 | 0 | 0 |
| Duplicate IDs | 0 | 0 | 0 |
| Repeat ordered ID/checksum mismatches | 0 | 0 | 0 |
| Whitespace-only chunks | 4 | 10 | 0 |
| Minimum chunk length | 209 | 153 | 274 |
| Maximum chunk length | 1,200 | 900 | 1,600 |

## Criterion results

| Preregistered criterion | Result | Evidence |
|---|---|---|
| Zero cross-page chunks | Pass for all | Every chunk carries one source checksum and one physical page. |
| Complete usable-text coverage | Pass for all | Zero uncovered characters across 41 accepted pages. |
| Positive overlap on every split page | Pass for all | Minimum observed adjacent overlap equals each candidate's frozen overlap. |
| Valid source offsets/regions | Pass for all | Every chunk equals the exact half-open page substring and its checksum verifies. |
| Unique deterministic identity | Pass for all | Zero duplicate IDs and zero repeat ordered ID/checksum mismatches. |
| Correct document/page attribution | Pass for all | Exact checksum, stable version ID, one-based page, sequence, method, offsets, candidate, and content checksum are present. |
| Form labels remain interpretable | Pass for all | Required foreign-corporation and GAI/LGU checklist associations were present in one chunk or overlapping adjacent pair. |
| OCR context remains interpretable | Pass for all | Required invoice-type, approval/reporting, deadline/extension, and effectivity/publication contexts were present in one chunk or overlapping adjacent pair. |
| Table headers and row meaning remain interpretable | **Fail for all** | Required procurement row/total relationships were separated beyond one chunk or overlapping adjacent pair. |

Because the pass rule is conjunctive, the table-context failure fails each candidate even though its mechanical gates passed.

## Material table-context failures

For every candidate, reviewer probes found zero single-chunk or overlapping-adjacent-pair windows containing each required relationship:

- `RR17_2024_Procurement_Monitoring_Report.pdf`, physical page 1: procurement code `2024-001`, end user `AHRMD`, Early Procurement value `Yes`, ABC `2,730,755.00`, and contract cost `2,622,648.24`.
- The same source, physical page 13: allotted-budget total/MOOE/CO, contract-price total/MOOE/CO, and reported total savings required by `KND-M5-LT-008`.
- The same source, physical page 15: ongoing-procurement allotted-budget and contract-cost totals required by `KND-M5-DF-013`.

The accepted Docling page strings contain very long fixed-width Markdown rows and padding. Character windows of at most 1,600 characters separate row labels or table headers from material values. Positive overlaps of at most 250 characters cannot restore those associations, so a reviewer or downstream retriever would have to guess or join distant fragments. That is explicitly forbidden by the frozen rubric.

## Discrepancies and limitations

- The mechanical success demonstrates page-bounded deterministic slicing only; it does not override the failed semantic-context gate.
- `ALT_CONTEXT_1600_250` avoided whitespace-only chunks but still failed the same required table relationships. Whitespace-only count is therefore diagnostic, not the decision criterion.
- This run evaluated only the three frozen character-window policies. It did not add a post-result candidate, normalize Docling output, synthesize headers, or change layout representation.
- A future layout-aware design must preserve exact page/source provenance and mechanically verifiable offsets or source regions. It requires a new preregistration and run; it cannot relabel this run.
- As in EXP-01, no legal or tax interpretation was adjudicated.

## Evidence

Generated evidence is ignored by Git under:

`evaluation/runs/EXP-03/20260817T085707+0800-3ce70b6/`

Principal artifacts are `registration.json`, `registration.sha256`, `candidate_matrix.json`, `harness-registration.json`, `run_chunking.py`, `mechanical_summary.json`, the three `metrics_*.json` files, primary/repeat `chunks_*.jsonl`, `context_probe.jq`, `interpretability_review.json`, and `evidence_manifest.json`.

## Consequences

- No chunk size, overlap, normalization, table policy, or deterministic identity configuration is selected or frozen as accepted.
- The existing Milestone 9 `1200/200` default remains implementation state, not an accepted EXP-03 configuration.
- No tracked configuration or code is changed because both experiments did not pass.
- EXP-02 and Milestone 10 remain blocked.
- The safe next step is a separately scoped, preregistered EXP-03 rerun with layout-aware table blocks or a table representation that keeps required header/row/value relationships together without crossing physical pages.
