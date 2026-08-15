# ADR-002: Immutable folder-backed document repository with a replaceable mount

**Status:** Accepted
**Date:** 2026-08-15
**Acceptance date:** August 15, 2026

## Context

The source-of-truth policy makes exact preserved document-version bytes authoritative and requires citations to survive path, index, and deployment changes. Git, PostgreSQL, Qdrant, OCR output, and extracted text must not become the authoritative document store. The first milestone requires local folder storage that can later become a NAS mount.

A filesystem path or filename cannot be document identity: paths change between hosts, NAS mounts, and recovery locations, while filenames can collide or be edited. A future NAS also creates network, identity, permission, snapshot, availability, and administrator trust boundaries.

## Decision

Define a `DocumentStore` application interface and implement `LocalDocumentStore` for the first MVP implementation phase.

The interface operates on stable `document_id` and `version_id` values and supports only the operations needed by the milestone:

- atomically admit a new immutable version from an approved intake area;
- stream exact bytes and byte ranges for source review;
- read the version manifest;
- report size and media type;
- verify the SHA-256 checksum; and
- resolve a logical repository URI without exposing a host path as identity.

The host repository root is deployment configuration. Docker Compose bind-mounts it read-only into the runtime API at one stable container path. A future approved NAS is mounted by the host at the configured repository root; the application still sees the same `DocumentStore` contract and logical URIs.

Each admitted version has an immutable object and a durable manifest. A conceptual layout is:

```text
<repository-root>/
  objects/<document_id>/<version_id>/source.pdf
  manifests/<document_id>/<version_id>.json
```

The manifest records at least stable IDs, SHA-256, byte length, media type, original filename, admitted logical URI, provenance reference, admission time/state, and any required human-governed classification or correction that must survive index rebuilds. Exact field ownership and agency authority still require governance approval.

Admission uses a controlled staging area and an atomic same-filesystem rename after validation. It must:

1. validate the approved intake manifest and file limits;
2. calculate SHA-256 over the exact bytes;
3. allocate a new `version_id` for every byte change;
4. write and synchronize the object and manifest to staging;
5. move both into their immutable version location without overwriting an existing version; and
6. only then register the version for processing in PostgreSQL.

The ordinary API has read-only source access. A trusted operator invokes a one-off admission command with a narrowly scoped read-write mount. Extracted text, page images, OCR, chunks, embeddings, databases, temporary files, caches, models, logs, and evaluation reports use separate locations and are disposable derived data.

PostgreSQL mirrors identifiers, logical locations, checksums, and governed assertions for queries and processing. The folder manifest remains necessary to reconstruct the source-to-registry relationship; PostgreSQL is not proof of authenticity or the only copy of non-reproducible human decisions. Qdrant stores only minimal pointers back to PostgreSQL/source versions.

## Citation and recovery rules

- A citation stores or resolves to `document_id`, `version_id`, source SHA-256, physical page or accepted source region, and processing/Git revision.
- A citation never depends on an absolute host path or current filename.
- Runtime source serving checks path containment and version identity; it must not accept a caller-supplied path.
- Activation of an index generation requires checksum and pointer reconciliation against the mounted repository.
- If a source cannot be resolved or its checksum differs, grounded answers stop. Index excerpts do not substitute for the original.
- A restored or NAS-mounted repository is accepted only after manifests, checksums, identifiers, and citation resolution are reconciled.

## Consequences

### Positive

- Original PDFs remain simple, inspectable files outside Git and derived stores.
- Bind-mount configuration can move from local disk to an approved NAS without changing citation identity or application logic.
- Runtime read-only access reduces accidental overwrite risk.
- Source recovery and derived-index rebuild remain separate operations.

### Negative and limitations

- Filesystem durability, locking, atomic rename behavior, backup, retention, and permissions become operational dependencies.
- A local disk is a single failure domain and does not satisfy production backup requirements.
- Keeping folder manifests and PostgreSQL mirrors consistent requires explicit admission and reconciliation logic.
- A host or NAS administrator can bypass application controls; organizational and storage controls remain necessary.
- Not every NAS provides the required POSIX semantics, range-read performance, stable mounts, or reliable permission mapping.

## Alternatives considered

### Store PDFs as PostgreSQL large objects

Rejected. It couples authoritative evidence to a database treated primarily as a derived registry, complicates direct custodian inspection, and makes a later NAS move less transparent.

### Add MinIO or another object-store service

Deferred. Object storage has useful immutability and API properties, but adds a service and operations burden not needed for the bounded first milestone. The `DocumentStore` seam permits this alternative later if evidence supports it.

### Store original bytes in Qdrant payloads

Rejected. Qdrant is a disposable retrieval index and must never become the only source copy or citation authority.

### Use filenames or relative paths as identifiers

Rejected. They are mutable, collide, leak deployment details, and break across storage migration.

### Let the runtime API write directly into the repository

Rejected for ordinary operation. It widens accidental and malicious modification paths. Admission receives temporary, explicit write access through a one-off operator command.

### Implement a NAS-specific client now

Rejected. The NAS product, protocol, permissions, topology, and recovery behavior are unknown. Mount substitution is the smallest reversible choice, subject to validation.

## Validation required

Before implementation is locked:

- test atomic admission failure before and after rename and prove an existing version is never overwritten;
- test checksum, stream, range-read, path-containment, and rebuild behavior across two different local mount points;
- measure temporary and steady-state disk use during Docling/OCR and two index generations;
- verify that the runtime API container cannot write to the source mount; and
- before any NAS claim, test the approved NAS for atomicity, permission mapping, mount-loss behavior, snapshot rollback, checksum throughput, backup/restore, and controlled rollback.

## Revisit when

Revisit the implementation when an approved NAS is selected, remote object access is required, corpus scale makes local scanning impractical, or governance mandates storage-native retention, legal hold, write-once behavior, or encryption/key controls that a mounted folder cannot provide.
