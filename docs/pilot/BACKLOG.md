# Pilot backlog

Milestone 14 design artifact. Every item below is scope only — **nothing
here is implemented by this milestone.** Owner-role values are limited to:
`operator`, `agency problem owner`, `agency IT`, `agency reviewer`,
`external`. `status: CONFIRMED` means a committed document or the code
already establishes the need; `status: ASSUMPTION` means it requires
stakeholder validation, and the item names who validates it.

Cross-reference: `docs/PILOT_PLAN.md`'s 14 priorities each cite at least one
ID below. `evaluation/M13_FINDINGS.md` Section 7 ("What remains open") and
the prior `docs/PILOT_PLAN.md`'s numbered items 1–5 are each mapped to an ID
here — none are dropped.

---

## Required before pilot

### PB-001 — Draft ADR-013: retry semantics for failed registry rows

- **Reason:** `find_by_checksum` (`apps/api/src/kendra_api/ingestion/registry.py`)
  treats any existing `document_versions` row for a checksum — including a
  `failed` one — as an unconditional duplicate and refuses to retry it. No
  ADR exists covering how a `failed` row should be distinguished from a
  genuine duplicate, what happens to its `document_id`/`version_id`, or
  whether a retry needs operator confirmation. `CLAUDE.md` explicitly
  forbids implementing a fix without this ADR first.
- **Acceptance criterion:** `docs/adr/013-*.md` is committed, with a decided
  scope covering reused-vs-superseded `document_id`/`version_id` semantics
  and whether retry requires operator confirmation.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** `PB-002` cannot be implemented per `CLAUDE.md`'s own
  standing rule; the extraction-retry gap (Priority 3) persists at pilot
  scale.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`CLAUDE.md` "Current state"; `docs/PILOT_PLAN.md`
  Priority 3; formerly `docs/PILOT_PLAN.md` item 1, cited by
  `evaluation/M13_FINDINGS.md` and `docs/DOST_DEMO.md` Section 10).

### PB-002 — Implement the extraction-retry fix

- **Reason:** Without this fix, a document that fails extraction for a
  fixable reason (a corrected extraction policy, a reprocessed scan, a
  retried OCR pass) has no ordinary retry path short of direct database
  cleanup — confirmed during Milestone 13's drill, where three of nine
  documents needed exactly this manual cleanup
  (`docs/DOST_DEMO.md` Section 10, "Two real, previously-undiscovered bugs,"
  item 2).
- **Acceptance criterion:** a new regression test demonstrates a `failed`
  `document_versions` row is retried without direct database deletion;
  `make test-full` passes with the new test(s) included.
- **Dependency:** `PB-001`.
- **Proposed owner role:** operator.
- **Risk if omitted:** at 100-document scale, any extraction failure
  requires an operator with direct database access to intervene — the
  expected pilot operator, per `docs/DATA_GOVERNANCE.md` Section 2's role
  separation, does not have that access.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (same sources as `PB-001`).

### PB-003 — Entrypoint-based `document-repository` initialization

- **Reason:** A fresh deployment still needs one privileged host `chown`
  command before its first ingestion (`README.md` Troubleshooting), found
  not to cover a truly fresh `document-repository/` by the
  `demo-dost-v1.1` from-tag recovery drill (`docs/DOST_DEMO.md` Section 10,
  "Recovery drill against `demo-dost-v1.1`"). A pilot operator should not
  need a privileged Docker command and host-level `chown` before first use.
- **Acceptance criterion:** `docker compose --profile ingestion run --rm
  ingest` succeeds against a genuinely fresh `document-repository/` with
  zero host-side `chown`/`mkdir` steps.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** every fresh pilot deployment (including any disaster
  recovery rebuild) requires an operator with host-level Docker privileges,
  which `docs/DATA_GOVERNANCE.md` Section 2 treats as a distinct, more
  privileged role than ordinary operation.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`docs/PILOT_PLAN.md` "Must fix before pilot" item
  2, `docs/DOST_DEMO.md` Section 10).

### PB-004 — Offline model bundle

- **Reason:** `ollama-model-loader`/`docling-model-loader` pull models from
  the network. A pilot site may not have outbound network access at all.
- **Acceptance criterion:** ingestion completes end to end (all staged
  models present, at least one document admitted `ready`) with the host's
  outbound network access disabled, using a media-carried bundle with a
  checksum manifest.
- **Dependency:** `[STAKEHOLDER: does the pilot site have any outbound
  network access at all, even intermittent, for staging?]`
