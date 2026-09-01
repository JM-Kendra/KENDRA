# Experiment ID registry

**Status:** Single source of truth for experiment-ID allocation, effective
2026-09-01. Created after two identifier collisions surfaced in the same day
(`EXP-04`, then `EXP-08`) while drafting a new experiment, on top of the
pre-existing, still-open `EXP-07` collision. This document exists so an ID is
checked once, here, instead of by hand-scanning `EXPERIMENT_PLAN.md`,
`ARCHITECTURE.md`, `KENDRA_MIGRATION_HANDOFF.md`, `docs/experiment-decisions/`,
and `evaluation/` separately.

**Rule (also in `CLAUDE.md`): a new experiment ID is allocated only by adding a
row to this table first.** Claiming an ID by filing a draft, an ADR reference,
or a code comment without a row here is not an allocation and does not resolve
a collision.

**Status values:** `reserved` (named in a plan or architecture table, no draft
or run exists yet), `draft` (a preregistration draft file exists, not frozen,
not run), `frozen` (a registration is checksummed and locked; none yet exist in
this project), `run` (executed at least once, with a recorded decision — the
status cell notes the outcome), `void` (claimed and later abandoned/superseded
with nothing carried forward). One ID (`EXP-07`) currently has two
unreconciled claims at once; the taxonomy above has no slot for that, so its
status is written as `open collision` instead of forced into one of the five —
see its row.

| ID | Title | Status | Owning document | Collision notes |
|---|---|---|---|---|
| `EXP-01` | Page extraction and OCR — can Docling with page-level Tesseract fallback preserve exact physical-page identity and required table/form context? | `run` — failed; the 2026-08-20 ADR-007 rerun is inconclusive, not passed | `docs/EXPERIMENT_PLAN.md` §3; decision record `docs/experiment-decisions/EXP-01.md` | None |
| `EXP-02` | BGE-M3 retrieval configuration — which bounded retrieval config retrieves every adjudicated supporting page without falsely supporting an unsupported case? | `reserved` — planned, never drafted or run | `docs/EXPERIMENT_PLAN.md` §4; `docs/ARCHITECTURE.md` row `EXP-02` | None |
| `EXP-03` | Page-bounded chunking — which deterministic, page-bounded chunking policy preserves complete evidence and layout context? | `run` — failed; blocked from resuming until `EXP-01` passes | `docs/EXPERIMENT_PLAN.md` §5; decision record `docs/experiment-decisions/EXP-03.md`; rerun draft `docs/experiment-decisions/EXP-03-rerun-preregistration-draft.md` | None |
| `EXP-04` | Local Qwen model selection — which of two pinned, workstation-suitable Qwen variants meets the structured grounded-answer and bounded latency contract? | `reserved` — planned, never drafted or run under this number | `docs/EXPERIMENT_PLAN.md` §6; `docs/ARCHITECTURE.md` row `EXP-04` | **Resolved.** `evaluation/EXP-04_PREREG_DRAFT.md` briefly claimed this ID (2026-09-01) for a narrower, different model-comparison study. Renamed to `EXP-08`, then to `EXP-11` after that also collided — see the `EXP-11` row. `EXP-04` itself, as defined here, was never drafted and is untouched by that history. |
| `EXP-05` | Two-stage grounding and abstention gate — does the API-enforced gate reject unsupported/malformed/uncited/unknown-ID/prompt-injected output? | `draft` — `docs/experiment-decisions/EXP-05-preregistration-draft.md`, not frozen, not run | `docs/EXPERIMENT_PLAN.md` §7; `docs/ARCHITECTURE.md` row `EXP-05` | None |
| `EXP-06` | Citation source resolution — can every supported claim's citation resolve to the checksum-matched original, correct physical page, and exact excerpt? | `reserved` — planned, never drafted or run | `docs/EXPERIMENT_PLAN.md` §8; `docs/ARCHITECTURE.md` row `EXP-06` | None |
| `EXP-07` | **Two unreconciled definitions under one number.** (a) `docs/ARCHITECTURE.md`: "Is the build genuinely offline?" — artifact staging, disabled outbound networking, zero-network acceptance. (b) `docs/experiment-decisions/EXP-07-preregistration-draft.md`: "OCR render resolution and recognition model" — DPI/Tesseract-model selection to reduce digit substitution. | `open collision` — **left open, not resolved here.** Already on record: `KENDRA_MIGRATION_HANDOFF.md` — *"EXP-07 identifier collision: architecture reserves EXP-07 for offline-build validation, while an OCR preregistration draft also uses EXP-07. Resolve before freezing either plan."* | (a) `docs/ARCHITECTURE.md` row `EXP-07`; (b) `docs/experiment-decisions/EXP-07-preregistration-draft.md` | **Open — reviewer decision required.** Neither claim is authoritative over the other in this registry. Resolving it means either renumbering one of the two, or a reviewer ruling that one definition supersedes the other. Not decided by this document. |
| `EXP-08` | Publication atomicity — is publication atomic across PostgreSQL and Qdrant under injected failure before/during a generation publish? | `reserved` — planned, never drafted or run under this number | `docs/ARCHITECTURE.md` row `EXP-08` | **Resolved.** `evaluation/EXP-08_PREREG_DRAFT.md` (itself renamed from `EXP-04_PREREG_DRAFT.md`) briefly claimed this ID (2026-09-01) for the same model-comparison study. Renamed to `EXP-11` after this collision was found and checked against this same table. `EXP-08` itself, as defined here (publication atomicity), was never drafted and remains unclaimed. |
| `EXP-09` | Parser limits — are parser limits adequate for hostile or accidental inputs (malformed, oversized, high-page-count, image-heavy fixtures)? | `reserved` — planned, never drafted or run | `docs/ARCHITECTURE.md` row `EXP-09` | None |
| `EXP-10` | Storage abstraction survives a mount change — checksum/stream/range-read/atomic-admission/rebuild tests against two local mount points. | `reserved` — planned, never drafted or run | `docs/ARCHITECTURE.md` row `EXP-10` | None |
| `EXP-11` | Model comparison on facts-in-context-but-abstained cases — does a larger local model answer the specific gold cases where `qwen2.5:7b-instruct` abstained despite sufficient retrieved context? Feeds `EXP-04`'s model-selection question; does not replace it. | `draft` — `evaluation/EXP-11_PREREG_DRAFT.md`, not frozen, not run | `evaluation/EXP-11_PREREG_DRAFT.md` | Checked against this table before being claimed (2026-09-01); does not collide with anything recorded here as of this date. Previously filed as `EXP-04` then `EXP-08` — see those rows. |

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
