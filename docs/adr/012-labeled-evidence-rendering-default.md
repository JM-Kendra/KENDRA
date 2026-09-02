# ADR-012: Adopt labeled evidence rendering as the default

**Status:** Accepted 2026-09-02.
**Amends:** the default value of `KENDRA_EVIDENCE_RENDERING`
(`apps/api/src/kendra_api/config.py`, wired through
`apps/api/src/kendra_api/answering/model_client.py` and
`docker-compose.yml`), introduced by EXP-13. No other answering behavior
changes — `SYSTEM_INSTRUCTION`, `_run_pipeline`'s gate logic, retrieval, and
the answering contract in ADR-003 are all untouched.
**Related:** `docs/experiment-decisions/EXP-13-preregistration.md` (frozen
2026-09-02); `evaluation/M12_FINDINGS.md` parts (g) and (h);
`evaluation/runs/EXP-13/20260902T005308Z-35770ed8/exp13_summary.md`.

## 1. Decision

**`KENDRA_EVIDENCE_RENDERING`'s default flips from `current` to `labeled`.**
`render_evidence_with_labels()` (EXP-13's `R1_LABELED`) becomes what a newly
deployed or freshly configured instance uses unless an operator explicitly
sets `KENDRA_EVIDENCE_RENDERING=current`. `render_evidence()` (the prior
default, `current`) is not removed, not deprecated, and remains fully
implemented and tested — only which one runs *by default* changes. No other
behavior changes: `SYSTEM_INSTRUCTION` is byte-identical, the answering
gate's admission and citation-construction logic is untouched, and the
answer model remains `qwen2.5:7b-instruct`.

## 2. Evidence

`docs/experiment-decisions/EXP-13-preregistration.md`'s frozen Section 8
decision rule required `R1_LABELED` to answer at least 5 of 6 qualified
cases, with zero label leaks and zero non-regression failures, to support
the experiment's own hypothesis. The run
(`evaluation/runs/EXP-13/20260902T005308Z-35770ed8/`) did not meet that bar:
**2 of 6 credited** (`KND-M5-DF-009`, `KND-M5-DF-020` — fact-complete;
`KND-M5-CD-005` and `KND-M5-DF-005` went from abstained to `supported` and
cited but are fact-incomplete, recorded as new defects per Section 7, not
credited; `KND-M5-CD-004` and `KND-M5-DF-008` remained abstained).

This decision does not rest on that threshold. It rests on the run's other,
unconditional measurements:

- **Full-set live classification accuracy: `0.72` → `0.82`.** The M12 clean
  baseline run (`evaluation/runs/M12-gold/20260831T125331Z-0bcc9dd7/report.json`,
  unlabeled rendering, `B0_BASELINE`) scored `0.72` accuracy on the full
  50-case gold set. EXP-13's live non-regression run under `R1_LABELED`
  (`evaluation/runs/EXP-13/nonregression/20260902T005308Z-35770ed8/report.json`)
  scored `0.82` on the same 50 cases, same model, same retrieval
  configuration — verified directly from both `report.json` files, not
  estimated.
- **Zero regressions** on the 37-case non-regression set (10
  `deliberately_unsupported` + 27 other gold cases, the corrected figure
  from `EXP-11-preregistration.md`'s 2026-09-01 erratum) — every previously-
  correct case retained its classification and `response_status` exactly.
- **Zero label leaks** in all 18 frozen-packet trials and spot-checked in the
  live run — no claim echoed a filename or a `"page N"` reference from
  `R1_LABELED`'s added rendering.
- **Zero flips** across all 3 trials, in both arms, for all 6 qualified
  cases — the comparison itself was not decided by nondeterminism.

## 3. This is a product decision, not an experimental pass — stated plainly

**`EXP-13`'s frozen verdict stands unaltered: the hypothesis it registered
("does labeling let the model answer at least 5 of 6 previously-abstained
cases") is NOT supported, and this ADR does not revise, soften, or
retroactively credit that result.** `EXP-13-preregistration.md` Section 8 is
frozen text; it is not reworded here, and its "not supported" outcome is not
disputed. What changed is the *decision being made*: EXP-13 asked a narrow
question about a specific, small case set, under a specific stringent bar
(all three trials, every fact present, zero leaks — Amendment A2's own
standard, imported into EXP-13 unmodified). This ADR asks a different,
broader question — does labeling improve the deployment on net, across the
whole gold set, without cost — and answers it from the same run's other
measurements, which the experiment's own frozen scope did not gate a
decision on either way (Section 8's closing text: *"This is not an
authorization to change `render_evidence()` in production either way... that
remains a separate decision requiring its own review"*). This ADR is that
separate review. It is deliberately not disguised as EXP-13 passing.

## 4. New known defect class: fact-incomplete supported answers

Adopting `labeled` rendering introduces a defect class that did not exist,
because it could not occur, under `current` rendering: **a `supported`,
correctly cited answer that omits one or more of a case's required facts.**
Two confirmed instances, both from the same EXP-13 run:

- **`KND-M5-CD-005`** — claim states the matching fine (PhP 1,000–50,000)
  and imprisonment range (2–4 years) correctly, cited, but omits the third
  required fact ("Both cite Section 264(a) of the Tax Code"). **2 of 3
  facts.**
- **`KND-M5-DF-005`** — claim states the Certificate of Registration need
  not be replaced and retains validity, correctly, cited, but omits the
  third required fact ("Updating is necessary only when registration
  information other than the Registration Fee changes"). **2 of 3 facts.**

**Fact-completeness is not machine-enforced anywhere in this pipeline.**
`_run_pipeline`'s gate (`apps/api/src/kendra_api/answering/service.py`)
validates structure — every claim has non-empty text, every `evidence_id`
resolves to admitted evidence, citations are server-constructed — but has no
mechanism to check a claim against a case's full fact set; that check exists
today only as the human review `docs/EVALUATION_METHOD.md` and
`M12_FINDINGS.md` part (c) already require for atomic-fact scoring
generally. This defect class is therefore not detectable by the API itself
at answer time, only by the same downstream human/scored-worksheet review
this project already treats as authoritative over any mechanical scorer.
Recorded here so it is not mistaken for a new occurrence each time a
reviewer finds one — it is the known, expected shape of this rendering
change's own risk, not a surprise.

**`KND-M5-UN-002` persists unchanged.** The pre-existing, separately-tracked
temporal-boundary defect (`M12_FINDINGS.md` part (a)) returned `supported`
under both `current` and `labeled` rendering, identically. Adoption neither
fixes nor worsens it; it is not counted as a consequence of this decision
either way.

## 5. Consequences

- Every newly created or reset deployment answers with `render_evidence_with_labels()`'s
  output by default. An operator who needs the prior behavior sets
  `KENDRA_EVIDENCE_RENDERING=current` explicitly — the setting, both code
  paths, and every test for both remain in place.
- Reviewers scoring future gold-evaluation runs should expect and check for
  the fact-incompleteness pattern in Section 4, not just outright
  hallucination or citation errors, when reading `supported` answers.
- This does not touch `KENDRA_ANSWERING_ENABLED` (still `false` by default —
  Milestone 10 answering remains an unaccepted prototype per
  `docs/milestones/M12_STATUS.md`) and does not authorize enabling answering
  in any environment where it is currently off. It changes what a
  `labeled`-rendering-capable deployment does *if and when* answering is
  turned on, nothing about whether it should be.
- Does not affect `EXP-01`, `EXP-03`, `EXP-04`, or `EXP-11`'s own recorded
  outcome, and does not select `B1_LARGER`/a different answer model —
  orthogonal, per `EXP-13-preregistration.md`'s own Section 1/2.

## 6. What this record does not claim

It does not claim `R1_LABELED`'s frozen-packet hypothesis was actually
supported — Section 3 above is explicit that it was not. It does not claim
the fact-incompleteness defect class is rare, bounded, or fully
characterized — two instances from one run is not a rate. It does not
authorize skipping human fact-review on any future run; if anything, Section
4 raises the cost of skipping it. It does not change `MVP_SPEC.md`,
`ADR-003`, or any frozen answering contract text — the rendering function
selected is an internal implementation detail of the model-client seam
ADR-003 already treats as swappable, not a change to the contract itself.
