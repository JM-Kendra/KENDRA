# Kendra

Kendra is a planned offline, citation-verifiable document intelligence platform for Philippine government offices.

This repository currently contains only the project-governance foundation. It does not contain application code, working prompts, models, document data, or a runnable system.

## Repository layout

- `apps/` — reserved application boundaries; intentionally empty.
- `docs/` — architecture, decisions, operating guidance, and governance policies.
- `evaluation/cases/` — version-controlled evaluation case definitions when they are introduced.
- `prompts/` — version-controlled production and evaluation prompts when they are introduced.
- `scripts/` — reviewed developer and operational scripts when they are introduced.
- `tests/` — version-controlled automated tests when they are introduced.

The authoritative ownership rules are in [docs/source-of-truth-policy.md](docs/source-of-truth-policy.md).

## Data boundary

Git is for reproducible intellectual and engineering work: code, configuration templates, prompts, tests, evaluation cases, scripts, and documentation. It is not a document store or runtime data store.

Uploaded government documents must be kept in a separately managed document repository. Databases, OCR output, chunks, embeddings, vector indexes, caches, downloaded models, logs, and generated evaluation reports are derived or runtime data and must not be committed.

## Local configuration

Copy `.env.example` to `.env` when local development begins. `.env` and related local overrides are ignored. The example file must contain names and safe placeholders only—never real credentials, tokens, private endpoints, or secret values.

## Current status

Foundation only. Application design and implementation are intentionally out of scope for this commit.
