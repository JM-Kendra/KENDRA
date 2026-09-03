# ADR-014: The release-drill evaluation gate

**Status:** Accepted 2026-09-02 by the operator. **`N = 47`** (Section 2).
**Date drafted:** 2026-09-02
**Amends:** the informal gate used by every from-scratch drill since Milestone
13 round 3 (`source_revision == RC; accuracy 0.82; TP 32/FN 8/FP 1/TN 9;
chain PASS; zero drill resources; main stack untouched; clone gone`), never
itself written down as a preregistered decision record until now.
**Basis:** Milestone 13 round 6's Task 2 diagnostics (`v17.md`), and round 5's
drill failure (`v16.md`) that prompted them.

> **Gating.** This record sets a two-part criterion. The deployment gate
> (Section 2, first bullet) is exact and unchanged from what every prior round
> already required. The evaluation gate (Section 2, second bullet) sets a
> per-case agreement threshold, `N = 47` of 50. Round 7 runs against this
> ADR.

## 1. Context

Every from-scratch drill since round 3 has required the drill's gold
evaluation to reproduce the release evaluation's confusion matrix **exactly**:
same accuracy, same `TP`/`FN`/`FP`/`TN` counts, same sole false positive. This
was workable through round 4's drill (which never reached the evaluation
stage) and was not tested end-to-end until round 5.

Round 5's drill (`v16.md`) passed every deployment-mechanics check — fresh
clone, ownership fix, both models staged, all nine documents ingested `ready`
with zero `extraction_conflict` (this round's own central fix, ADR-007's
default, proven end-to-end) — then its gold evaluation returned `0.80`
(`TP 31/FN 9/FP 1/TN 9`) against the release eval's `0.82`
(`TP 32/FN 8/FP 1/TN 9`). Three cases differed: `KND-M5-CD-004` (release:
`unsupported`/wrong; drill: `supported`/correct — an improvement) and
`KND-M5-DF-005`, `KND-M5-DF-018` (release: `supported`/correct; drill:
`unsupported`/wrong — two regressions). The sole false positive
(`KND-M5-UN-002`) and the unsupported false-answer rate (`0.1`) were unchanged.
Per the round's own rule, this was treated as a gate failure: the drill
stopped, tore down, and reported, without a tag.

This was already a documented, accepted limitation, not a surprise in kind:
`docs/DOST_DEMO.md` Section 8, point 8 states plainly —

> Model output nondeterminism observed at temperature 0 with a fixed seed.
> `ANSWER_NUM_CTX`, `temperature: 0`, and `seed: 0` are all fixed
> (`apps/api/src/kendra_api/answering/model_client.py`), but temperature 0
> alone does not guarantee bit-identical generation run to run
> (`evaluation/M12_FINDINGS.md` part (f)); a fixed seed narrows this, it does
> not eliminate it.

(`evaluation/M12_FINDINGS.md` part (f) is itself a different, earlier
diagnostic — a pre-Stage-1 EXP-11 truncation/context-window check, not a
nondeterminism study in its own right; it is cited here only because
`docs/DOST_DEMO.md` cites it at that point. The nondeterminism claim itself
rests on `docs/DOST_DEMO.md` Section 8 point 8's own text and on
`EXP-11-preregistration.md` Amendment A2, Section 2 below.)

What was not known before this round is **where** the round-5 divergence came
from — whether the same generator, called again, simply produces a different
answer some fraction of the time (generator-side), or whether an
independently-built retrieval index returns different evidence for the same
questions even from identical source chunks (index-side). Round 6's Task 2
diagnostics answer this:

- **Task 2a (chunk-count parity):** all nine documents' `chunk_count` and
  `page_count`, queried from the main stack's database, match `v16.md`
  Stage 3's ingestion output values exactly, document for document. The
  drill's ingestion was not different from the release's at the
  chunk/page-count level.
