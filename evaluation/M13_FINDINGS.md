# Milestone 13 findings — demonstration release

**Status:** a summary of the demonstration-release milestone's own record —
tag history, from-scratch drills, and the determinism investigation that
followed the first drill failure. Every number below traces to a commit
hash, a run directory under `evaluation/runs/`, or a committed document
(`docs/adr/014-release-drill-evaluation-gate.md`, `docs/DOST_DEMO.md`,
`docs/PILOT_PLAN.md`); intermediate round reports are not cited, since they
are not tracked in this repository.

## 1. What Milestone 13 set out to do

A demonstration release with two properties neither prior milestone had
established: **proven from-scratch deployability** (a fresh clone of a
tagged commit, with no manual workaround, reaches a working, ingested,
answerable stack) and **an honest evaluation record** (a gold evaluation's
result is reproducible, or its non-reproducibility is measured and disclosed
rather than assumed away). Both properties turned out to require more than
one release to actually establish.

## 2. Releases cut and why each was superseded

**`demo-dost-v1`** (`903b10895d543bad337cabab97e7e1d8d1ea4690`). Predates the
`docker-compose.yml` `ingest`-service environment-passthrough fix: the
one-off ingestion command never received
`KENDRA_EXTRACTION_COMPLETENESS_POLICY`/`KENDRA_EXTRACTION_CANDIDATE_MINIMUM_AGREEMENT`
from `.env`, silently falling back to `Settings`' own stricter default and
failing three of nine documents with `extraction_conflict` on a fresh
ingest. Fixed by commit `4b09600` (added both variables to the `ingest`
service's `environment:` block), found during the drill recorded in
`docs/DOST_DEMO.md` §10 "Attempt 1" (`evaluation/runs/M13-recovery-drill/20260902T031954Z-ac0852bf/`).

**`demo-dost-v1.1`** (`6a671dee7df6d8fb263deb4a372f87c91d71816f`). Fixed
`v1`'s two `Attempt 1` bugs (the extraction-policy passthrough above, and an
ownership gap — `document-repository/{objects,manifests,.staging}` not
writable by the ingest container's non-root uid 999, initially patched with
a `chmod o+w` world-writable grant, commit `4b09600`, later replaced by an
ownership-based `chown` fix, commit `401d1b3`). But a from-tag drill against
the *pushed* `v1.1` tag itself — a fresh clone and checkout of the tag, not
the working tree — found a **third, different bug in the same ownership
family**: the `chown` command names three subdirectories
(`objects/`, `manifests/`, `.staging/`) that do not exist yet on a
genuinely fresh `document-repository/` (they are created lazily by
`LocalDocumentAdmissionStore.admit()` on first ingestion), so the fix had
only ever been exercised against a long-lived dev environment where those
subdirectories already existed. The drill stopped at this point, per its own
governing rule, rather than working around it — no Compose project was ever
brought up for that attempt. Fixed by commit `8c91cb4` (`mkdir -p` the three
subdirectories before `chown`), which post-dates the `v1.1` tag and — per
the standing rule against re-pointing a pushed tag — does not retroactively
make `v1.1` pass. `v1.1` was also missing the answer model in its documented
model-staging step: `ollama-model-loader` had, since its Milestone 9
introduction, only ever pulled `KENDRA_EMBEDDING_MODEL` (`bge-m3`); no
documented procedure staged `KENDRA_ANSWER_MODEL`
(`qwen2.5:7b-instruct`) at all. Fixed by commit `c9219c3`. And the
extraction-policy value itself was never actually adopted as the *tracked
default* — `.env.example`, `docker-compose.yml`'s `ingest`-service `:-`
fallback, and `Settings.extraction_completeness_policy`'s class default all
still carried the pre-`ADR-007` `native-page-token-coverage-v1` value,
distinct from the passthrough gap `v1`'s drill found. Fixed by commit
`733aaf0` (all three now match `docs/adr/007-native-primary-detection.md`
§2.3).

**`demo-dost-v1.2`** (`b82867291be1d12fb783b365c022ba90fb0f8587`). All of the
above fixed and, for the first time, confirmed **before** tagging rather
than discovered after: drilled from a fresh origin clone, top to bottom, per
`docs/DOST_DEMO.md` §10 exactly as written, then gated under `ADR-014`
(Section 5 below) alongside a release-gold-evaluation gate, both evaluated
at the same commit before the tag was created. Run directories:
`evaluation/runs/M13.6-recovery-drill/20260902T121128Z-b8286729/` (drill),
`evaluation/runs/M13.6-release/20260902T121848Z-b8286729/` (release).

## 3. The drill-before-tag sequence and the four deployment gaps it found

Four distinct deployment-mechanics gaps surfaced across the drills above,
in this order:

