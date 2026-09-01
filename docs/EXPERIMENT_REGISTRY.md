# Experiment ID registry

**Status:** Single source of truth for experiment-ID allocation, effective
2026-09-01. Created after two identifier collisions surfaced in the same day
(`EXP-04`, then `EXP-08`) while drafting a new experiment, on top of the
pre-existing `EXP-07` collision — resolved the same day this registry was
created (see the `EXP-07` and `EXP-12` rows). This document exists so an ID is
checked once, here, instead of by hand-scanning `EXPERIMENT_PLAN.md`,
`ARCHITECTURE.md`, `KENDRA_MIGRATION_HANDOFF.md`, `docs/experiment-decisions/`,
and `evaluation/` separately.

**Rule (also in `CLAUDE.md`): a new experiment ID is allocated only by adding a
row to this table first.** Claiming an ID by filing a draft, an ADR reference,
or a code comment without a row here is not an allocation and does not resolve
a collision.

**Status values:** `reserved` (named in a plan or architecture table, no draft
or run exists yet), `draft` (a preregistration draft file exists, not frozen,
not run), `frozen` (a registration is locked at a specific commit before any
candidate has run — `EXP-11` is the first), `run` (executed at least once, with
a recorded decision — the status cell notes the outcome), `void` (claimed and
later abandoned/superseded with nothing carried forward). An `open collision`
value also exists, for an ID with two unreconciled claims at once — none
currently in that state; `EXP-07` was in it until 2026-09-01, see its row.

