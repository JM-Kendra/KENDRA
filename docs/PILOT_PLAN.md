# Pilot plan

**Status:** Milestone 13 planning artifact for the `demo-dost-v1`/`demo-dost-v1.1`
demonstration releases. This is a metric and gating plan, not evidence that a
pilot has been approved, resourced, or run. It does not resolve any **AGENCY
DECISION REQUIRED** item in `docs/DATA_GOVERNANCE.md` or any **pilot
blocker** question in `docs/OPEN_QUESTIONS.md`; those remain open and are
listed in Section 5.

## Must fix before pilot

1. **Extraction-retry gap.** `find_by_checksum`
   (`apps/api/src/kendra_api/ingestion/registry.py`,
   `apps/api/src/kendra_api/ingestion/pipeline.py`) treats any existing
   `document_versions` row for a checksum — including one whose
   `processing_state` is `failed` — as an unconditional duplicate, and
   refuses to retry it. A document that fails extraction (for example,
   `extraction_conflict`) has no ordinary retry path today: an operator must
   directly delete the failed `document_versions`/`processing_runs`/
   `index_generations` rows before the one-off ingestion command will accept
   the same file again. Found during Milestone 13's from-scratch recovery
   drill (`v11.md` Section 6, finding 2; `docs/DOST_DEMO.md`'s recovery-plan
   section) when three of nine demonstration documents needed exactly this
   manual database cleanup after an unrelated configuration bug was fixed.
   In a real pilot, an operator without direct database access — the
   expected case, per `docs/DATA_GOVERNANCE.md` Section 2's role
   separation — would have no way to recover a document that failed
   extraction for a fixable reason (a corrected extraction policy, a
   reprocessed scan, a retried OCR pass) without escalating to whoever holds
   that access.

   **Proposed: `ADR-013`, retry semantics for failed registry rows.**
   One-paragraph scope: decide how `find_by_checksum` (or the ingestion
   pipeline calling it) should distinguish a `ready` version — a genuine
   duplicate, correctly rejected — from a `failed` one, which represents an
   admitted-but-unprocessed original that a corrected pipeline configuration
   or a retried extraction attempt should be allowed to reprocess without
   discarding the immutable admitted bytes already on disk; the decision
   must also cover what happens to the failed row's original
   `document_id`/`version_id` (reused vs. superseded) and whether a retry
   requires operator confirmation given a `failed` state may also indicate a
   genuinely corrupt or unusable source. **Not written here** — this section
   only proposes the title and scope; implementing a fix without the ADR is
   out of scope for this milestone (it touches duplicate-detection
   semantics that the rest of the ingestion pipeline's tests and contract
   currently assume are simple).

## 1. Why not headline accuracy alone

`docs/PRODUCT_BRIEF.md`'s provisional pilot targets and
`docs/EVALUATION_METHOD.md`'s classification metrics both matter, but a
single aggregate accuracy number can hide the one failure mode this project
treats as worst: a confident, unsupported answer delivered as if it were
supported. `evaluation/M12_FINDINGS.md` part (a) (`KND-M5-UN-002`) is exactly
that failure sitting inside an otherwise-improving accuracy trend (`0.72` →
`0.82`, `docs/DOST_DEMO.md` Section 4, item 1). A pilot go/no-go built only
on headline accuracy would not have flagged it. This plan's three metrics
are chosen specifically to surface that class of failure, category-level
regressions, and audit-integrity problems that an aggregate score cannot
show.

## 2. Primary pilot success metrics

### 2.1 Unsupported false-answer rate

Definition (`docs/EVALUATION_METHOD.md` "Unsupported rejection rate"):
share of deliberately unsupported cases on which the system supplied any
definitive factual answer, rather than a clear "insufficient evidence"
statement.

```text
unsupported false-answer rate = definitive answers on unsupported cases
                                 --------------------------------------
                                 all deliberately unsupported cases attempted
```

- **Measured at the M12 baseline:** `0.1` (1 of 10) —
  `evaluation/runs/M12-gold/20260831T125331Z-0bcc9dd7/report.json`,
  `unsupported_rejection.unsupported_false_answer_rate`. The one false answer
  is `KND-M5-UN-002`.
