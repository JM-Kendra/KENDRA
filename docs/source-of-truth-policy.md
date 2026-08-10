# Source-of-Truth Policy

## Purpose

Kendra must make every document-grounded answer traceable to a stable, verifiable source while keeping source documents and sensitive government data out of Git. This policy defines the authoritative home of each class of asset.

## 1. Git owns reproducible project assets

The Git repository is the source of truth for:

- application and infrastructure code;
- non-secret configuration schemas, defaults, and templates;
- production and evaluation prompts;
- automated tests, fixtures that contain no sensitive or source-document content, and evaluation case definitions;
- reviewed scripts and migrations;
- architecture records, policies, runbooks, and other documentation.

Every tracked asset must be safe to copy to a developer machine and to the repository's future remote. Secrets, live credentials, personal data, confidential document excerpts, and machine-specific state are prohibited.

## 2. The document repository owns source evidence

A separately managed document repository is the source of truth for:

- original uploaded or imported documents and their preserved binary bytes;
- a stable document identifier and version identifier for each source;
- integrity metadata, including a cryptographic checksum of each version;
- authoritative provenance and access-control metadata;
- human-authored corrections or classifications that are intended to persist independently of any index rebuild.

Source versions are immutable. A changed document becomes a new version rather than silently replacing the bytes used by an earlier citation. The repository must preserve enough information to resolve a citation to the exact document version and location—such as page, section, paragraph, or bounding region—that supported a result.

The document repository is not stored in Git. Its backup, retention, access control, and audit requirements must be defined before production use.

## 3. Derived data is reproducible and disposable

Derived data includes:

- extracted text, OCR output, layout analysis, thumbnails, and normalized renditions;
- chunks, tokenization, embeddings, lexical indexes, vector indexes, and retrieval caches;
- application databases or tables reconstructed from source documents and Git-owned logic;
- downloaded model files and local inference caches;
- logs, temporary files, generated metrics, evaluation runs, and evaluation reports.

Derived data is never authoritative evidence and must not be committed to Git. It may be deleted and rebuilt from a named source-document version plus a named Git revision and declared model/tool versions.

If a human correction cannot be reproduced automatically, it must be promoted to authoritative metadata in the document repository or to a non-sensitive Git-owned rule or evaluation case. It must not survive only inside a derived index.

## Citation verification invariant

A citation is verifiable only when it records, directly or through a durable manifest:

1. the stable document identifier;
2. the exact document version or checksum;
3. a resolvable location within that version; and
4. the pipeline or Git revision that produced the cited representation.

Answers must not present derived text as authoritative when the corresponding source version and location cannot be resolved.

## Evaluation boundary

Evaluation case definitions, expected behaviors, scoring rules, and non-sensitive synthetic fixtures belong in Git. Generated predictions, traces, metrics exports, screenshots, and reports are derived outputs and remain outside Git.

Evaluation cases based on restricted documents must reference stable document/version identifiers and permitted assertions; they must not copy restricted document content into Git.

## Change control

Changes to these ownership boundaries require a documented policy or architecture decision reviewed in Git. Moving an asset between ownership classes requires an explicit migration and, where applicable, retention and deletion handling.
