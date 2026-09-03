# Kendra

Kendra is a local-first, citation-verifiable document intelligence project for Philippine government offices.

Milestone 9 adds a trusted-operator, one-off PDF ingestion command to the Milestone 8 foundation. It validates and preserves approved originals, extracts physical pages with Docling and page-level Tesseract fallback, creates deterministic overlapping page chunks, generates local BGE-M3 embeddings through Ollama, and publishes derived metadata and vectors through PostgreSQL and Qdrant. Question answering remains intentionally unavailable.

## Safety boundary

This scaffold is for one trusted evaluator on one controlled workstation and only the approved public evaluation sample. It has no authentication or authorization. Do not load agency, personal, confidential, privileged, procurement-sensitive, case-restricted, or mixed-permission documents.

Original documents belong in a separately managed document repository, never Git. PostgreSQL, Qdrant data, model files, extracted text, logs, and generated evaluation reports are derived runtime data and also remain outside Git. See [the source-of-truth policy](docs/source-of-truth-policy.md).

## Repository layout

- `apps/api/` — FastAPI application, typed configuration, service connections, read-only storage seam, and backend tests.
- `apps/web/` — minimal Next.js service-readiness interface and frontend tests.
- `docs/` — architecture, accepted decisions, governance, and experiment plans.
- `evaluation/` — version-controlled evaluation definitions; generated runs remain ignored.
- `document-repository/` — ignored host folder for approved source bytes and manifests.
- `intake/` — ignored host folder mounted read-only by the one-off ingestion command.

## Prerequisites

Install Docker Desktop, or Docker Engine with the Compose plugin. Confirm both commands work:

```bash
docker --version
docker compose version
```

No host Python, Node.js, PostgreSQL, Qdrant, or Ollama installation is required for the reference setup.

## First run

Run every command from the repository root.

1. Create your local configuration:

   ```bash
   cp .env.example .env
   ```

   The example contains disposable local defaults only. Change `KENDRA_POSTGRES_PASSWORD` in `.env`; never commit that file.

2. Ensure the configured source folder exists:

   ```bash
   mkdir -p document-repository
   ```

   `KENDRA_DOCUMENT_STORE_HOST_PATH` may instead point to an approved NAS mount. Compose mounts either host path read-only at `KENDRA_DOCUMENT_STORE_ROOT=/documents`, so application business logic does not change when the host root changes.

   Create the separate intake folder as well:

   ```bash
   mkdir -p intake
   ```

3. Build the application images:

   ```bash
   docker compose build
   ```

   To rebuild the `api` image with a real `KENDRA_SOURCE_REVISION` baked in (so
   `/api/v1/health` and citations report the actual revision without exporting the
   variable at every `docker compose up`), use the `build` Makefile target instead,
   which exports it from the current commit for you:

   ```bash
   make build
   ```

4. Start all five services:

   ```bash
   docker compose up -d
   ```

5. Inspect startup:

   ```bash
   docker compose ps
   docker compose logs --tail=100 api web postgres qdrant ollama
   ```

6. Check API readiness:

   ```bash
   curl -i http://127.0.0.1:8000/api/v1/health
   ```

   HTTP `200` means PostgreSQL, Qdrant, Ollama, and the configured document-store root are reachable. HTTP `503` identifies unavailable dependencies using safe status codes; the response never includes connection strings, paths, credentials, or raw exceptions. Ollama readiness checks its local API only. Model selection belongs to EXP-04 and is not claimed by this milestone.

