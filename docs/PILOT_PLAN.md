# Pilot plan

**Status:** Milestone 14 pilot-preparation plan, design only. Rewritten from
the Milestone 13 planning artifact for the `demo-dost-v1`/`demo-dost-v1.1`/
`demo-dost-v1.2` demonstration releases. **This is not a go decision.** It
does not name a pilot agency, does not resolve any **AGENCY DECISION
REQUIRED** item in `docs/DATA_GOVERNANCE.md`, and does not resolve any
**pilot blocker** question in `docs/OPEN_QUESTIONS.md`. Every fact this
agency's pilot needs that is not established by a committed document or the
code is marked `[STAKEHOLDER: …]` with the question that resolves it — never
supplied as a plausible name, number, or quote. Nothing in this document is
implemented by this milestone.

**Note on Milestone 13's numbered "Must fix before pilot" items.** The five
items that section listed — extraction-retry gap, entrypoint-based
`document-repository` init, offline model bundle, runner-side retrieval
probe, and scripted drill — are no longer presented as a separate numbered
list. They are backlog entries in `docs/pilot/BACKLOG.md` now. Two committed
documents cite them by their old item numbers (`evaluation/M13_FINDINGS.md`
line 156/203, `docs/adr/014-release-drill-evaluation-gate.md` Section 2/4);
those citations are historical text this milestone does not edit. The mapping
from old item number to current backlog ID, for anyone following one of those
citations here:

| Old item | Title | Backlog ID |
|---|---|---|
| 1 | Extraction-retry gap (ADR-013 + fix) | `PB-001`, `PB-002` |
| 2 | Entrypoint-based `document-repository` init | `PB-003` |
| 3 | Offline model bundle | `PB-004` |
| 4 | Runner-side retrieval probe | `PB-005` |
| 5 | Scripted drill | `PB-006` |

## Governance frameworks this pilot sits under

A Philippine agency pilot for a system of this kind sits under RA 12009 and
DICT-CSC JMC 003 Series 2026 as procurement/governance frameworks, and — for
any personal data the corpus or `question_audit` may contain — RA 10173 (the
Data Privacy Act of 2012) and National Privacy Commission (NPC) guidance
(Priority 11). This plan cites these by name only; it does not paraphrase or
invent any of their provisions, and none of the numeric or procedural
requirements below are asserted to come from them unless a committed
document already states so.

---

# Part A — Fourteen pilot-readiness priorities

Each priority states: **current state** (from code and committed documents),
**pilot target**, what is **confirmed** versus an **assumption requiring
stakeholder validation**, and the backlog items (`docs/pilot/BACKLOG.md`)
that deliver it.

## 1. Named pilot agency

**Current state:** No confirmed pilot agency exists in this repository.
`docs/DOST_DEMO.md` documents `demo-dost-v1.2` for a DOST demonstration
audience, but that is a demonstration script, not a pilot commitment — no
committed document names DOST, or any other agency, as a confirmed pilot
partner. Standing rule 7 forbids treating the demo audience as a stakeholder
fact, so this priority is not narrowed to DOST or any other candidate.

**Pilot target:** one named agency with a documented engagement.

**Confirmed:** nothing — this priority is entirely open.

**Qualification criteria** (for the operator to apply to any candidate
agency, not a recommendation of one):

- document volume: the agency's own corpus, or the slice it is willing to
  contribute, must plausibly hold ≥100 representative documents (Priority
  3) in its own custody, under its own authority to share;
- question volume: the agency must be able to supply or co-author enough
  real task questions to support 100 answerable and 30 unsupported
  evaluation cases (Priorities 4–5) without inventing unrepresentative ones;
- an owner with authority over **both** the corpus (who may authorize its
  use) and the staff who would use the system (who may direct their time to
  a pilot) — see Priority 2. An agency without one accountable owner for
  both is not a bounded pilot per `docs/OPEN_QUESTIONS.md` Section 8, item 1
  (pilot blocker).

**`[STAKEHOLDER:` Which agency will serve as the pilot partner, has its
leadership approved participation in writing, and does it meet the three
criteria above? `]`**

**Backlog:** `PB-011`.

## 2. Named agency problem owner

**Current state:** No agency problem owner is named anywhere in this
repository.

