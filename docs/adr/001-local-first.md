# ADR-001: Local-first modular application on Docker Compose

**Status:** Accepted
**Date:** 2026-08-15
**Acceptance date:** August 15, 2026

## Context

Kendra must support evidence retrieval when internet connectivity is unreliable and document content may be unsuitable for external transmission. The first milestone must use Next.js, FastAPI/Python, Ollama with a Qwen-family model, BGE-M3, Qdrant, PostgreSQL, Docling, Tesseract, Docker Compose, and local-folder document storage. It must not introduce authentication, cloud routing, an observability platform, or microservices.

The repository contains no runtime evidence about target hardware, concurrency, corpus size, agency network design, identity provider, confidential-data approval, or recovery objectives. The initial approved evaluation set is bounded and public. A distributed production topology would therefore solve unverified problems while creating more failure and trust boundaries.

## Decision

Use one Docker Compose project on a single, physically controlled workstation for the first MVP implementation phase.

Run five long-lived services:

1. `web`: Next.js user interface and original-PDF review experience;
2. `api`: one modular FastAPI/Python application for HTTP endpoints, ingestion modules, retrieval, model orchestration, citation validation, and evaluation hooks;
3. `postgres`: registry, processing manifests, and publication state;
4. `qdrant`: rebuildable BGE-M3 retrieval index; and
5. `ollama`: locally cached Qwen-family inference.

Docling, Tesseract, and the BGE-M3 Python runtime are libraries/processes inside the API image. Ingestion is a reviewed one-off command using that image, not a continuously running worker service. Services communicate only on the private Compose network. User-facing ports bind to `127.0.0.1`.

After installation artifacts and model weights are staged, the complete core path must work with outbound networking disabled. There is no cloud fallback.

Because authentication is excluded, the first MVP implementation phase is a single-trusted-evaluator experiment using only the approved public evaluation corpus. It must not ingest real agency, personal, confidential, privileged, or mixed-permission material. This restriction is a safety boundary, not a claim that local hosting supplies authorization.

## Consequences

### Positive

- The whole system can be started, stopped, inspected, and rebuilt as one local deployment.
- Source content and queries need not cross an internet boundary.
- The API can keep ingestion and query invariants in one transactionally coordinated codebase.
- There are fewer network APIs, independent releases, and partial-failure modes than a microservice design.
- The same Compose topology gives development and evaluation a reproducible baseline.

### Negative and limitations

- A single host and local storage are single points of failure.
- There is no high availability, automatic failover, or production recovery claim.
- Local administrators and anyone with OS access remain inside the trust boundary.
- CPU/GPU, RAM, disk, and thermal contention can affect ingestion and answer latency.
- No authentication means there is no safe multi-user or restricted-document deployment.
- Container isolation is not sufficient by itself for hostile production document intake.
- Offline dependency and model update custody remains a manual operational problem.

## Alternatives considered

### Cloud-managed model and data services

Rejected for the first MVP implementation phase. They conflict with the required offline path and introduce data-routing, procurement, and authorization questions that have not been approved.

### Kubernetes

Rejected. The milestone has no demonstrated scaling, availability, tenancy, or deployment-frequency requirement that justifies a cluster, ingress, secrets platform, and additional control plane.

### Independent ingestion, retrieval, model, and citation microservices

Rejected. These boundaries would create versioned network contracts and distributed consistency problems without a measured workload or team ownership need. Internal Python interfaces preserve later seams.

### Host processes without containers

Rejected as the reference architecture. Direct host installation can be smaller at runtime, but it weakens dependency reproducibility and offline artifact inventory. It may remain useful for isolated experiments.

### Desktop-packaged monolith

Deferred. It could improve single-user installation, but it does not match the required Next.js/FastAPI/Docker Compose stack and would add packaging work before feasibility is established.

## Validation required

Before implementation is locked:

- benchmark candidate Qwen variants and BGE-M3 on the actual target hardware;
- prove that all required containers, packages, OCR data, and models can start and run with outbound networking disabled;
- measure peak RAM, VRAM, disk, and latency under serialized ingestion and one concurrent query; and
- inject service restarts and confirm the API refuses answers until PostgreSQL, the active Qdrant generation, Ollama, and source repository are consistent.

## Revisit when

Revisit this decision only when evidence establishes a second site, concurrent users, background ingestion demand, stronger parser isolation, high-availability objectives, or independently owned deployment units. Authentication and authorization must be designed before any such multi-user expansion.
