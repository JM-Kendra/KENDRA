# INC-001 — two ghost evaluation runs against the live API

**Date:** 2026-09-01. **Status:** closed, remediated. **Severity:** no data
integrity impact confirmed (hash chain verifies intact); a process/tooling
gap, not a security incident.

## What happened

While running EXP-11 Stage 1's non-regression check (the live, full-50-case
gold evaluation against `qwen2.5:14b-instruct` with answering enabled), the
evaluation runner (`kendra_api.evaluation.run`, invoked via a throwaway
`docker run` container) was started **three times**, not once:

1. **First attempt** failed immediately at dataset load with a `PermissionError`
   (the container's non-root user could not traverse the bind-mounted repo
   directory, `700` permissions) — no request ever reached the API. No audit
   impact.
2. **Second attempt** appeared to hang and was killed at the operating
   session's own tool-level **2-minute foreground timeout**. This was read as
   a failure at the time. It was not: the underlying `docker run` container
   (invoked without `--name` and without `-d`) kept running, detached from
   its now-dead foreground client, and completed the full 50-case run against
   the live API minutes later, entirely unobserved.
3. **Third attempt**, this time launched with `--name` and monitored properly
   in the background to completion, also ran the full 50-case set and was the
   one whose output files were actually captured
   (`evaluation_run_id eval-5fc7ff75-341b-4883-b301-3409c07f072d`).

The second attempt's completion was discovered only when
`question_audit`'s row count was checked before/after and came back **+150,
not the expected +50**. Querying `question_audit` directly by
`evaluation_run_id` recovered what had happened: two additional, real,
complete 50-case runs (`eval-91f92ac2-60b2-40fb-b867-bd83640e36dc` and
`eval-7623e3ca-211a-4835-9f2e-3c325e0e9fa3`) had executed against the live API
without ever being noticed as separate processes, one of them (`91f92ac2`)
overlapping in sequence range with the other (`7623e3ca`) — confirming they
ran concurrently, not merely back-to-back.

## Affected `question_audit` rows

| `evaluation_run_id` | `sequence` range | row count |
|---|---|---:|
| `eval-91f92ac2-60b2-40fb-b867-bd83640e36dc` | 101–160 | 50 |
| `eval-7623e3ca-211a-4835-9f2e-3c325e0e9fa3` | 140–200 | 50 |
| `eval-5fc7ff75-341b-4883-b301-3409c07f072d` (captured, not a ghost) | 201–250 | 50 |

**Combined affected range for the two ghost runs: `sequence` 101–200 (100
rows).** The overlap between 140–160 is real, not a query artifact — both
`evaluation_run_id`s appear within that sub-range, confirming the two
processes were interleaving live writes to the same table at the same time.

All three runs' aggregate results are identical (20 `insufficient_evidence` +
30 `supported` of 50 in each), which is why no answering-quality conclusion in
`evaluation/runs/EXP-11/stage1-20260901T120327Z-221e1bcd/` needed to be
revisited — the captured run is representative, not an outlier.

## Hash chain: verified intact from genesis

`question_audit`'s append-only hash chain
(`apps/api/src/kendra_api/audit/sink.py`) was verified directly against the
live table after the incident was discovered:

```
PASS: 250 records, chain verified from genesis
```

Every record from `sequence` 1 through 250 — including all 100 rows from the
two ghost runs — links correctly to its predecessor via `record_hash`/
`previous_record_hash`, recomputed from each record's own contents, not
merely read back. The two ghost runs and their interleaving did not corrupt,
skip, or duplicate any hash-chain link. Concurrent writes are serialized
safely by `PostgresAuditSink.write()`'s `pg_advisory_xact_lock` — this is
exactly why concurrent writers produced an intact, if interleaved, chain
rather than a broken one.

## Disposition: rows retained as legitimate records; no surviving run directory

**The 100 rows from the two ghost runs are retained in `question_audit`, as
legitimate records of real requests the API actually answered.** They are not
edited, flagged, or removed — `question_audit` has no `UPDATE`/`DELETE` path
by design, and these rows are not fabricated or erroneous data; they are true
records of two real evaluation runs that happened, which is precisely why an
append-only audit trail exists: to make an unnoticed process's own actions
discoverable after the fact, which is exactly what happened here.

**No run directory survives on disk for either ghost run.** Both ran inside
ephemeral `docker run --rm` containers with no host-mounted output directory
at the time; by the time their existence was discovered (via the audit-count
discrepancy), both containers had already exited and been removed by
`--rm`, taking their in-container `/tmp/out` contents with them. Their
`report.json`/`report.md`/`cases.jsonl`/etc. are permanently unrecoverable.
Only `evaluation_run_id eval-5fc7ff75-...`'s output was retrieved (via
`docker cp` before its container was removed) and is preserved at
`evaluation/runs/EXP-11/stage1-20260901T120327Z-221e1bcd/nonregression/`.

## Root cause

Two independent gaps compounded:

1. **No lock.** Nothing prevented — or even detected — a second invocation of
   the same runner while a first was still in flight.
2. **Output written only at completion, to an ephemeral location.** The
   runner's own `write_run_directory` (as it existed before this incident)
   produced no file at all until every case had finished, and this
   invocation's containers had no host-mounted output directory in the first
   place — so there was no way to notice an in-progress or completed-but-
   unretrieved run short of directly querying `question_audit`.

## Remediation (this round)

- **`RunLock`** (`apps/api/src/kendra_api/evaluation/lock.py`): a fixed-path
  lock file, acquired atomically (`O_CREAT|O_EXCL`) before any other work, that
  refuses a second invocation outright and is removed only on a clean
  (successful) exit — a crash or a kill leaves it in place, deliberately, so
  the next invocation's attempt surfaces the problem instead of proceeding.
- **Incremental output.** `run_config.json` and `cases.jsonl` are now written
  from the first line of the run (`initialize_run_directory`, before the first
  case is asked) and `cases.jsonl` is appended to as each case completes
  (`append_case_result`), not batched to a single write at the end.
- **A source-revision preflight** (`check_source_revision_matches_head`)
  refuses to run the live tier when `/api/v1/health`'s `source_revision`
  doesn't match `git rev-parse HEAD` at the checkout in use — unrelated to
  this incident's direct cause, but found and fixed in the same session (a
  stale baked revision was discovered on the api image used for this same
  Stage 1 round) and belongs alongside this hardening pass.

None of this remediation retroactively protects the two ghost runs recorded
here — it exists so this specific failure mode cannot recur silently.

## Registry link

See `docs/EXPERIMENT_REGISTRY.md`'s `EXP-11` row for the dated pointer to this
document.