- **Proposed owner role:** operator (bundle preparation); agency IT
  (transport to an air-gapped site, if required).
- **Risk if omitted:** a pilot site without outbound access cannot stage
  models at all, blocking deployment outright.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`docs/PILOT_PLAN.md` "Must fix before pilot" item
  3).

### PB-005 — Runner-side retrieval probe

- **Reason:** `ADR-014`'s evaluation gate uses a count-based tolerance
  (`N = 47` of 50) because the evaluation runner records no retrieval
  score, similarity, or distance for any case — only final citations. This
  makes it impossible to confirm *why* a drill and a release evaluation
  disagree on a case.
- **Acceptance criterion:** `cases.jsonl` records, per case, the retrieved
  chunk IDs and similarity scores actually returned by the retriever,
  cross-checked against the answer's own citations as a consistency check.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** `ADR-014`'s intended successor criterion ("every
  differing case must show a different retrieved chunk set") stays
  unreachable, and the pilot's own drills at 100-document scale inherit the
  same count-based tolerance with no way to confirm its mechanism.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`docs/PILOT_PLAN.md` "Must fix before pilot" item
  4, cited by `evaluation/M13_FINDINGS.md` line 156 and
  `docs/adr/014-release-drill-evaluation-gate.md` Sections 2 and 4).

### PB-006 — Scripted drill

- **Reason:** every from-scratch drill through Milestone 13 has been run by
  hand against `docs/DOST_DEMO.md` Section 10, which is how Milestone 13
  round 7's own audit found a real gap (intake staging) only after a drill
  had already improvised past it. A script that *is* the procedure cannot
  drift silently.
- **Acceptance criterion:** `scripts/drill.sh` (or `make drill RC=<sha>`)
  executes `docs/DOST_DEMO.md` Section 10 top to bottom against a given
  commit, with per-stage start/end markers, and exits non-zero — not
  silently substituting a workaround — on any step that cannot complete as
  scripted.
- **Dependency:** `PB-002`, `PB-003` (the script should encode whichever
  retry/entrypoint behavior is current once those land, not the pre-fix
  procedure).
- **Proposed owner role:** operator.
- **Risk if omitted:** procedure drift between what `docs/DOST_DEMO.md`
  Section 10 says and what an operator actually runs goes undetected until
  the next manual audit, at 100-document scale where a manual re-typed drill
  is materially more error-prone and slower than at nine documents.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`docs/PILOT_PLAN.md` "Must fix before pilot" item
  5).

### PB-007 — Decide `KND-M5-UN-002`: fix, guard, or disclose

- **Reason:** the sole false positive across every gold evaluation this
  project has run — a confident, citation-backed `supported` answer to a
  currentness question the corpus cannot answer as of the asked date
  (`CLAUDE.md` "Current state"; `docs/DOST_DEMO.md` Section 4, item 3). For
  a legal-document product entering a real pilot, this is a decision the
  project must make deliberately, not carry forward unexamined.
- **Acceptance criterion:** a committed record (an ADR or equivalent)
  states whether `KND-M5-UN-002`'s failure mode is fixed, mechanically
  guarded (the system abstains instead), or remains a disclosed limitation
  with the corpus-bounded reasoning stated — and, if disclosed, exactly how
  the pilot UAT/training (Priorities 12–13) communicates it to agency
  reviewers.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** a pilot agency reviewer relies on a confident wrong
  answer about whether a regulation is currently in effect — the exact harm
  `docs/THREAT_MODEL.md` TM-19 names as highest-severity.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`CLAUDE.md`, `evaluation/M13_FINDINGS.md` Section
  7, `docs/DOST_DEMO.md` Section 4 item 3).

### PB-008 — Fact-incompleteness detection/mitigation mechanism

- **Reason:** the system can return a `supported`, correctly cited answer
  that omits a required fact (`KND-M5-CD-005`, `KND-M5-DF-005`), introduced
  by labeled rendering (`ADR-012`) and not machine-enforced anywhere in the
  verification contract (`ADR-012` Section 4).
- **Acceptance criterion:** a documented mechanism — automated check or a
  mandatory reviewer checklist step — that flags a supported answer's
  fact-completeness against its case's expected facts before the answer
  reaches a pilot user, or an explicit decision that this remains
  human-review-only with the reasoning recorded.