- **Pilot gate:** this rate must not increase from its measured value at the
  time a pilot go/no-go decision is made, and every individual false answer
  must be named and explained (not merely counted) before a go decision,
  because this is the metric most directly tied to the harm this project's
  own threat model treats as highest-severity (`docs/THREAT_MODEL.md` TM-19:
  "A user copies a plausible AI answer into an official record... without
  opening the cited original").
- This plan does not set a numeric pilot target below the measured baseline
  because no expert-adjudicated gold set exists yet to certify a lower rate
  against (Section 5).

### 2.2 Misclassified-case count by category

Definition (`docs/EVALUATION_METHOD.md` "Supported versus unsupported
classification"): count of `supported`/`unsupported` misclassifications,
reported per category (`direct_factual`, `list_or_table`,
`cross_document_comparison`, `deliberately_unsupported`), not only in
aggregate.

- **Measured at the M12 baseline**
  (`evaluation/runs/M12-gold/20260831T125331Z-0bcc9dd7/report.json`,
  `classification_by_category`):

  | Category | Accuracy | False negatives | False positives |
  |---|---:|---:|---:|
  | `cross_document_comparison` | `0.50` | 5 | 0 |
  | `direct_factual` | `0.70` | 6 | 0 |
  | `list_or_table` | `0.80` | 2 | 0 |
  | `deliberately_unsupported` | `0.90` | 0 | 1 |

- **Pilot gate:** no category may regress from its measured baseline
  accuracy without an explicit, reviewed explanation (not silently absorbed
  into an improved aggregate figure). `cross_document_comparison`'s `0.50`
  is the weakest category measured so far and is explicitly called out —
  an aggregate improvement driven entirely by other categories must not be
  read as fixing it. Report this table for every future run this plan
  gates, not just the categories that improved.

### 2.3 Audit-chain verification

Definition: `PostgresAuditSink.verify_chain()`
(`apps/api/src/kendra_api/audit/sink.py`, invoked via
`scripts/verify_audit_chain.py`) recomputes every `question_audit` record's
hash from its own contents and confirms an unbroken link from genesis to the
latest row.

```bash
docker compose exec api python scripts/verify_audit_chain.py
```

- **Pilot gate:** `PASS` with zero unexplained rows, checked before and
  after every pilot evaluation session, not only once at setup.
  `docs/incidents/INC-001-ghost-evaluation-runs.md` is the standing proof
  this check catches what a row-count glance alone would not — two
  duplicate 50-case runs on 2026-09-01 were discovered specifically because
  the audit trail let sequence ranges be reconstructed, not because anything
  looked wrong at the time.
- A `FAIL` result, or any row whose `evaluation_run_id`/timing cannot be
  explained, is an automatic pilot stop condition (Section 4), independent
  of every other metric in this plan.

## 3. Supporting metrics (reported, not gating)

Carried over from `docs/EVALUATION_METHOD.md` and `docs/PRODUCT_BRIEF.md`
because they inform interpretation of the three gating metrics above, but do
not themselves gate a go/no-go decision until the human-review gate in
Section 5 is met:

- classification accuracy, precision, recall, F1 (overall and by category);
- atomic-fact precision/recall/F1 — currently `status: provisional`
  (`docs/DOST_DEMO.md` Section 4, item 2) and explicitly not usable for a
  gating decision until a human-scored `scoring_worksheet.json` exists;
- citation precision and correct-page citation rate — currently
  `status: provisional_page_level_approximation` for the same reason;
- response latency (median/p90/max, cold vs. warm, OCR vs. non-OCR).

## 4. Stop conditions

Any one of these halts a pilot session immediately, independent of the
metrics above meeting their gates:

1. Audit-chain verification (Section 2.3) returns `FAIL`.
2. A new unsupported false answer appears on a case that previously rejected
   correctly (a genuine regression, not `KND-M5-UN-002` persisting at its
   already-measured, already-disclosed rate).
3. Any document content is found to have altered model behavior outside the
   documented evidence-quoting contract (`docs/THREAT_MODEL.md` TM-08,
   `SYSTEM_INSTRUCTION` in `apps/api/src/kendra_api/answering/model_client.py`).
4. A real agency, confidential, personal, or mixed-permission document is
   found in the pilot corpus — this MVP has no authentication and is
   restricted to the approved public BIR sample only
   (`README.md` "Safety boundary").

## 5. What this plan does not authorize

- **This is not a go decision.** `docs/OPEN_QUESTIONS.md`'s pilot-blocker
  questions (Section 1 item 1, Section 3 items 1–2, Section 5 items 1–3,
  Section 6 item 1, Section 8 items 1–2) are unresolved. No accountable
  agency owner has approved a document class, custodian, offline model, or
  confidentiality boundary for a real pilot.
- **The gold set is not expert-adjudicated.** `dataset_status:
  initial_expert_review_required` on `kendra-bir-public-gold-v2`
  (`evaluation/gold_cases.json`) — every metric in Sections 2–3 is measured
  against a candidate dataset, not a reviewed benchmark
  (`docs/EVALUATION_METHOD.md` "Human review and gold-set promotion").
  Numeric targets are deliberately not set below currently measured values
  until that review exists; this plan gates on non-regression against a
  measured baseline, not on an aspirational target.
- **Milestone 10 remains unaccepted** (`acceptance_claim: false` on every
  report) and Milestone 11 (OCR quality work) is unimplemented
  (`docs/DOST_DEMO.md` Section 4, items 7 and 9). A pilot decision is not
  implied by this release existing.
- This plan does not change `docs/DATA_GOVERNANCE.md`'s **AGENCY DECISION
  REQUIRED** items; none of them are resolved by writing this document.