- **Task 2c (generator repeatability on a fixed index):** two diagnostic gold
  evaluations run back-to-back against the main stack's own long-lived index,
  answering temporarily enabled, `--seed 0` both times, produced results
  **identical to each other and to the original release evaluation**:
  `0.82`, `TP 32/FN 8/FP 1/TN 9`, the same exact eight "other
  misclassifications," the same sole false positive. Zero per-case
  disagreement across all three runs, 50/50 cases, confirmed by direct
  per-case diff of `cases.jsonl`.

**Conclusion: `INDEX-SIDE`.** The generator is deterministic, on this
hardware, against a fixed index, with `--seed 0` — three independent runs
against the same index agree on every one of 50 cases. Round 5's divergence
therefore cannot be attributed to generator-call-to-generator-call variance;
it is a property of the freshly-built index differing from the release
index in some way that chunk/page counts alone do not capture (Task 2d
proposes, but does not run, the next diagnostic that would isolate this
further — whether two independently built indexes from identical chunks
themselves agree).

A gate that requires exact confusion-matrix reproduction between two
structurally different indexes — one long-lived, one freshly built at every
drill — was measuring something the deployment process does not actually
control for, and had never been examined until it failed.

## 2. Decision, structured as two gates

Every element of both gates below is `PASS` or `FAIL`; there is no third
outcome — an element that is only partially met (e.g. a provenance field
recorded one commit before the release candidate rather than at it) is
`FAIL`, not "caveated" or "not blocking" (`demo-dost-v1.3` reported such an
element as caveated; that was a misapplication of this ADR, corrected in
`docs/DOST_DEMO.md` Section 6.4's supersession note).

- **Deployment gate — exact, unchanged.** `source_revision` at the drill's
  `/api/v1/health` equals the release commit (RC); `make check-template`
  passes inside the fresh clone before any manual step; both documented
  models (`bge-m3`, `qwen2.5:7b-instruct`) are present in the drill's Ollama
  volume; all nine documents reach `ready` with per-document `chunk_count`
  and `page_count` equal to the release stack's own values (Task 2a's
  comparison, now made a standing gate element rather than a one-off
  diagnostic); `pipeline_revision` is stamped from the baked source revision
  and equals RC for all nine documents (Task 2e's fix has landed as of round
  6 — this clause is unconditional, not contingent); `/api/v1/health` reports
  `source_revision` equal to RC with no discrepancy, and the evaluation
  runner's own `report.json` records `source_revision_mismatch_overridden:
  false` (this is a field of the runner's preflight output, not of
  `/api/v1/health` — corrected here; the two were conflated in the first
  draft of this record); the drill's own audit chain verifies `PASS` at 50;
  zero drill-project containers/volumes/networks and no scratch clone remain
  after teardown.
- **Evaluation gate — per-case agreement.** The drill's per-case
  classification agrees with the release evaluation's on at least **`N = 47`
  of 50** cases; the sole false positive remains `KND-M5-UN-002` in both
  evaluations; the unsupported false-answer rate is unchanged between the two
  evaluations; **every** differing case is listed by ID, with its
  `expected_result`/predicted labels in both evaluations, in the round's
  report and in `docs/DOST_DEMO.md` Section 6.

  **Operator decision: N = 47.** (1) Three runs on a fixed index agreed on
  50/50 cases, so generator-side variance on this hardware is zero; the
  tolerance below exists solely for index-build variance, and any future
  disagreement between two evaluations of the *same* index fails the gate
  regardless of N. (2) The single index-rebuild observation on record is
  47/50. Setting N above it would fail the only drill that has reached this
  gate, so a pass in the next round would be luck rather than evidence;
  setting N below it has no data behind it. (3) The shape constraints carry
  the real weight: the sole false positive must remain `KND-M5-UN-002`, the
  unsupported false-answer rate must be unchanged, and every differing case
  is listed with both labels. A drill that loses supported cases to
  abstention within the band passes; a drill that gains a single new
  confident wrong answer fails at any N. (4) N equals one observation and is
  provisional: it is revisited once three index-rebuild drills exist, and it
  is expected to be superseded by a mechanism-based criterion (every
  differing case must show a different retrieved chunk set) once the
  evaluation runner records retrieval output — see Alternatives and
  `docs/PILOT_PLAN.md` item 4.

## 3. Disclosure

This ADR was drafted **after** one drill (round 5, `v16.md`) failed the
exact-reproduction gate then in force, at `0.80` accuracy against a required
`0.82`. The three differing cases were `KND-M5-CD-004` (newly correct in the
drill), `KND-M5-DF-005`, and `KND-M5-DF-018` (both newly incorrect in the
drill). This is disclosed here plainly, per the project's standing rule
against weakening a criterion after seeing the result it would otherwise
fail: **the band this ADR introduces applies from round 7 forward. No earlier
drill is re-graded, re-scored, or retroactively judged to have passed under
it.** Round 5's drill remains, in its own report, a recorded gate failure.

## 4. Alternatives considered

1. **Exact confusion-matrix reproduction (the status quo to date).**
   Rejected: it failed on the only index-rebuild drill run against it
   (round 5), on a run where the generator was independently ruled out as
   the cause (Task 2c: zero disagreements across three fixed-index runs) and
   the ingested chunk/page counts matched the release exactly (Task 2a). One
   failure with the generator eliminated is not proof the requirement can
   never be met — n=1 does not establish "not achievable," only that it is
   not reliably achievable on the evidence collected so far — but it is
   already enough to show the gate was measuring index-rebuild variance,
   an axis this project does not otherwise control for, while being labeled
   as a measure of deployment correctness. Continuing to require exact
   reproduction risks failing a correctly deployed drill on a day the index
   happens to land differently, for reasons unrelated to whether the
   deployment itself is correct.
2. **N-of-M trial agreement, per `EXP-11` Amendment A2.** A2 requires three
   independent trials of the *same* (case, arm) pair — same persisted
   evidence packet, same index — to unanimously agree before a case counts as
   answered; its purpose is to surface *generator*-call-to-call variance on a
   fixed evidence packet. Task 2c already established that this project's
   generator has zero observed call-to-call variance on a fixed index at
   `--seed 0` (0/50 disagreements across three runs) — A2's mechanism
   addresses a variance source Task 2 did not find, not the one it did. Not
   adopted for this gate for that reason; the analogous per-case repetition
   this record would need is repetition *across independently built indexes*
   (Task 2d's proposed procedure), not repetition of calls against one index.
3. **A numeric accuracy tolerance without per-case disclosure** (e.g., "within
   0.02 of the release accuracy"). Rejected: two evaluations can land on the
   same aggregate accuracy while disagreeing on entirely different cases (a
   tolerance band cannot distinguish "the same three cases moved" from "three
   different cases moved instead," which matters for judging whether a
   specific regression class is stable or churns randomly). The chosen
   design's per-case disclosure requirement exists specifically to keep this
   visible, matching this project's existing preference for per-case
   transparency (`misclassified_cases.md`, `docs/DOST_DEMO.md` Section 6)
   over aggregate-only reporting.
4. **Mechanism-based criterion: every differing case must show a different
   retrieved chunk set.** Rather than tolerating a count of disagreements,
   this would require that any case whose classification differs between the
   drill and release evaluations also show different top-k retrieval —
   directly confirming the mechanism (index-build variance) rather than
   inferring it from a count, and catching a disagreement caused by anything
   *other* than retrieval (a generator regression, a scoring bug) as a real
   failure regardless of how few cases it touches. **Not adopted yet: the
   evaluation runner records no retrieval score, similarity, or distance for
   any case** (round 6, `v17.md` Task 2b) — there is nothing to compare a
   differing case's retrieval against today. This is the intended successor
   to the `N = 47` count-based gate once that gap is closed; see
   `docs/PILOT_PLAN.md` item 4.