| ID | Title | Status | Owning document | Collision notes |
|---|---|---|---|---|
| `EXP-01` | Page extraction and OCR — can Docling with page-level Tesseract fallback preserve exact physical-page identity and required table/form context? | `run` — failed; the 2026-08-20 ADR-007 rerun is inconclusive, not passed | `docs/EXPERIMENT_PLAN.md` §3; decision record `docs/experiment-decisions/EXP-01.md` | None |
| `EXP-02` | BGE-M3 retrieval configuration — which bounded retrieval config retrieves every adjudicated supporting page without falsely supporting an unsupported case? | `reserved` — planned, never drafted or run | `docs/EXPERIMENT_PLAN.md` §4; `docs/ARCHITECTURE.md` row `EXP-02` | None |
| `EXP-03` | Page-bounded chunking — which deterministic, page-bounded chunking policy preserves complete evidence and layout context? | `run` — failed; blocked from resuming until `EXP-01` passes | `docs/EXPERIMENT_PLAN.md` §5; decision record `docs/experiment-decisions/EXP-03.md`; rerun draft `docs/experiment-decisions/EXP-03-rerun-preregistration-draft.md` | None |
| `EXP-04` | Local Qwen model selection — which of two pinned, workstation-suitable Qwen variants meets the structured grounded-answer and bounded latency contract? | `reserved` — planned, never drafted or run under this number | `docs/EXPERIMENT_PLAN.md` §6; `docs/ARCHITECTURE.md` row `EXP-04` | **Resolved.** `evaluation/EXP-04_PREREG_DRAFT.md` briefly claimed this ID (2026-09-01) for a narrower, different model-comparison study. Renamed to `EXP-08`, then to `EXP-11` after that also collided — see the `EXP-11` row. `EXP-04` itself, as defined here, was never drafted and is untouched by that history. |
| `EXP-05` | Two-stage grounding and abstention gate — does the API-enforced gate reject unsupported/malformed/uncited/unknown-ID/prompt-injected output? | `draft` — `docs/experiment-decisions/EXP-05-preregistration-draft.md`, not frozen, not run | `docs/EXPERIMENT_PLAN.md` §7; `docs/ARCHITECTURE.md` row `EXP-05` | None |
| `EXP-06` | Citation source resolution — can every supported claim's citation resolve to the checksum-matched original, correct physical page, and exact excerpt? | `reserved` — planned, never drafted or run | `docs/EXPERIMENT_PLAN.md` §8; `docs/ARCHITECTURE.md` row `EXP-06` | None |
| `EXP-07` | Is the build genuinely offline? — artifact staging, disabled outbound networking, zero-network acceptance. | `reserved` — planned, never drafted or run | `docs/ARCHITECTURE.md` row `EXP-07` | **Resolved 2026-09-01.** Previously collided with a drafted OCR render-resolution experiment also filed as `EXP-07`. Reviewer decision: `ARCHITECTURE.md`'s offline-build claim keeps `EXP-07`; the OCR draft moved to `EXP-12` (see that row). Dated resolution note in `KENDRA_MIGRATION_HANDOFF.md`; the original collision note there is kept, not deleted. |
| `EXP-08` | Publication atomicity — is publication atomic across PostgreSQL and Qdrant under injected failure before/during a generation publish? | `reserved` — planned, never drafted or run under this number | `docs/ARCHITECTURE.md` row `EXP-08` | **Resolved.** `evaluation/EXP-08_PREREG_DRAFT.md` (itself renamed from `EXP-04_PREREG_DRAFT.md`) briefly claimed this ID (2026-09-01) for the same model-comparison study. Renamed to `EXP-11` after this collision was found and checked against this same table. `EXP-08` itself, as defined here (publication atomicity), was never drafted and remains unclaimed. |
| `EXP-09` | Parser limits — are parser limits adequate for hostile or accidental inputs (malformed, oversized, high-page-count, image-heavy fixtures)? | `reserved` — planned, never drafted or run | `docs/ARCHITECTURE.md` row `EXP-09` | None |
| `EXP-10` | Storage abstraction survives a mount change — checksum/stream/range-read/atomic-admission/rebuild tests against two local mount points. | `reserved` — planned, never drafted or run | `docs/ARCHITECTURE.md` row `EXP-10` | None |
| `EXP-11` | Model comparison on facts-in-context-but-abstained cases — does a larger local model answer the specific gold cases where `qwen2.5:7b-instruct` abstained despite sufficient retrieved context? Feeds `EXP-04`'s model-selection question; does not replace it. | `frozen` — 2026-09-01, at commit `19192da8469f8ee0a8bdf1e791969056e8e3232d`. Frozen copy: `docs/experiment-decisions/EXP-11-preregistration.md`; the pre-freeze draft remains at `evaluation/EXP-11_PREREG_DRAFT.md` with a pointer to the frozen copy. Stage 0 executed 2026-09-01 (`evaluation/runs/EXP-11/20260901T014805Z-0bcc9dd7/`); Stage 1 not yet run. | `docs/experiment-decisions/EXP-11-preregistration.md` (frozen); `evaluation/EXP-11_PREREG_DRAFT.md` (pre-freeze history) | Checked against this table before being claimed (2026-09-01); does not collide with anything recorded here as of this date. Previously filed as `EXP-04` then `EXP-08` — see those rows. **Protocol deviation, recorded 2026-09-01 (read-only truncation check, not remediated here):** Section 4's frozen mechanism requires Stage 0 to seed a static retriever from a pinned evidence packet captured by `M12_FINDINGS.md` part (d), explicitly forbidding a live Qdrant/embedding call. `stage0_summary.md` (line 5) records that Stage 0 as executed instead used evidence "freshly re-fetched via the real `QdrantRetriever`" — a live call. No machine-readable record of part (d)'s own chunk IDs was ever persisted, so a chunk-identical replay cannot be verified against any artifact. See `evaluation/runs/EXP-11/20260901T014805Z-0bcc9dd7/truncation_check.md` Section 5 and `M12_FINDINGS.md` part (f) for the full detail. Whoever reviews Stage 0 before Stage 1 should account for this before treating Stage 0's classifications as satisfying Section 4 as frozen. |
| `EXP-12` | OCR render resolution and recognition model — which bounded combination of render resolution and Tesseract model reduces digit substitution on OCR-retained pages without regressing any already-correct token? | `draft` — `docs/experiment-decisions/EXP-12-preregistration-draft.md`, not frozen, not run | `docs/experiment-decisions/EXP-12-preregistration-draft.md`; gated by ADR-009 (proposed) | **Renamed from `EXP-07` on 2026-09-01** to resolve the collision recorded there — see the `EXP-07` row. No new collision found for `EXP-12` as of this date. `docs/adr/009-ocr-render-and-model-fidelity.md` and `docs/experiment-decisions/ocr-substitution-measurement.md` still cite this experiment as `EXP-07` in several places and were not updated as part of this rename — flagged as a known follow-up, not silently left. |

## Allocating a new ID

1. Search this table for the next unclaimed number — do not assume the
   numerically-next ID is free; `EXP-08`, `EXP-09`, and `EXP-10` were all
   already reserved in `ARCHITECTURE.md` when `EXP-08` was tried and found
   taken on 2026-09-01.
2. Add a row here first, with `status: reserved` or `draft` as appropriate, a
   one-line scope, the owning document, and `None` in collision notes unless
   one exists.
3. Only then file the draft, ADR reference, or code comment that uses the ID.
4. If a later check finds the ID already claimed elsewhere in the tracked docs
   that this table doesn't yet list, add that source to the row's owning
   document and record the collision — do not silently pick a different number
   without leaving a trail, per this project's established practice around the
   `EXP-04`, `EXP-07`, and `EXP-08` entries above.