1. **Ownership** — two separate incidents. First, `document-repository/`
   subdirectories not writable by the ingest container's uid 999 on a
   freshly created host directory (found pre-`v1`, commit `4b09600`
   world-writable patch, superseded by commit `401d1b3`'s ownership-based
   fix). Second, the ownership fix itself assumed those subdirectories
   already existed, failing on a genuinely fresh directory (found by a
   from-tag drill against the pushed `v1.1` tag; fixed by commit `8c91cb4`,
   too late to retroactively pass that tag).
2. **Answer-model staging** — `ollama-model-loader` never pulled
   `KENDRA_ANSWER_MODEL`, only `KENDRA_EMBEDDING_MODEL`, since its Milestone
   9 introduction. Found by a from-scratch drill against a `v1.2`
   release-candidate whose fresh `ollama_data` volume ended up with only
   `bge-m3` after both documented loader commands exited `0`. Fixed by
   commit `c9219c3`.
3. **Extraction-policy default** — the tracked defaults
   (`.env.example`, the `ingest` service's `:-` fallback, `Settings`' class
   default) still carried the pre-`ADR-007` policy value, distinct from the
   environment-passthrough gap `v1`'s drill found; a fresh clone's own
   untouched `.env.example` failed 3 of 9 ingests with
   `extraction_conflict`. Fixed by commit `733aaf0`.
4. **Revision export** — the one-off ingestion command's documented
   invocation (`README.md`'s example, `docs/DOST_DEMO.md` §10's ingest loop)
   never exported `KENDRA_SOURCE_REVISION`, even though
   `docker-compose.yml`'s `ingest` service already passed it through; every
   row a from-scratch drill ingested recorded `pipeline_revision =
   "unknown"` rather than a real commit. Fixed by commit `7a3d391`.

**None of these four gaps would have been found by evaluating the long-lived
main stack.** All four are properties of standing up a *fresh* stack from a
tagged commit — a directory that has never been ingested into, a volume
that has never staged a model, a template that has never been rendered, an
environment variable that has never been exported — which the main dev
stack, continuously running and incrementally patched since Milestone 9,
does not exercise. This is the concrete argument for drilling every release
before, not instead of, evaluating it.

## 4. Determinism findings

**On a fixed index, the generator is deterministic.** Three independent
50-case gold evaluations run against the same long-lived Qdrant index, all
at `--seed 0`: `evaluation/runs/M13.1-release/20260902T044009Z-6a671dee/`
(`eval-f8338dde-fa4f-4b78-b760-a219bf13690e`),
`evaluation/runs/M13.5-diag/20260902T102352Z-6a671dee/`
(`eval-b8e77344-ea60-495c-91f0-e153a3e3ed6b`), and
`evaluation/runs/M13.5-diag/20260902T102542Z-6a671dee/`
(`eval-f92ab6a7-1dd7-4bd3-bcd0-c57e1fcfe000`). All three: `accuracy 0.82`,
`TP 32/FN 8/FP 1/TN 9`, identical per-case classification across every one
of the 50 cases, confirmed by direct diff of each run's `cases.jsonl`.

**On independently rebuilt indexes, it is not.** Two from-scratch drills
have each rebuilt the vector index from the same nine source documents and
run a gold evaluation against it, compared case-by-case to a release
evaluation run against the long-lived index at the same commit:

| Drill | RC | Agreement | Differing cases |
|---|---|---|---|
| `M13.4-recovery-drill` | `6a671dee` | 47/50 (`0.80` vs. release `0.82`) | `KND-M5-CD-004`, `KND-M5-DF-005`, `KND-M5-DF-018` |
| `M13.6-recovery-drill` | `b8286729` | 48/50 (`0.82`, matching release `0.82` in aggregate) | `KND-M5-CD-004`, `KND-M5-DF-018` |

`M13.4-recovery-drill`'s run directory **does not exist on disk — its
artifacts were lost to teardown before a preserve-before-teardown step
existed** (added afterward: commits `85ccabe`, corrected by `f996f90`). Its
figures above are cited from `docs/adr/014-release-drill-evaluation-gate.md`
§1, the only place they are now recorded in this repository, not from a run
directory. `M13.6-recovery-drill`'s figures are cited directly from
`evaluation/runs/M13.6-recovery-drill/20260902T121128Z-b8286729/report.json`
and `evaluation/runs/M13.6-release/20260902T121848Z-b8286729/report.json`.

`KND-M5-CD-004` and `KND-M5-DF-018` have now moved classification on *both*
independently built indexes on record; `KND-M5-DF-005` moved on only one.
Two data points cannot establish whether this is a structural sensitivity
in those two cases specifically or coincidence. **The mechanism is inferred,
not shown**: the evaluation runner records no retrieval score, similarity,
or distance for any case — only the final citations that survived into an
answer — so there is no way to check directly whether a differing case's
top-k retrieval set actually changed between index builds, as opposed to
some other cause (a generator regression, a scoring defect) that a
count-based tolerance would silently absorb as the same, already-understood
variance. Closing this gap is `docs/PILOT_PLAN.md` item 4.

## 5. `ADR-014`