- **Dependency:** `ADR-012`.
- **Proposed owner role:** operator.
- **Risk if omitted:** an agency reviewer receives a correctly cited but
  incomplete answer and reasonably treats it as complete, since nothing
  flags the omission.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`ADR-012` Section 4; `evaluation/M13_FINDINGS.md`
  Section 7; `docs/DOST_DEMO.md` Section 4 item 6).

### PB-009 — Ingest fails closed on an unknown source revision

- **Reason:** an unset `KENDRA_SOURCE_REVISION` currently resolves to the
  literal `"unknown"` rather than failing the ingestion outright
  (`evaluation/M13_FINDINGS.md` Section 7).
- **Acceptance criterion:** a new test asserts that ingestion refuses to
  proceed (rather than recording `"unknown"`) when `KENDRA_SOURCE_REVISION`
  is unset; `make test-full` passes with the new test included.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** at 100-document scale, a misconfigured pilot
  deployment could silently admit an entire corpus with unresolvable
  pipeline provenance, discovered only later, if at all.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`evaluation/M13_FINDINGS.md` Section 7).

### PB-010 — Expert review of the gold set (existing 50 + new 130)

- **Reason:** `evaluation/gold_cases.json`'s `dataset_status:
  initial_expert_review_required` has never changed — every accuracy figure
  this project has ever reported is measured against a candidate dataset,
  not a reviewed benchmark. A pilot reports numbers from 130 new cases on
  top of this same unreviewed foundation unless review happens first.
- **Acceptance criterion:** `docs/EVALUATION_METHOD.md`'s "Human review and
  gold-set promotion" procedure is completed over all 180 cases (130 new +
  50 existing) — two independent reviewers, at least one with domain
  competence, disagreements recorded and adjudicated in Git — and
  `dataset_status` changes to reflect it, with inter-reviewer agreement
  reported.
- **Dependency:** `PB-014`, `PB-015` (the 130 new cases must exist before
  they can be reviewed).
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** every pilot accuracy, false-answer-rate, or
  misclassification number reported is measured against an unreviewed
  dataset — exactly the caveat `docs/PILOT_PLAN.md` Part B Section 5
  already states must not be silently dropped.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (`evaluation/gold_cases.json`'s own
  `dataset_status`; `docs/EVALUATION_METHOD.md`; `docs/PILOT_PLAN.md` Part B
  Section 5).

### PB-011 — Qualify and document the pilot agency

- **Reason:** no pilot agency is named anywhere in this repository
  (`docs/PILOT_PLAN.md` Priority 1).
- **Acceptance criterion:** a committed document names the agency and shows
  it meets the three qualification criteria in `docs/PILOT_PLAN.md`
  Priority 1 (document volume, question volume, an owner with dual
  authority).
- **Dependency:** `[STAKEHOLDER: which agency will serve as the pilot
  partner?]`
- **Proposed owner role:** operator.
- **Risk if omitted:** every downstream priority (corpus sourcing,
  question authoring, roles, PIA) has no real subject to validate against.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: operator + the candidate agency's
  own leadership.

### PB-012 — Identify and document the agency problem owner

- **Reason:** no agency problem owner is named anywhere in this repository
  (`docs/PILOT_PLAN.md` Priority 2).
- **Acceptance criterion:** a committed document names the owner with a
  written delegation (or equivalent confirmation) of authority over both
  the corpus and the staff who will use the system.
- **Dependency:** `PB-011`.
- **Proposed owner role:** operator.
- **Risk if omitted:** no accountable decision-maker exists for go/no-go,
  corpus release, or staff time commitments — `docs/OPEN_QUESTIONS.md`
  Section 8 item 1's pilot-blocker condition stays unmet.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner (self-
  confirming, once identified) + operator.

### PB-013 — Source ≥100 representative agency documents

- **Reason:** the current corpus is nine documents; the pilot target is
  ≥100 (`docs/PILOT_PLAN.md` Priority 3).
- **Acceptance criterion:** ≥100 documents admitted with
  `processing_state = 'ready'`, under a signed agency document-provision
  agreement, verified by `SELECT count(*) FROM document_versions WHERE
  processing_state = 'ready';` returning ≥100.
- **Dependency:** `PB-011`, `PB-012`, `PB-002`, `PB-003`.
- **Proposed owner role:** agency problem owner.
- **Risk if omitted:** Priorities 4–5's question authoring and Priority 14's
  baseline study have no real corpus to run against.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner (source and
  approve the documents).

### PB-014 — Author and freeze 100 answerable evaluation questions

- **Reason:** the current gold set has 40 `supported` cases total; the
  pilot target is 100 answerable questions on the pilot's own corpus
  (`docs/PILOT_PLAN.md` Priority 4).
- **Acceptance criterion:** 100 answerable cases committed to a pilot
  gold-case file matching `evaluation/gold_cases.json`'s schema.
- **Dependency:** `PB-013`.
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** no representative evaluation set exists for the
  pilot corpus; Priority 14's accuracy comparison has nothing pilot-scale
  to measure.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: `[STAKEHOLDER: who from the agency
  will author or co-author these questions, with what domain competence?]`

### PB-015 — Author and freeze 30 unsupported evaluation questions

- **Reason:** the current gold set has 10 `unsupported` cases; the pilot
  target is 30 on the pilot's own corpus (`docs/PILOT_PLAN.md` Priority 5).
- **Acceptance criterion:** 30 unsupported cases committed to the same
  pilot gold-case file, each independently confirmed genuinely unanswerable
  from the pilot corpus (not merely unasked).
- **Dependency:** `PB-013`.
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** the unsupported false-answer-rate gate (Part B
  Section 2.1) has no pilot-scale denominator, and constructing a
  genuinely-unanswerable question against a real corpus without expert
  input risks accidentally constructing an answerable one.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: same as `PB-014`.

### PB-016 — Authentication and role-based access control

- **Reason:** no user-facing authentication exists in the code today (only
  Qdrant's internal `qdrant_api_key`) and the current safety boundary is
  policy, not a technical control (`docs/PILOT_PLAN.md` Priority 6).
- **Acceptance criterion:** an authenticated request without valid
  credentials receives `401`/`403` from every question-answering and
  document-management endpoint, verified by an integration test; each
  proposed role's permitted actions match a committed role table.
- **Dependency:** `ADR-011` (precedent for widening the frozen API surface);
  `[STAKEHOLDER: which roles and boundaries does the agency actually
  require?]`
- **Proposed owner role:** operator.
- **Risk if omitted:** real agency documents cannot be ingested under the
  current safety boundary at all (`README.md` "Safety boundary"), and any
  pilot handling real agency material without authentication exposes every
  document to anything able to reach the loopback port.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED need (code fact — no auth exists); ASSUMPTION on
  exact role design — validated by: agency problem owner + agency's
  privacy/security function.

### PB-017 — Extend audit trail to admission, supersession, and administrative actions

- **Reason:** `question_audit`'s hash chain covers only `answer`/
  `retrieval_only`/`evaluation` modes today; document admission,
  supersession, and administrative actions write no audit row at all
  (`docs/PILOT_PLAN.md` Priority 7; `docs/DATA_GOVERNANCE.md` Section 8's
  required event classes).
- **Acceptance criterion:** an extended audit mechanism (or an additional
  hash-chained table with the same append-only guarantee) records the event
  classes in `docs/DATA_GOVERNANCE.md` Section 8; `scripts/verify_audit_chain.py`
  (or an extended equivalent) verifies all of them, not just
  `question_audit`.
- **Dependency:** `PB-018` (supersession semantics must be decided before
  the supersession audit row's fields can be designed).
- **Proposed owner role:** operator.
- **Risk if omitted:** `docs/DATA_GOVERNANCE.md` Section 8's audit
  requirement — "who did what, to which document/version, when... with what
  result and reason" — is unmet for every action except asking a question,
  undermining the pilot's own accountability story.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED (code fact — audit sink wired only through
  answering + evaluation; `docs/DATA_GOVERNANCE.md` Section 8).

### PB-018 — Decide document-supersession semantics

- **Reason:** `document_versions` has no `supersedes`/`superseded_by`
  column or logic today; `docs/DATA_GOVERNANCE.md` Section 4.2 specifies
  the target governed-metadata model as policy only
  (`docs/PILOT_PLAN.md` Priority 8).
- **Acceptance criterion:** a committed record (an ADR or equivalent) is
  Accepted, answering: whether a superseded version remains citable; what a
  supersession audit row records (old/new version, actor, authority); and
  who is authorized to mark a version superseded.
- **Dependency:** None.
- **Proposed owner role:** operator (drafts, with agency records-custodian
  input required per `docs/DATA_GOVERNANCE.md` Section 2).
- **Risk if omitted:** a real agency corpus of ≥100 documents plausibly
  contains superseded regulations; without a decision, the system either
  silently treats every version as equally current (a `docs/DATA_GOVERNANCE.md`
  Section 4.3 violation) or has no way to represent supersession at all.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED need (code fact — no supersession schema exists);
  the answers themselves are open questions per `docs/PILOT_PLAN.md`
  Priority 8, validated by: agency problem owner + agency records
  custodian.

### PB-019 — Backup/restore procedure design and first restore-from-backup test

- **Reason:** no backup-and-restore-from-backup capability exists; the
  existing from-scratch drill (`docs/DOST_DEMO.md` Section 10) rebuilds from
  source PDFs and Git, not from a backup artifact
  (`docs/PILOT_PLAN.md` Priority 9; `docs/DATA_GOVERNANCE.md` Section 7).
- **Acceptance criterion:** a restore is performed from a backup artifact
  (a PostgreSQL dump, a document-repository snapshot — not from original
  source bytes), and the restored deployment's audit-chain verification and
  citation resolution are confirmed to match pre-failure state, with
  wall-clock restore time recorded against the RPO/RTO target.
- **Dependency:** `PB-006` (the scripted drill is this test's seed, per
  `docs/PILOT_PLAN.md` Priority 9's design note); `[STAKEHOLDER: RPO/RTO
  targets]`.
- **Proposed owner role:** operator.
- **Risk if omitted:** `docs/DATA_GOVERNANCE.md` Section 9's "Backup restore
  fails" row stays a documented risk rather than a tested one — recoverability
  and RPO/RTO remain unproven, per that section's own language, for a
  deployment now holding a real agency's documents.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED need (`docs/DATA_GOVERNANCE.md` Section 7, 9);
  RPO/RTO numbers themselves are ASSUMPTION — validated by: agency problem
  owner.

### PB-020 — Privacy Impact Assessment under RA 10173

- **Reason:** `question_audit` stores question text verbatim with no delete
  path, and a real agency corpus may contain personal data
  (`docs/PILOT_PLAN.md` Priority 11).
- **Acceptance criterion:** a completed PIA document is committed under
  `docs/`, reviewed and signed by the agency's designated privacy/security
  function, before any real agency document is ingested — covering
  minimization, retention, and access as scoped in `docs/PILOT_PLAN.md`
  Priority 11.
- **Dependency:** `[STAKEHOLDER: does the candidate pilot corpus contain
  personal data as RA 10173 defines it, and if so which category?]`;
  `PB-011`.
- **Proposed owner role:** agency problem owner (may delegate to the
  agency's own Data Protection Officer function).
- **Risk if omitted:** real agency documents are ingested and audited
  without a privacy determination, a direct violation of
  `docs/DATA_GOVERNANCE.md` Section 5's baseline rule and RA 10173's
  purpose limitation and lawful-basis requirements (cited by name only,
  per this milestone's constraint).
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED need (legal requirement, code fact on verbatim
  audit storage); the corpus's actual personal-data content is ASSUMPTION —
  validated by: agency problem owner.

### PB-021 — UAT protocol design

- **Reason:** no UAT protocol exists (`docs/PILOT_PLAN.md` Priority 12).
- **Acceptance criterion:** a UAT protocol document is committed, with
  scripted tasks drawn from the pilot's authored questions and corpus, and
  pass/fail criteria per task.
- **Dependency:** `PB-013`, `PB-014`, `PB-015`.
- **Proposed owner role:** operator.
- **Risk if omitted:** the pilot has no structured way to confirm the
  system works for real agency tasks before staff rely on it operationally.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner (approves the
  protocol).

### PB-022 — Staff training program design

- **Reason:** no training plan exists (`docs/PILOT_PLAN.md` Priority 13).
- **Acceptance criterion:** a training plan document is committed,
  specifying audience, duration, and a post-training competency check
  covering at minimum the four skills listed in `docs/PILOT_PLAN.md`
  Priority 13.
- **Dependency:** `PB-016` (training covers the role-based interface).
- **Proposed owner role:** operator.
- **Risk if omitted:** staff use the system without knowing how to read a
  `supported`/`insufficient_evidence` result or when to escalate to human
  review — the TM-19 harm this project treats as highest-severity.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner.

### PB-023 — Baseline (without-Kendra) time/accuracy study design and measurement

- **Reason:** no time-to-answer figure, with or without Kendra, exists
  anywhere in this repository (`docs/PILOT_PLAN.md` Priority 14).
- **Acceptance criterion:** a without-Kendra baseline measurement report,
  recording time-to-answer and accuracy for the pilot's own task set using
  the pilot's own staff, is committed.
- **Dependency:** `PB-011`, `PB-012`, `PB-013`, `PB-014`, `PB-015`.
- **Proposed owner role:** operator (designs); agency reviewer (performs
  the measured tasks).
- **Risk if omitted:** Priority 14's improvement claim has no controlled
  comparison to measure against — an aggregate "faster" claim would be
  unverifiable.
- **Target phase:** Required before pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner (approves the
  study design).

### PB-024 — Scale ADR-007, ADR-014, and the drill procedure to a 100-document corpus

- **Reason:** `ADR-007`'s extraction policy and `ADR-014`'s evaluation gate
  have only ever been exercised against nine documents; a 100-document
  corpus is the first real test of whether either generalizes
  (`docs/PILOT_PLAN.md` Priorities 3–5).
- **Acceptance criterion:** a report is committed showing the scripted
  drill (`PB-006`) run successfully end to end against the full ≥100-
  document pilot corpus, with chunk counts, ingest time, and model-staging
  time actually measured (not the linear extrapolation in
  `docs/PILOT_PLAN.md` Priorities 3–5) and `ADR-014`'s deployment gate
  checked against the pilot corpus's own values.
- **Dependency:** `PB-013`, `PB-002`, `PB-006`.
- **Proposed owner role:** operator.
- **Risk if omitted:** the pilot deploys on an extraction policy and
  evaluation gate never tested past nine documents, with no measured
  ingest-time or conflict-rate figure at real scale.
- **Target phase:** Required before pilot.
- **Status:** CONFIRMED need (`ADR-007` Section 8's own "corpus
  under-sampling" open item; `docs/PILOT_PLAN.md` Priorities 3–5).

---

## Required during pilot

### PB-025 — Revisit `ADR-014`'s `N = 47` at three index-rebuild drills

- **Reason:** `ADR-014` Section 2 states `N` is provisional and is
  revisited once three index-rebuild drills exist on record; two exist
  today (`M13.4-recovery-drill`, `M13.6-recovery-drill`)
  (`evaluation/M13_FINDINGS.md` Section 7).
- **Acceptance criterion:** once a third index-rebuild drill exists (either
  from `PB-024`'s pilot-corpus drill or a subsequent one), a report is
  filed revisiting `N` per `ADR-014` Section 2's own text.
- **Dependency:** `PB-024` (supplies a third drill data point, if it is a
  genuine index rebuild).
- **Proposed owner role:** operator.
- **Risk if omitted:** the evaluation gate's tolerance stays permanently
  anchored to a single historical observation, unrevisited despite the
  ADR's own text requiring reconsideration.
- **Target phase:** Required during pilot.
- **Status:** CONFIRMED (`docs/adr/014-release-drill-evaluation-gate.md`
  Section 2, item 4; `evaluation/M13_FINDINGS.md` Section 7).

### PB-026 — Answer-model artifact/version provenance investigation

- **Reason:** `pipeline_revision` records the ingestion pipeline's commit,
  but nothing records which exact answer-model artifact (beyond its name,
  `qwen2.5:7b-instruct`) produced a given answering run — not investigated
  in Milestone 13, no committed document addresses it
  (`evaluation/M13_FINDINGS.md` Section 7).
- **Acceptance criterion:** a committed document either records a mechanism
  that captures the exact answer-model artifact per run, or explicitly
  states this remains unresolved with a stated reason and follow-up owner.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** a pilot answer's full provenance chain — what code,
  what model artifact, what evidence — cannot be reconstructed for audit or
  incident investigation beyond the model's name.
- **Target phase:** Required during pilot.
- **Status:** CONFIRMED (`evaluation/M13_FINDINGS.md` Section 7 — explicit,
  not previously captured in a required-item list, included here per the
  no-drop rule).

### PB-027 — With-Kendra baseline measurement

- **Reason:** completes the controlled comparison `PB-023` starts
  (`docs/PILOT_PLAN.md` Priority 14).
- **Acceptance criterion:** a with-Kendra measurement report, using the
  same tasks and the same staff as `PB-023`'s baseline, is committed.
- **Dependency:** `PB-023`.
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** no evidence-based improvement claim can be made for
  the pilot; any "faster" or "more accurate" statement stays an assertion.
- **Target phase:** Required during pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner (confirms the
  measurement conditions match `PB-023`'s).

### PB-028 — UAT execution and sign-off

- **Reason:** `PB-021` designs the protocol; it must actually run and be
  signed before staff rely on the system operationally
  (`docs/PILOT_PLAN.md` Priority 12).
- **Acceptance criterion:** a signed UAT sign-off sheet from the agency
  reviewer role, referencing `PB-021`'s protocol and recording pass/fail per
  task.
- **Dependency:** `PB-021`.
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** no documented confirmation the system works for real
  agency tasks exists before or during the pilot.
- **Target phase:** Required during pilot.
- **Status:** ASSUMPTION — validated by: agency reviewer (signs) + agency
  problem owner (accepts the result).

### PB-029 — Staff training delivery and competency confirmation

- **Reason:** `PB-022` designs the plan; delivery and confirmation must
  actually happen (`docs/PILOT_PLAN.md` Priority 13).
- **Acceptance criterion:** a training log naming attendees, dates, and
  confirmed competency-check results (per `PB-022`'s design) is committed.
- **Dependency:** `PB-022`.
- **Proposed owner role:** operator (delivers); agency reviewer (attends,
  confirms competency).
- **Risk if omitted:** staff use the system without confirmed competency —
  same risk as `PB-022` but at the execution stage.
- **Target phase:** Required during pilot.
- **Status:** ASSUMPTION — validated by: agency problem owner.

### PB-030 — Ongoing audit-chain verification and stop-condition monitoring at pilot scale

- **Reason:** `docs/PILOT_PLAN.md` Part B Section 2.3 requires
  `make verify-chain` (or its pilot-scale/extended equivalent per `PB-017`)
  `PASS` before and after every pilot session, not only once at setup.
- **Acceptance criterion:** a log of verification runs (`PASS`/`FAIL`,
  timestamp, session) is maintained for every pilot evaluation or
  interactive session.
- **Dependency:** `PB-017`.
- **Proposed owner role:** operator.
- **Risk if omitted:** `docs/PILOT_PLAN.md` Part B Section 4's automatic
  stop condition (a `FAIL` result) could go unchecked during an actual
  pilot session, defeating the entire point of the gate.
- **Target phase:** Required during pilot.
- **Status:** CONFIRMED (`docs/PILOT_PLAN.md` Part B Section 2.3, already
  an existing gate this backlog item operationalizes at pilot scale).

### PB-031 — Continued human fact-review / fact-incompleteness monitoring on the pilot corpus

- **Reason:** `PB-008` designs a detection mechanism; findings from it (or
  from ordinary human review) need an ongoing record during the pilot,
  since the defect class is confirmed not rare, bounded, or fully
  characterized (`ADR-012` Section 6).
- **Acceptance criterion:** a running log of fact-incompleteness findings
  from continued human review, cross-referenced to case IDs, is maintained
  for the duration of the pilot.
- **Dependency:** `PB-008`.
- **Proposed owner role:** agency reviewer.
- **Risk if omitted:** the fact-incompleteness defect class (Priority 12–13
  training notwithstanding) goes unmonitored once the pilot is live, and a
  new instance is indistinguishable from an already-known one without a
  record.
- **Target phase:** Required during pilot.
- **Status:** CONFIRMED (`ADR-012` Section 6; `docs/DOST_DEMO.md` Section 4
  item 6).

---

## Required before production

### PB-032 — NAS deployment migration

- **Reason:** `docs/DATA_GOVERNANCE.md` Section 6.1 requires agency
  approval of NAS ownership, network location, access mapping, encryption,
  snapshot/backup behavior, failure behavior, monitoring, recovery test,
  and rollback plan before migration; none of this exists today
  (`docs/PILOT_PLAN.md` Priority 10).
- **Acceptance criterion:** a NAS deployment design document is committed,
  and on migration, `docker compose --env-file <nas-env> config --quiet`
  validates against the NAS-backed configuration with all services
  reporting `healthy`.
- **Dependency:** `[STAKEHOLDER: NAS ownership, network/physical location,
  and access mapping approved by the agency]`.
- **Proposed owner role:** agency IT.
- **Risk if omitted:** production reliance on local appliance storage alone
  has no documented failover, and any future NAS move happens without the
  agency-approved governance `docs/DATA_GOVERNANCE.md` Section 6.1 requires.
- **Target phase:** Required before production.
- **Status:** CONFIRMED need (`docs/DATA_GOVERNANCE.md` Section 6.1);
  design details are ASSUMPTION — validated by: agency IT + agency problem
  owner.

### PB-033 — Resolve remaining `docs/DATA_GOVERNANCE.md` AGENCY DECISION REQUIRED items

- **Reason:** role mapping to real positions (Section 2), retention
  schedules and RPO/RTO (Section 7), and PII classification (Section 5)
  remain open in the governance baseline; a pilot can proceed under
  documented interim assumptions (this backlog's before-pilot items), but
  production reliance requires the agency's own final decisions.
- **Acceptance criterion:** every **AGENCY DECISION REQUIRED** marker in
  `docs/DATA_GOVERNANCE.md` has a recorded decision (not an interim
  assumption) before production reliance.
- **Dependency:** `PB-011`, `PB-012`, `PB-020`.
- **Proposed owner role:** agency problem owner.
- **Risk if omitted:** production operation continues on pilot-stage
  interim assumptions indefinitely, without the accountable agency sign-off
  `docs/DATA_GOVERNANCE.md` Section 10 requires before production.
- **Target phase:** Required before production.
- **Status:** CONFIRMED (`docs/DATA_GOVERNANCE.md` Sections 2, 5, 7, 10).

### PB-034 — `ADR-011` acceptance decision, or an analogous auth-surface unfreeze record

- **Reason:** `docs/PILOT_PLAN.md` Priority 6 notes that authentication
  widens the frozen API surface the same way `ADR-011`'s upload/modes/score
  proposals do, and needs the same specification-unfreeze procedure
  (`MVP_SPEC.md` Section 11) whether or not `ADR-011` itself is accepted.
- **Acceptance criterion:** an ADR (either `ADR-011` itself, or a new
  authentication-specific record following its procedure) is drafted and
  Accepted before any authentication-driven change to the frozen API
  surface ships to production.
- **Dependency:** `PB-016`, `ADR-011`.
- **Proposed owner role:** operator.
- **Risk if omitted:** the authentication implementation ships as an
  undocumented, unreviewed widening of a specification this project's own
  process treats as requiring explicit unfreeze.
- **Target phase:** Required before production.
- **Status:** CONFIRMED (`docs/adr/011-interface-surface-unfreeze.md`;
  `MVP_SPEC.md` Section 11).

### PB-035 — Production authentication/authorization security review

- **Reason:** `PB-016` implements pilot-scope RBAC; production reliance on
  real agency documents warrants an independent security review of that
  implementation before it is trusted beyond a supervised pilot.
- **Acceptance criterion:** a security review of the production
  authentication/authorization implementation is completed and committed.
- **Dependency:** `PB-016`.
- **Proposed owner role:** external.
- **Risk if omitted:** an unreviewed authentication implementation is the
  sole control preventing unauthorized access to real agency documents in
  production.
- **Target phase:** Required before production.
- **Status:** ASSUMPTION — validated by: agency problem owner (commissions
  the review) + external reviewer.

---

## Explicitly deferred

### PB-036 — Main stack's `'unversioned'` provenance rows

- **Reason:** the demonstration stack's nine indexed documents all carry
  `pipeline_revision = 'unversioned'` — a literal `Settings` class default
  from Milestone 9, removed when Milestone 12 introduced real revision
  stamping via `resolve_source_revision()`. Current code cannot itself
  produce this value (`docs/DOST_DEMO.md` Section 8;
  `evaluation/M13_FINDINGS.md` Section 7).
- **Acceptance criterion (were this ever undeferred):** the nine main-stack
  documents are re-ingested under current code, which stamps a real commit
  rather than `'unversioned'`.
- **Dependency:** None.
- **Proposed owner role:** operator.
- **Risk if omitted:** the main dev stack's own index remains not fully
  provenance-stamped indefinitely — but this is the demonstration/dev
  stack, not the pilot deployment. A pilot's own fresh ingestion under
  current code cannot reproduce this defect (`docs/DOST_DEMO.md` Section 8
  confirms current code always stamps a real revision).
- **Target phase:** Explicitly deferred.
- **Status:** CONFIRMED (code fact, cited sources above).
- **Reason for deferral:** fixing this touches the main dev stack, which
  standing rule 4 of this milestone prohibits rebuilding, evaluating, or
  otherwise touching. It also has no bearing on pilot readiness — a pilot
  ingests fresh documents under current code, which already stamps
  provenance correctly, so this defect cannot recur in a pilot deployment.
  Recorded here per `evaluation/M13_FINDINGS.md` Section 7's no-drop rule,
  not silently omitted.
