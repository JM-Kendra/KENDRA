# Kendra

Kendra is a local-first, citation-verifiable document intelligence project for Philippine government offices.

Milestone 8 provides only the runnable application foundation: a minimal Next.js frontend, a modular FastAPI backend, PostgreSQL, Qdrant, Ollama connectivity, a replaceable read-only document-store interface, and dependency readiness reporting. Document ingestion and question answering are intentionally not implemented.

## Safety boundary

This scaffold is for one trusted evaluator on one controlled workstation and only the approved public evaluation sample. It has no authentication or authorization. Do not load agency, personal, confidential, privileged, procurement-sensitive, case-restricted, or mixed-permission documents.

Original documents belong in a separately managed document repository, never Git. PostgreSQL, Qdrant data, model files, extracted text, logs, and generated evaluation reports are derived runtime data and also remain outside Git. See [the source-of-truth policy](docs/source-of-truth-policy.md).

## Repository layout

- `apps/api/` — FastAPI application, typed configuration, service connections, read-only storage seam, and backend tests.
- `apps/web/` — minimal Next.js service-readiness interface and frontend tests.
- `docs/` — architecture, accepted decisions, governance, and experiment plans.
- `evaluation/` — version-controlled evaluation definitions; generated runs remain ignored.
- `document-repository/` — ignored host folder for approved source bytes and manifests.

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

3. Build the application images:

   ```bash
   docker compose build
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

7. Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The page displays the same readiness information and clearly marks ingestion and question answering as unavailable.

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

Backend tests run in an isolated test image and do not require live services:

```bash
docker build --target test -t kendra-api-test ./apps/api
docker run --rm kendra-api-test
```

Frontend unit tests and TypeScript checks run during the frontend test-image build:

```bash
docker build --target test -t kendra-web-test ./apps/web
```

Validate the resolved Compose configuration without starting services:

```bash
docker compose config --quiet
```

## Troubleshooting

- If health returns `503`, run `docker compose ps` and `docker compose logs --tail=100 <service>` using the unavailable service name.
- If the document store is unavailable, confirm `KENDRA_DOCUMENT_STORE_HOST_PATH` exists and Docker can read it.
- If ports 3000 or 8000 are occupied, change `KENDRA_WEB_PORT` or `KENDRA_API_PORT` in `.env`; keep both bind hosts at `127.0.0.1`.
- If you change `NEXT_PUBLIC_KENDRA_API_BASE_URL`, rebuild `web` because browser-visible Next.js variables are compiled into the image.