**Pilot target:** a named individual (by role, per `docs/DATA_GOVERNANCE.md`
Section 2's functional placeholders) with documented authority over the
pilot corpus and the staff who will use the system.

**Confirmed:** nothing.

**`[STAKEHOLDER:` Who within the pilot agency holds authority over both the
corpus (the "Records custodian" or "Document owner" function in
`docs/DATA_GOVERNANCE.md` Section 2) and the staff who will use the system,
and can that authority be confirmed in a written delegation? `]`**

**Backlog:** `PB-012`.

## 3–5. Corpus and evaluation-set scale-up

These three priorities are addressed together because the same sourcing,
authoring, and review problem underlies all of them; each still gets its own
current-state/target/backlog block below.

**Current state, corpus:** nine documents are currently admitted, 41
physical pages, 382 chunks total (`34/4, 5/2, 35/12, 3/1, 2/1, 3/1, 2/1,
12/3, 286/16` chunk/page pairs, summed from `docs/DOST_DEMO.md` Section 6.3's
`ADR-014` deployment-gate table — the same nine-document set the gold
evaluation and every from-scratch drill through Milestone 13 used). Ingesting
all nine took **201s** wall-clock in the `M13.6-recovery-drill` run,
marker-measured (`docs/DOST_DEMO.md` Section 6.3's wall-clock table); staging
both Ollama models and Docling's layout/table models in parallel took
**953s**, also marker-measured, same table.

**Current state, evaluation set:** `evaluation/gold_cases.json` holds 50
cases — 40 `supported` / 10 `unsupported` (`expected_result` split, read
directly from the file), across `direct_factual` (20), `list_or_table` (10),
`cross_document_comparison` (10), and `deliberately_unsupported` (10)
categories. `dataset_status: initial_expert_review_required` — the set has
never had expert review, and every accuracy figure in this repository is
measured against it as a candidate dataset, not a benchmark.

**Labeled extrapolation, not a projection to trust operationally:** a linear
scale from 9 to 100 documents on the 201s ingest figure gives
`201s × (100/9) ≈ 2,233s` (≈37 minutes) if per-document cost is uniform. This
is stated as a linear estimate only, not a measured or committed number,
because the current 9-document corpus's OCR share (12 of 41 pages, ≈29%) may
not match a real agency corpus's share, and Tesseract-fallback pages measured
slower than native-text pages in every prior round's timing. A pilot corpus
skewed more toward scans would take longer than this estimate; one skewed
toward born-digital text would take less. No number below should be reported
as a target until it is measured against the real pilot corpus.

### 3. 100 or more representative documents

**Pilot target:** ≥100 documents sourced from the pilot agency, agency
provided, under an explicit agreement (custody, provenance, and scope
comparable to today's intake manifest fields — `original_filename`,
`expected_sha256`, `expected_page_count`, `approval_scope`,
`provenance_reference`, `approval_status`, README.md "One-off PDF
ingestion").

**Confirmed:** current corpus size, chunk/page counts, and ingest/staging
timing (code and committed run evidence, above).

**Assumption:** how the agency actually provides the documents, and under
what agreement — `[STAKEHOLDER: will the agency provide documents as a bulk
export, ongoing feed, or supervised on-site scan, and who signs the
provenance/approval-scope agreement for each?]`. Validated by: agency
problem owner + operator.

**Scaling ADR-007 / the drill procedure to 100 documents:** `ADR-007`'s
native-primary-detection policy is a per-document, per-page comparison — it
has no document-count ceiling in its own text, but it has never been
exercised past nine documents, and its own Section 8 "Open items" already
flags corpus under-sampling as unresolved even at nine. A 100-document corpus
would be the first real test of whether the detector's zero-conflict result
on the current corpus (Section 1's finding) generalizes, or whether a larger,
more varied corpus surfaces `extraction_completeness_conflict` failures the
nine-document corpus never triggered. The scripted-drill backlog item
(`PB-006`) and the extraction-retry fix (`PB-002`) both become load-bearing
at this scale: without a retry path, a single `extraction_conflict` on
document 60 of 100 would require the same manual database cleanup Milestone
13's drill needed for three of nine documents (`docs/DOST_DEMO.md` Section
10, "Two real, previously-undiscovered bugs" item 2), at ~11x the exposure.

**Backlog:** `PB-002`, `PB-003`, `PB-013`, `PB-024`.

### 4. 100 answerable evaluation questions

**Pilot target:** 100 answerable questions authored against the pilot's own
≥100-document corpus, expert-reviewed before any number derived from them
governs a decision.

**Confirmed:** current dataset size, composition, and review status (above).

**Assumption:** who authors the questions and under what domain-competence
standard — `[STAKEHOLDER: who from the agency will author or co-author the
100 answerable questions, and does that person have the domain competence
docs/EVALUATION_METHOD.md's "Human review and gold-set promotion" section
requires of at least one reviewer?]`.

**Backlog:** `PB-014`, `PB-010`.

### 5. 30 unsupported evaluation questions

**Pilot target:** 30 deliberately unsupported questions on the same pilot
corpus — three times the current set's 10, reflecting a corpus more than ten
times larger.

**Confirmed:** current unsupported-case count (10 of 50, above).

**Assumption:** same authoring question as Priority 4, extended to
unsupported cases — deliberately constructing a genuinely unanswerable
question against a real corpus without accidentally constructing an
answerable one is itself expert judgment, not an engineering task.

**Expert review, all 130 new plus the existing 50:** `docs/EVALUATION_METHOD.md`'s
"Human review and gold-set promotion" section is the existing, committed
procedure this plan relies on rather than inventing a new one: two
independent reviewers open every named source at every expected page and
verify each expected fact; at least one reviewer must have suitable
domain competence; disagreements are recorded, not silently resolved; an
accountable adjudicator resolves them with a reviewable rationale in Git;
and the dataset's `dataset_status` changes only after case IDs, expected
facts, pages, OCR flags, and unsupported boundaries are approved. This
procedure must run over **all 180 cases** — the 130 new pilot cases and the
existing 50 — before any accuracy, precision, recall, or false-answer-rate
number computed from either set is reported as a pilot result. The existing
50 remain `initial_expert_review_required` today; nothing in this plan
changes that status without the review actually happening.

**Backlog:** `PB-015`, `PB-010`.

## 6. Authentication and roles

**Current state:** no user-facing authentication exists in the code today.
`apps/api/src/kendra_api/config.py` defines `qdrant_api_key` — an internal
credential the `api` service uses to talk to Qdrant (`connections/qdrant.py`)
— and nothing else resembling a login, session, token, or role model exists
anywhere under `apps/api/src/kendra_api/` (checked directly, not assumed).
Deployment is loopback-only (`KENDRA_API_BIND_HOST`/`KENDRA_WEB_BIND_HOST`
both default to `127.0.0.1`) and the safety boundary is policy, not a
technical control: "one trusted evaluator... no authentication or
authorization" (`README.md` "Safety boundary"; `CLAUDE.md` "Current state").

**Pilot target (proposed, not confirmed):** role-based access with at
minimum three roles —

| Role | May | May not |
|---|---|---|
| Agency reviewer | Query, view own query's audit record, view cited originals | Manage documents, run evaluations, view other users' audit records |
| Agency administrator | Manage documents (admit, mark superseded per Priority 8), view full audit trail for the corpus | Run evaluations against the release gate, change deployment configuration |
| Operator/maintainer | Run evaluations, deploy, view full audit trail, manage configuration | — (this is the current de facto role and already has full access) |

This table is a proposal for the operator to bring to the agency, not a
decision — role names and their exact boundaries are `[STAKEHOLDER: what
roles does the agency's own organization actually require, and who holds
each]`.

**Confirmed:** the absence of authentication today (code fact, above).

**Assumption:** the role table above — validated by: agency problem owner +
whoever the agency designates for the "Privacy/security owner" function in
`docs/DATA_GOVERNANCE.md` Section 2.

**API-surface interaction:** `docs/adr/011-interface-surface-unfreeze.md` is
`Proposed`, not `Accepted` — it already establishes the precedent and
procedure (`MVP_SPEC.md` Section 11) for widening the frozen API surface for
upload, request modes, and citation score display. Authentication is a
fourth, larger widening of that same frozen surface (new request/response
fields, new failure modes, new endpoints for role management) and will need
its own specification-unfreeze record following the same procedure ADR-011
demonstrates, whether or not ADR-011 itself is ever accepted.

**Backlog:** `PB-016`.

## 7. Immutable audit trail

**Current state:** the hash-chained, append-only `question_audit` table
exists and works (`apps/api/src/kendra_api/audit/sink.py`) — every gold
evaluation and demo release in Milestones 12–13 verified it with
`scripts/verify_audit_chain.py`, and `INC-001` is the standing proof it
catches what a row count alone would not. Its coverage is narrower than
"every action," though: the schema's `mode` column is constrained to
`'answer'`, `'retrieval_only'`, `'evaluation'` (`sink.py`'s `SCHEMA_SQL`) —
question-asking activity only. `AuditSink`/the record-writing path is wired
only from `answering/service.py`, `answering/router.py`,
`answering/dependencies.py`, `evaluation/run.py`, `evaluation/stage0.py`,
`evaluation/fake_model.py`, and `main.py` (checked by grep across
`apps/api/src/kendra_api/`). Document admission and processing
(`ingestion/registry.py`, `ingestion/pipeline.py`) write no audit row of any
kind today. There is no supersession action to audit yet either (Priority
8), and no administrative-action audit path exists because no
administrative role exists yet (Priority 6).

**Covered today:** interactive queries (`answer`/`retrieval_only` modes) and
gold-evaluation runs (`evaluation` mode).

**Not covered today:** document admission, rejection, or quarantine;
version/status/supersession changes; permission grants, denials, or
privileged actions; backup, restore, or recovery events; and any
administrative action, because none of these write to `question_audit` or
any other audited table.

**Pilot target:** audit coverage extended to the event classes
`docs/DATA_GOVERNANCE.md` Section 8 already specifies as required — upload,
quarantine, admission, rejection, checksum verification; version/status
change, reclassification, withdrawal, hold, disposal; permission grant,
change, revocation, denial, privileged/emergency action; search, source
open, export/print, bulk access; processing, index build/swap/invalidation,
detected corruption; backup, restore, recovery test/failure; and incident
handling. None of these are implemented for anything except query events
today.

**Confirmed:** current chain's exact coverage and wiring (code fact, above).

**Assumption:** the exact schema and retention for the new event classes —
`docs/DATA_GOVERNANCE.md` Section 8 itself marks review frequency, alert/
escalation ownership, privacy constraints, and evidence-handling as
**AGENCY DECISION REQUIRED**, unresolved.

**Backlog:** `PB-017`.

## 8. Document versioning and supersession

**Current state:** `document_versions` (`apps/api/src/kendra_api/ingestion/registry.py`,
`SCHEMA_SQL`) has `document_id`, `version_id`, `sha256` (unique), and
`processing_state` (`processing`/`ready`/`failed`); `find_by_checksum` does
checksum-keyed duplicate detection. There is no `supersedes`,
`superseded_by`, `amends`, `amended_by`, or any lifecycle-status column in
the schema, and no supersession logic anywhere in `registry.py` or
`pipeline.py` (grep for "supersede" across `apps/api/src/` returns nothing).
`docs/DATA_GOVERNANCE.md` Section 4.2 already specifies the target governed-
metadata model — issuer, issuance date, effectivity dates, a lifecycle status
enum (`draft`/`issued`/`effective`/`expired`/`withdrawn`/`revoked`/
`superseded`/`obsolete`/`disputed`/`unknown`), and `supersedes`/
`superseded_by`/`amends`/`amended_by` relationships at document-version level
— but this is policy, not implementation. `ADR-013` (referenced, undrafted)
covers a related but distinct question: retry semantics for a `failed`
processing row, not supersession of a `ready` one.

**Pilot target:** not set here — this priority is questions to decide, not a
decision, per the milestone's own scope:

- **Does a superseded version remain citable?** `docs/DATA_GOVERNANCE.md`
  Section 4.3 says a superseded version "must not appear as current by
  default" but permits "authorized historical retrieval" showing status and
  successor — whether the pilot exposes that at all, and to which role
  (Priority 6), is undecided.
- **What does the audit row show when a document is superseded?** The old
  `version_id`, the new one, both, the actor, and the authority backing the
  supersession claim (`docs/DATA_GOVERNANCE.md` Section 4.2's "authoritative
  register, publication, document passage, or custodian action supporting
  the assertion") are all fields the current audit design (Priority 7) has
  no place to record, because no supersession event exists to audit.
- **Who is authorized to mark a version superseded?** `docs/DATA_GOVERNANCE.md`
  Section 2's "Records custodian" function is closest, but it is a
  functional placeholder, not mapped to a real position (Section 2's own
  **AGENCY DECISION REQUIRED**).

**Confirmed:** current schema's exact columns and absence of supersession
logic (code fact, above).

**Assumption:** everything above — validated by: agency problem owner
(authority) + whoever the agency designates as records custodian.

**Backlog:** `PB-018`.

## 9. Backup and recovery

**Current state:** no backup-and-restore-from-backup capability exists for
this deployment. `docs/DOST_DEMO.md` Section 10's from-scratch recovery
procedure rebuilds a deployment from admitted source PDFs and Git — a
different failure mode than restoring from a backup artifact when the
source-of-record itself is unavailable. `docs/DATA_GOVERNANCE.md` Section 7
already marks retention schedules, RPO, RTO, backup locations, and
restore-test frequency as **AGENCY DECISION REQUIRED**, unresolved.

**Pilot target:** a tested backup-and-restore procedure with RPO/RTO
targets, distinct from the existing from-scratch rebuild drill.

**Design note — the drill is the seed, not the whole thing:**
`docs/DOST_DEMO.md` Section 10's from-scratch procedure already proves the
system can be rebuilt from admitted source bytes plus code, with measured
wall-clock timing per stage (Section 6.3's wall-clock table; Section 10's
Attempt 1/Attempt 2 tables). A genuine restore test needs to additionally
prove recovery from a **backup artifact** — a PostgreSQL dump, a
document-repository snapshot — because "source PDFs and Git are still
available" is not the same failure as "the deployment's own recorded state
is gone and only a backup remains." The drill procedure is the seed of that
restore test: its staging, bring-up, and verification steps (health check,
audit-chain verify) are directly reusable for a restore-from-backup test;
what it does not yet exercise is restoring the PostgreSQL registry and
`question_audit` history itself from a dump rather than rebuilding it from
zero via re-ingestion.

**RPO/RTO:** `[STAKEHOLDER: what recovery point objective (maximum
acceptable data loss) and recovery time objective (maximum acceptable
downtime) does the agency require for this corpus and workflow?]`

**Confirmed:** the existing drill procedure's coverage and measured timings
(above); the absence of a backup-from-artifact test (code/procedure fact).

**Backlog:** `PB-019`.

## 10. NAS deployment

**Current state:** `docker-compose.yml` already supports pointing
`KENDRA_DOCUMENT_STORE_HOST_PATH` at an approved NAS mount instead of the
local `document-repository/` folder (`README.md` "First run" step 2 — "may
instead point to an approved NAS mount... Compose mounts either host path
read-only... so application business logic does not change when the host
root changes"). The abstraction exists; no NAS has ever been used in
practice. `docs/DATA_GOVERNANCE.md` Section 6.1 already marks NAS ownership,
physical/network location, access mapping, encryption/key responsibility,
snapshot/backup behavior, failure behavior, monitoring, recovery test, and
rollback plan as requiring agency approval **before migration** — none of
that approval exists.

**Pilot target (design level only, per this milestone's scope):** a split
between what lives on the GPU appliance (Ollama, the api/web services,
compute) and what lives on the NAS (the document store, PostgreSQL data
directory, backups) — not decided here.

**`[STAKEHOLDER:` which components move to NAS versus stay on the GPU
appliance, who administers the NAS, and what is its network/physical
location relative to the appliance? `]`**

**Confirmed:** the existing host-path abstraction already supports this
without an application code change (code fact, above).

**Backlog:** `PB-032` (before production — the pilot itself may run on
local/appliance storage while NAS design and agency approval are still in
progress; that is a deliberate design choice stated here, not a gap).

## 11. Privacy-impact assessment

RA 10173 (the Data Privacy Act of 2012) and National Privacy Commission
(NPC) guidance are cited by name only below; no provision of either is
paraphrased or invented, per this milestone's own constraint.

**Current state:** `question_audit` stores `question text NOT NULL`
verbatim in an append-only table with no `UPDATE`/`DELETE` path by design
(`apps/api/src/kendra_api/audit/sink.py`) — this is a real retention/
minimization tension if a pilot question, or (via a future citation) a cited
excerpt, ever contains personal data, because the audit design as built
cannot later redact or forget it. `docs/DATA_GOVERNANCE.md` Section 5
already states baseline PII handling rules (least privilege; no restricted
content in Git, public services, or external models; logs should use
identifiers rather than content) but marks the classification scheme, lawful
basis, and permitted document classes as **AGENCY DECISION REQUIRED**,
unresolved — `docs/OPEN_QUESTIONS.md` Section 5 lists three separate
pilot-blocker questions on exactly this point.

**What personal data the pilot may encounter:** agency documents in a
100-document corpus plausibly name individuals (applicants, taxpayers,
signatories, complainants, depending on document class), and any question
asked about such a document is stored verbatim in `question_audit`, along
with (once a citation surfaces the excerpt) the underlying text. Whether
this actually occurs, and to what category of personal or sensitive personal
information, is unknown without the specific pilot corpus.
`[STAKEHOLDER: does the candidate pilot corpus contain personal data as RA
10173 defines it, and if so, which category?]`

**What the plan does:** requires a completed Privacy Impact Assessment,
reviewed and signed by the agency's designated privacy/security function,
before any real agency document is ingested. The PIA must address:

- **minimization** — whether `question_audit`'s verbatim question-text
  storage is acceptable as-is for this corpus, or whether truncation,
  hashing, or a redaction step is needed before pilot use (an open design
  question, not decided here, and in tension with the append-only,
  hash-chained design's own integrity guarantee — truncating after the fact
  would break the chain; any minimization has to be decided before the
  first write, not applied retroactively);
- **retention** — tied to `docs/DATA_GOVERNANCE.md` Section 7's still-open
  retention-schedule decision;
- **access** — tied to Priority 6's role model, so that only an authorized
  role can view another user's query history.

**Confirmed:** the audit schema's verbatim storage and lack of a delete path
(code fact, above); the existing baseline PII rules in
`docs/DATA_GOVERNANCE.md` Section 5.

**Backlog:** `PB-020`.

## 12. User-acceptance testing

**Current state:** no UAT protocol exists in this repository.

**Pilot target:** a scripted UAT protocol — concrete tasks drawn from the
pilot's own 130 authored evaluation questions and real corpus, pass/fail
criteria per task, and a named signer (the agency reviewer role, Priority 6)
who confirms each result.

**Confirmed:** nothing — this priority is an assumption until the agency
validates it.

**Assumption:** the entire protocol, its tasks, and its pass/fail criteria —
validated by: agency problem owner (approves the protocol) + agency reviewer
(executes it and signs off).

**Backlog:** `PB-021` (protocol design, before pilot), `PB-028` (execution
and sign-off, during pilot).

## 13. Staff training

**Current state:** no training plan exists in this repository.

**Pilot target:** a training plan specifying who is trained, how long
training takes, and what a trained user must be able to do afterward
(at minimum: ask a question, read a `supported`/`insufficient_evidence`
result correctly, open a cited original and verify it against the answer,
and know when to escalate to a human reviewer rather than trust the
system's output — the last point directly answering
`docs/THREAT_MODEL.md` TM-19's highest-severity harm, a user copying an
unverified AI answer into an official record).

**Confirmed:** nothing — assumption until the agency validates it.

**Assumption:** audience, duration, and the competency check — validated by:
agency problem owner.

**Backlog:** `PB-022` (design, before pilot), `PB-029` (delivery and
competency confirmation, during pilot).

## 14. Measurable time and accuracy improvements

**Current state (the system baseline, not a promise):** on the current
50-case, unreviewed gold set — `0.82` classification accuracy (`TP 32 / FN 8
/ FP 1 / TN 9`), unsupported false-answer rate `0.1` (1 of 10), and `48/50`
per-case agreement between a from-scratch drill and the release evaluation
(`M13.6-recovery-drill` versus `M13.6-release`) — cite
`evaluation/M13_FINDINGS.md` and the run directories
`evaluation/runs/M13.6-release/20260902T121848Z-b8286729/` and
`evaluation/runs/M13.6-recovery-drill/20260902T121128Z-b8286729/`
(`docs/DOST_DEMO.md` Section 6.3). No time-to-answer figure exists anywhere
in this repository, with or without Kendra — this system has never been
timed against a manual baseline.

**Pilot target:** a baseline study design measuring time-to-answer and
accuracy **without** Kendra first, then **with** Kendra, on the same
questions, by the same staff, so that any improvement claim is a controlled
comparison rather than an assertion.

**Proposed targets are assumptions with reasoning, not numbers:** this plan
does not set a numeric time-saving or accuracy-improvement target, for the
same reason the current metrics plan (Part B, Section 2.1) does not set a
numeric target below the measured baseline: no expert-adjudicated gold set
exists yet (Priorities 4–5), and no without-Kendra baseline has ever been
measured. A defensible target requires the without-Kendra number to exist
first — reporting a percentage improvement target now would be exactly the
kind of invented number standing rule 1 forbids. Once the without-Kendra
baseline exists, a target should be reasoned from whether the measured time
saved exceeds the added review burden this project's own accuracy floor
(no accuracy regression, per Part B Section 2.2) requires — not set in
advance of that evidence.

**Confirmed:** the current system-baseline figures above (from committed run
evidence).

**Assumption:** everything about the study design past "measure both
conditions on the same tasks with the same staff" — validated by: agency
problem owner (approves the study) + operator (designs and runs it).

**Backlog:** `PB-023` (design + without-Kendra measurement, before pilot),
`PB-027` (with-Kendra measurement, during pilot).

---

# Part B — Existing gating-metrics framework, carried forward

Unchanged in substance from the Milestone 13 plan; retained here because
`docs/DOST_DEMO.md` Section 9 and other committed documents point to it, and
because Priority 14 above depends on it. Numbers below remain M13/demo-scale
measurements on the unreviewed 50-case set — they are not re-measured by
this milestone and must not be read as pilot-scale figures.

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
  `unsupported_rejection.unsupported_false_answer_rate`. Reproduced
  unchanged through `demo-dost-v1.2`'s own release evaluation
  (`evaluation/runs/M13.6-release/20260902T121848Z-b8286729/`). The one
  false answer is `KND-M5-UN-002` (Priority 6's `PB-007` addresses whether
  this is fixed, guarded, or remains a disclosed limitation before pilot).
- **Pilot gate:** this rate must not increase from its measured value at the
  time a pilot go/no-go decision is made, and every individual false answer
  must be named and explained (not merely counted) before a go decision,
  because this is the metric most directly tied to the harm this project's
  own threat model treats as highest-severity (`docs/THREAT_MODEL.md` TM-19:
  "A user copies a plausible AI answer into an official record... without
  opening the cited original").
- This plan does not set a numeric pilot target below the measured baseline
  because no expert-adjudicated gold set exists yet to certify a lower rate
  against (Priorities 4–5).

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
  read as fixing it. A pilot corpus and question set will need this same
  table computed fresh once Priorities 4–5's cases exist and pass expert
  review; the table above is not assumed to transfer.

### 2.3 Audit-chain verification

Definition: `PostgresAuditSink.verify_chain()`
(`apps/api/src/kendra_api/audit/sink.py`, invoked via
`scripts/verify_audit_chain.py`) recomputes every `question_audit` record's
hash from its own contents and confirms an unbroken link from genesis to the
latest row.

```bash
make verify-chain
```

- **Pilot gate:** `PASS` with zero unexplained rows, checked before and
  after every pilot evaluation session, not only once at setup.
  `docs/incidents/INC-001-ghost-evaluation-runs.md` is the standing proof
  this check catches what a row-count glance alone would not — two
  duplicate 50-case runs on 2026-09-01 were discovered specifically because
  the audit trail let sequence ranges be reconstructed, not because anything
  looked wrong at the time. Priority 7 above notes this check currently
  covers only query events, not admission, supersession, or administrative
  actions.
- A `FAIL` result, or any row whose `evaluation_run_id`/timing cannot be
  explained, is an automatic pilot stop condition (Section 4 below),
  independent of every other metric in this plan.

## 3. Supporting metrics (reported, not gating)

Carried over from `docs/EVALUATION_METHOD.md` and `docs/PRODUCT_BRIEF.md`
because they inform interpretation of the three gating metrics above, but do
not themselves gate a go/no-go decision until the human-review gate in
Section 5 below is met:

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
   already-measured, already-disclosed rate, or whatever `PB-007` decides
   for it).
3. Any document content is found to have altered model behavior outside the
   documented evidence-quoting contract (`docs/THREAT_MODEL.md` TM-08,
   `SYSTEM_INSTRUCTION` in `apps/api/src/kendra_api/answering/model_client.py`).
4. A real agency, confidential, personal, or mixed-permission document is
   found in the corpus **without the governance this plan's Priorities 6, 7,
   and 11 establish** — this MVP has no authentication today and is
   currently restricted to the approved public BIR sample only
   (`README.md` "Safety boundary"); a pilot with real agency documents does
   not remove this stop condition, it requires the priorities above to be
   satisfied first.

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
- This plan does not name a pilot agency, an agency problem owner, an NAS
  location, an RPO/RTO, or any other fact Part A above marks
  `[STAKEHOLDER: …]`. Every such mark is a question for the operator to put
  to a real agency, not a placeholder answer.