`docs/adr/014-release-drill-evaluation-gate.md`, Accepted, splits the
release-drill gate the `M13.4-recovery-drill` failure exposed into two
parts: a **deployment gate** (exact, unchanged — `source_revision` match,
`make check-template`, both models present, chunk/page counts and
`pipeline_revision` matching the release exactly, chain `PASS`, zero
residual resources) and an **evaluation gate** requiring per-case agreement
of at least `N = 47` of 50 between a drill and its release evaluation, with
the sole false positive and unsupported false-answer rate unchanged and
every differing case disclosed by ID with both labels. `N = 47` is
explicitly provisional — set from the single `M13.4-recovery-drill`
observation available when the ADR was accepted, with the ADR's own text
stating it is to be revisited once three index-rebuild drills exist. The
ADR's Alternative 4 names the intended successor: a mechanism-based
criterion ("every differing case must show a different retrieved chunk
set") rather than a count, not adoptable today because of the retrieval-
output gap in Section 4 above.

## 6. Provenance

The demonstration stack's own nine indexed documents all carry
`pipeline_revision = 'unversioned'` in their `processing_runs` rows — a
literal `Settings` class default from Milestone 9 (`3ce70b6`), removed when
Milestone 12 (`4f57903`) introduced real revision stamping via
`resolve_source_revision()`. These documents were ingested before that
change and have not been re-ingested since; current code cannot itself
produce `"unversioned"` — only a real commit, an explicit environment
override, or the literal `"unknown"`. `extractor_identity` is recorded for
all nine and does state the extraction policy and tool versions used, but
not a checkable commit. A from-scratch drill's own index does not have this
limitation: `M13.6-recovery-drill`'s ingestion (Section 2's revision-export
fix, commit `7a3d391`) recorded `pipeline_revision` equal to the deploying
commit for all nine documents. An evaluator who specifically needs a fully
provenance-stamped index — every row traceable to a real commit — should be
shown a fresh `docs/DOST_DEMO.md` §10 deployment rather than the long-lived
demonstration stack.

## 7. What remains open

- **`ADR-013`** (retry semantics for failed registry rows) — proposed only,
  not drafted. `find_by_checksum` treats any existing row for a checksum,
  including a `failed` one, as an unconditional duplicate; a document that
  fails extraction has no ordinary retry path short of direct database
  cleanup.
- **`docs/PILOT_PLAN.md` items 1–5** — extraction-retry gap (item 1),
  entrypoint-based `document-repository` init (item 2), offline model bundle
  (item 3), runner-side retrieval probe (item 4), and scripted drill (item
  5) are all scope-only, none implemented.
- **`KND-M5-UN-002`** — the sole false positive across every gold evaluation
  in this milestone's record. A confident, citation-backed `supported`
  answer to a question the corpus cannot answer as of the asked date; not
  fixed.
- **Fact-incompleteness under labeled rendering** — a known, unfixed defect
  class where a `supported`, correctly cited answer omits a required fact
  (`KND-M5-CD-005`, `KND-M5-DF-005`); not machine-enforced anywhere in the
  verification contract.
- **The answer model's own build/version provenance** — `pipeline_revision`
  now records the ingestion pipeline's commit, but nothing records which
  exact answer-model artifact (beyond its name, `qwen2.5:7b-instruct`)
  produced a given answering run. Not investigated this milestone; no
  committed document currently addresses it.
- **The demonstration stack's `'unversioned'` rows** (Section 6) — disclosed
  in `docs/DOST_DEMO.md` §8, not re-ingested. The main stack's own index
  remains not fully provenance-stamped; only a fresh drill's index is.
- **Ingest accepting an unknown revision silently** — an unset
  `KENDRA_SOURCE_REVISION` resolves to the literal `"unknown"` rather than
  failing the ingestion outright. Not addressed.
- **`ADR-014`'s `N = 47` is provisional** — one index-rebuild observation
  informed it (`M13.4-recovery-drill`); `M13.6-recovery-drill` supplies a
  second (48/50). Per the ADR's own text, `N` is revisited once three
  index-rebuild drills exist on record; two exist as of this milestone.

## 8. Deployment time

Marker-measured stages from `M13.6-recovery-drill`
(`evaluation/runs/M13.6-recovery-drill/20260902T121128Z-b8286729/`): model
staging (Docling + both Ollama models, parallel) `953s`; ingesting all nine
documents `201s`; building `api`/`web` with the release commit baked in and
bringing them up `84s`; enabling answering and running the 50-case gold
evaluation `136s`. These four stages sum to `1374s` (≈`22.9` minutes).
**The full procedure — `.env`/ownership setup, bringing up
`postgres`/`qdrant`/`ollama`, hash-chain verification, preserving run
artifacts, and teardown — is not yet timed end to end**: those five stages
were not individually marker-measured in the drill this figure is drawn
from, and no drill to date has captured a single, continuous, per-stage
wall-clock table with a documented, scripted procedure. `docs/PILOT_PLAN.md`
item 5 (scripted drill) is proposed specifically to close this by
construction, timing every stage without added operator effort.
