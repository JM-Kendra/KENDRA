# Milestone 12 status — audit records and repeatable evaluation

**This is a preflight report, not a gate.** Prompt 12 asks the implementer to "confirm
M1–11 pass" before building. They do not. This document states exactly what is
missing, then M12 is built anyway, on the same terms as Milestone 10: **code presence
on this branch is not milestone acceptance.**

## What is missing

- **Milestone 10 (retrieval and question answering) is unaccepted.** `CLAUDE.md`
  states "Milestone 10: blocked. Retrieval and question answering must not be
  implemented," and separately "Currently at Milestone 9." Working answering code
  exists only on `prototype/milestone-10-verification-contract` — a prototype branch,
  never merged to `main`, never declared passing. M12's audit and evaluation code is
  built against that prototype's contract because there is nothing else to audit or
  evaluate; this does not make Milestone 10 accepted.
- **Milestone 11 is defined but has no implementation.** `ADR-011` (proposed, not
  accepted) covers its interface-surface unfreeze; `EXPERIMENT_PLAN.md`'s EXP-06
  names Milestone 11 as its execution milestone and prerequisite; and
  `KENDRA_MIGRATION_HANDOFF.md` §12 lays out its recommended starting point. None of
  that is a branch, a commit, or code — nothing has been built. (An earlier version
  of this document said Milestone 11 "does not exist," which overstated the gap:
  it is planned and undecided, not absent.)
- **EXP-01 is not passing.** The 2026-08-20 rerun under ADR-007 retained 41 of 41
  physical pages with zero unresolved conflicts, and 121 of 125 expected facts are
  now established after adjudication — but 4 remain held by a gold-case page-scoping
  defect and one material finding (MF-01, an OCR digit substitution) awaits a
  reviewer ruling. The decision rule treats this as inconclusive, and inconclusive is
  not a pass. See `docs/experiment-decisions/EXP-01.md`.
- **EXP-03 remains blocked.** It may not resume until EXP-01 passes, per the frozen
  decision rule. It has not been rerun.
- **The gold dataset (`kendra-bir-public-gold-v2`) is unapproved.** Its
  `dataset_status` is `initial_expert_review_required`. Nothing in M12 changes that
  field; every M12 report carries the status verbatim and sets `acceptance_claim:
  false` until the required independent review happens. A two-reviewer independent
  adjudication of the v2 correction now exists on `governance/m5-v2-adjudication`
  (commit `cacb266`) — `dataset_status` is unchanged there too, pending that branch's
  own acceptance; it has not been merged and does not change anything M12 reports.

## What M12 delivers

Given the above, M12 is scoped to infrastructure the eventual accepted system will
need regardless of when M10/EXP-01/EXP-03 close, built so it does not itself make any
claim about their status:

1. **Append-only audit records** (`question_audit`, Postgres, hash-chained,
   trigger-enforced against `UPDATE`/`DELETE`/`TRUNCATE`) for every call through
   `answer_question` — including the fail-closed defaults an unconfigured or
   unaccepted deployment already returns today. Answer text, claim text, evidence
   text, excerpts, prompts, model raw output, and model reasoning are structurally
   excluded: `AuditRecord` has no field that could hold them.
   `scripts/verify_audit_chain.py` recomputes the hash chain from row contents to
   detect tampering after the fact.
   **Known limitation, not closed by M12:** append-only is enforced against the
   application's own database role via triggers, not against the role that owns the
   table. That role (or anyone with equivalent privileges) can still
   `ALTER TABLE ... DISABLE TRIGGER` or drop the triggers outright — the hash chain
   would then detect the resulting inconsistency, but nothing prevents a
   sufficiently privileged actor from attempting it in the first place. Real
   role separation (a distinct, unprivileged application role with no DDL rights on
   `question_audit`) is an M14 item, since M14 is what actually depends on this
   audit trail being immutable end to end.
2. **One source-revision resolution path** (`KENDRA_SOURCE_REVISION` env var, else
   `git rev-parse HEAD`, else `"unknown"`) replacing the two previous placeholders
   (`pipeline_revision = "unversioned"`, `pipeline_git_revision = "0"*40"`).
   Consumed by audit, citations, and `/api/v1/health`.
3. **A gold-set evaluation runner** (`python -m kendra_api.evaluation.run`) that
   validates the dataset, preflights the live system (fail loud, never silently
   report 50 "unsupported" results against a system that was never ready), runs the
   protocol `docs/EVALUATION_METHOD.md` defines, and writes a run directory whose
   `report.json` aggregates are recomputable from the same directory's `cases.jsonl`.
   Atomic-fact and citation correctness require judging meaning, which the method
   says explicitly — those scores are computed as clearly labeled **provisional**
   approximations and are superseded only by a human-reviewed
   `scoring_worksheet.json` supplied via `--scored-worksheet`. Every report this
   milestone produces carries `acceptance_claim: false` with the open-gate reasons
   above, regardless of what the provisional numbers say.

## What would have to be true before either report could claim otherwise

- EXP-01 passes outright (not inconclusive) and EXP-03 is rerun and passes.
- Milestone 10 is reviewed and accepted on its own terms, on its own branch.
- The gold dataset completes the two-reviewer independent review
  `docs/EVALUATION_METHOD.md` requires and its `dataset_status` changes accordingly.
- A live evaluation run's `scoring_worksheet.json` is reviewed by a qualified human
  and supplied back via `--scored-worksheet`.

None of those happened as part of M12. This document exists so that a passing M12
test suite is never mistaken for any of them having happened.