7. Open [http://127.0.0.1:3000](http://127.0.0.1:3000) (or `http://localhost:3000` — both work identically as of `demo-dost-v1.3`, no CORS dependency; the browser calls the api at the page's own origin, proxied server-side). The page displays the same readiness information and clearly marks ingestion and question answering as unavailable.

## One-off PDF ingestion

Ingestion is not exposed through the browser or running API. It accepts one PDF beneath the configured intake root and an exact JSON manifest. Use only approved public evaluation material; do not put the intake folder or document repository in Git.

The manifest schema is intentionally closed:

```json
{
  "original_filename": "approved-sample.pdf",
  "expected_sha256": "64-lowercase-hexadecimal-characters",
  "expected_page_count": 1,
  "approval_scope": "approved-public-evaluation",
  "provenance_reference": "approval-manifest-entry-or-reviewed-source",
  "approval_status": "approved"
}
```

Before the first offline run, stage the Docling layout/table models and both Ollama models — the embedding model (`KENDRA_EMBEDDING_MODEL`, `bge-m3`) and the answer model (`KENDRA_ANSWER_MODEL`, `qwen2.5:7b-instruct`) — while approved network access is available. `ollama-model-loader` pulls both, in sequence, failing if either pull fails:

```bash
docker compose --profile ingestion-setup run --rm docling-model-loader
docker compose --profile ingestion-setup run --rm ollama-model-loader
docker compose up -d postgres qdrant ollama
```

The ingestion profile mounts the staged Docling model volume read-only and explicitly disables Docling OCR. Missing model artifacts fail ingestion; they are never fetched silently during the controlled run. Tesseract is the only OCR fallback.

Export `KENDRA_SOURCE_REVISION` to the exact Git commit being run before invoking ingestion — this is the value actually recorded as each processing run's `pipeline_revision` (`resolve_source_revision()`, `apps/api/src/kendra_api/ingestion/cli.py`); an unset value resolves to the literal `"unknown"` rather than silently guessing. Place the PDF and manifest under `intake/`, then invoke the profile-scoped command:

```bash
KENDRA_SOURCE_REVISION=$(git rev-parse HEAD) docker compose --profile ingestion run --rm ingest approved-sample.pdf --manifest approved-sample.json
```

The command emits one machine-readable receipt. An exact-checksum duplicate returns `"duplicate": true` and the existing version identity rather than creating new PostgreSQL records, originals, chunks, or vectors. A processing failure preserves the admitted original, marks the PostgreSQL version/run/generation failed where possible, and never activates the partial Qdrant generation.

## Stop and restart

Stop containers while retaining the local PostgreSQL, Qdrant, and Ollama volumes:

```bash
docker compose down
```

Restart with:

```bash
docker compose up -d
```

Do not add `--volumes` unless you intentionally want to delete derived local service data.

## Automated checks

Backend tests run in an isolated test image and do not require live services. Run this from the repository root — the `--build-context fixtures=.` flag pulls in `scripts/validate_gold_cases.py` and `evaluation/gold_cases.json` from the repo root, which the evaluation-runner lock tests need to build a throwaway git repository in `tmp_path` (see `apps/api/tests/conftest.py`); neither file lives under `apps/api`'s own build context. `make test` runs both steps:

```bash
docker build --target test --build-context fixtures=. -t kendra-api-test ./apps/api
docker run --rm kendra-api-test
```

This is the containerized *subset* (`120 passed, 2 skipped, 43 deselected`) — two files need a real, on-disk git checkout to run at all and are excluded by design (`test_evaluation_runner.py`, `test_source_revision.py`; see `CLAUDE.md`'s "Commands"). `make test-full` runs the complete suite (`141 passed, 43 deselected, 0 skipped`) by bind-mounting this checkout into the same image instead of building a throwaway one.

The backend suite generates its digital and scanned PDFs under pytest temporary directories. It commits no generated PDFs or extracted content. Both fixtures exercise Docling's actual local PDF parser; the scanned fixture then invokes the container's actual Poppler/Tesseract tools. Unit tests do not download model artifacts.

Frontend unit tests and TypeScript checks run during the frontend test-image build:

```bash
docker build --target test -t kendra-web-test ./apps/web
```

Validate the resolved Compose configuration without starting services:

```bash
docker compose --env-file .env.example config --quiet
```

## Demonstration releases

A tagged demonstration release (for example `demo-dost-v1.3`, the current
release — see `docs/DOST_DEMO.md`) bakes its Git commit into both images
(and its tag into the `api` image) rather than requiring anyone to remember
which checkout produced them:

1. Confirm the working tree is clean and tests pass (`docker build --target
   test --build-context fixtures=. -t kendra-api-test ./apps/api && docker
   run --rm kendra-api-test`, `docker build --target test ./apps/web`).
2. Tag the commit: `git tag demo-dost-v1.3`.
3. Rebuild with the tag baked in:

   ```bash
   make build
   ```

   This computes `KENDRA_SOURCE_REVISION` and `NEXT_PUBLIC_KENDRA_GIT_COMMIT`
   from `git rev-parse HEAD` and `KENDRA_RELEASE_TAG` from `git describe
   --tags --exact-match HEAD` (harmlessly empty on an untagged commit), then
   passes all three to `docker compose build api web`. Nothing is
   hand-typed into a Dockerfile or compose file.

4. Recreate the running containers (`docker compose up -d --force-recreate
   api web`) and confirm both surfaces agree with the tag:

   ```bash
   curl -s http://127.0.0.1:8000/api/v1/health | python3 -m json.tool
   # source_revision and release_tag should match the tagged commit
   ```

   Open `http://127.0.0.1:3000` (or `http://localhost:3000` — both work
   identically as of `demo-dost-v1.3`) and check the page footer for the
   same commit, and the heading for the same tag.
5. Push the branch and the tag: `git push origin <branch> demo-dost-v1.3`.

See [`docs/DOST_DEMO.md`](docs/DOST_DEMO.md) for the seven-minute
demonstration guide, architecture diagram, honest limitations, hardware and
deployment requirements, and the tested recovery plan, and
[`docs/PILOT_PLAN.md`](docs/PILOT_PLAN.md) for the pilot success metrics a
release like this one is measured against.

## Troubleshooting

- If health returns `503`, run `docker compose ps` and `docker compose logs --tail=100 <service>` using the unavailable service name.
- If the document store is unavailable, confirm `KENDRA_DOCUMENT_STORE_HOST_PATH` exists and Docker can read it.
- If ports 3000 or 8000 are occupied, change `KENDRA_WEB_PORT` or `KENDRA_API_PORT` in `.env`; keep both bind hosts at `127.0.0.1`.
- If you change `NEXT_PUBLIC_KENDRA_API_BASE_URL`, rebuild `web` because browser-visible Next.js variables are compiled into the image.
- If one-off ingestion fails with `admission_failure` on every document, the host `document-repository/objects`, `document-repository/manifests`, and `document-repository/.staging` directories are not owned by the container's non-root `kendra` user (uid 999) — the `ingest` service runs as that user by design, but a directory created by the host user under a default umask (`755`, owner-only write) blocks a different uid from creating new entries in it. Fix ownership, not permissions: a world-writable grant (`chmod o+w`) would let any local user unlink or replace an admitted, `0444`-mode original despite its immutable file mode, which the filesystem alone cannot prevent (`ARCHITECTURE.md` Section 9's immutability invariant is enforced by application logic, not filesystem permissions). Instead, `chown` those three directories to uid/gid `999` so the container that already owns them can write, and leave the mode at `755`. On a genuinely fresh `document-repository/` the three subdirectories do not exist yet — they are created lazily by the ingestion pipeline's own code on first use — so create them first:

  ```bash
  docker run --rm -v "$(pwd)/document-repository":/repo alpine sh -c \
    "mkdir -p /repo/objects /repo/manifests /repo/.staging && \
     chown -R 999:999 /repo/objects /repo/manifests /repo/.staging && \
     chmod 755 /repo/objects /repo/manifests /repo/.staging"
  ```

  (A one-off privileged container is used because root inside it maps to real host root, which can `chown` to an arbitrary uid without needing host `sudo`.) Run this once on a freshly created `document-repository/` before ingesting. Found during Milestone 13's from-scratch recovery drill and initially patched with the broader `chmod o+w` grant, later replaced with the ownership fix above; the `mkdir -p` step was added after a from-tag drill against the pushed `demo-dost-v1.1` tag found the ownership-only command failing with "No such file or directory" on a truly fresh directory (the fix had only ever been exercised against a long-lived dev environment where these subdirectories already existed) — see `docs/DOST_DEMO.md`'s recovery plan. This correction post-dates the `demo-dost-v1.1` tag and does not retroactively make that tag deployable from scratch as tagged; a future release's own from-tag drill is what would confirm it.
