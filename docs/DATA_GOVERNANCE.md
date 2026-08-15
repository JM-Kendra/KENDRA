# Data Governance and Document Authority

**Status:** Governance baseline; agency validation required before any pilot uses real documents

**Last updated:** 2026-08-15

## Purpose and policy status

This document defines Kendra's baseline rules for document authority, lifecycle, storage ownership, derived data, audit, and recovery. It must be read with the [source-of-truth policy](source-of-truth-policy.md), [product brief](PRODUCT_BRIEF.md), and [user workflows](USER_WORKFLOWS.md).

These rules are repository-level constraints, not evidence that any agency has approved a document class, custodian, retention period, access model, storage location, or recovery target. Items marked **AGENCY DECISION REQUIRED** must be resolved by accountable records, legal, privacy, security, and business owners before real agency documents are ingested.

Kendra is an evidence-retrieval aid. A search result, excerpt, summary, citation packet, or AI-generated answer is not an official government decision, approval, legal opinion, procurement determination, records disposition, or declaration that a document is controlling. Accountable personnel must inspect the preserved source and make those determinations under the agency's existing authority.

## 1. Authority model

### 1.1 Authoritative source evidence

For Kendra, the authoritative evidence is the exact, preserved binary content of an original document version accepted through an agency-authorized custody or publication process. This includes all pages and any annexes, attachments, signatures, seals, stamps, or other components that the responsible custodian determines are part of that version.

A file does not become authentic, official, effective, current, controlling, or applicable merely because it was uploaded, hashed, indexed, retrieved, or described as such. Those properties require evidence from the document itself and, where the agency requires it, an authorized register, publication, custodian, or decision process.

If a preserved copy is a scan or export rather than the physical or native original, the responsible custodian must establish whether it is the accepted authoritative rendition for the intended workflow. Kendra must expose that distinction; it must not infer equivalence.

### 1.2 Derived representations

All metadata, filenames, database rows, extracted text, OCR output, layout analysis, thumbnails, normalized renditions, chunks, tokenization, embeddings, lexical or vector indexes, caches, summaries, and generated answers are derived representations. They may help locate or manage evidence, but they do not replace or amend the preserved document bytes.

Governed metadata such as identifiers, checksums, provenance, sensitivity labels, issuance dates, effectivity assertions, and supersession links is necessary for integrity and operations. It remains a derived assertion. When metadata conflicts with the preserved document or an authorized external register, the conflict must be flagged, retrieval must not present the assertion as settled, and an authorized custodian must correct or adjudicate it through an audited process.

### 1.3 Authority precedence

When evidence conflicts, Kendra must not decide which instrument controls. It must preserve and surface the conflict for an authorized human. The baseline precedence for system handling is:

1. preserve every admitted original document version without alteration;
2. use an agency-designated authority or custodian to adjudicate authenticity and status;
3. record that adjudication as governed, auditable metadata linked to its supporting authority; and
4. rebuild or invalidate affected derived representations.

## 2. Roles and authorization

Role names are functional placeholders. **AGENCY DECISION REQUIRED:** map them to real positions, written delegations, separation-of-duties rules, and alternates.

| Function | Baseline responsibility | Prohibited action |
|---|---|---|
| Document owner | Accountable for the collection's business purpose, permitted users, and acceptable status evidence | Treating Kendra output as an approval or delegating statutory authority to the system |
| Records custodian | Confirms custody, completeness, accepted rendition, document class, version relationship, and applicable retention or hold | Silently changing preserved bytes or disposing outside approved records procedures |
| Authorized uploader | Submits files and available provenance for an approved collection | Admitting a document to a collection solely on personal judgment or replacing bytes in place |
| Document reviewer | Independently validates an intake or status change when required | Approving their own upload where agency policy requires segregation of duties |
| Privacy/security owner | Approves permitted sensitivity classes, storage boundaries, access handling, incident handling, and audit access | Using confidentiality as a substitute for a documented access decision |
| System administrator | Operates storage, databases, indexes, backups, and recovery under approved procedures | Granting content access, changing document status, or bypassing custody controls without authorization |
| Authorized user | Searches only permitted collections and independently verifies evidence in context | Redistributing restricted material or presenting a generated answer as an official decision |
| Auditor/incident responder | Reviews authorized audit evidence and investigates deviations | Browsing source content beyond the approved audit or incident purpose |

Only an authorized uploader acting for an approved collection may submit a document. Admission into the authoritative repository requires the custodian or designated reviewer to validate the intake. Upload capability and authority to admit, replace, release, reclassify, or dispose of a document are separate permissions.

## 3. Identification, integrity, and versioning

Each admitted source must have:

- a stable, opaque `document_id` for the continuing document identity;
- a unique `version_id` for one exact preserved binary version;
- a SHA-256 checksum calculated over the exact stored bytes and recorded as 64 lowercase hexadecimal characters;
- the original filename as received, media type, byte length, ingestion timestamp, and documented provenance;
- a location in the authoritative document repository; and
- a processing manifest linking derived representations to the source `version_id`, SHA-256 checksum, pipeline or Git revision, and declared tool/model versions.

A filename, title, document number, database row number, or vector-index key must not serve as the sole stable identifier. A checksum proves byte equality, not authenticity, completeness, lawful custody, effectivity, or applicability.

Source versions are immutable. A corrected scan, added signature page, changed attachment, re-export, redaction, or any other byte change creates a new `version_id` and checksum. The old version remains resolvable while retention permits. “Replace” means admit a new version and record its relationship to the prior version; it never means overwrite cited bytes.

Duplicate bytes may be linked to more than one provenance event or document context only through a reviewed, auditable decision. Kendra must not merge records based on checksum or filename alone.

## 4. Lifecycle and status metadata

### 4.1 Intake gates

Before a document version becomes available for ordinary retrieval, the intake record must show:

1. the approved collection and authorized uploader;
2. provenance and custody source;
3. successful byte capture and SHA-256 verification;
4. completeness checks appropriate to the document class;
5. sensitivity and PII handling status;
6. draft/final/obsolete status and any uncertainty;
7. reviewer or custodian disposition; and
8. an auditable admission time and actor.

An interrupted, rejected, unverified, or suspicious upload remains quarantined and must not be represented as an admitted authoritative source.

### 4.2 Issuance, effectivity, and supersession

The governed metadata model must be able to record, without inventing values:

- issuer and issuing office;
- document type, official number, title, and issuance date;
- effectivity start and end dates, including the source location supporting each date;
- lifecycle status such as `draft`, `issued`, `effective`, `expired`, `withdrawn`, `revoked`, `superseded`, `obsolete`, `disputed`, or `unknown`;
- `supersedes`, `superseded_by`, `amends`, and `amended_by` relationships at document-version level;
- the authoritative register, publication, document passage, or custodian action supporting the assertion;
- validation state (`unverified`, `verified`, or `disputed`), validator, validation time, and reason; and
- applicable jurisdiction, office, or scope only when established by authorized evidence.

Absence of a supersession link does not prove that a document is current. Where status evidence is missing, stale, conflicting, or outside the user's authorized corpus, Kendra must report the limitation and must not label the document controlling or applicable.

### 4.3 Drafts, obsolete versions, and withdrawals

Drafts must be segregated from final issuances, visibly labeled on every result or export, and excluded from any workflow that asks for controlling authority unless an agency-authorized use expressly requires draft research. A draft must never silently replace or be grouped as an issued version.

Superseded, expired, withdrawn, revoked, and obsolete versions remain immutable historical evidence while retention or legal hold requires them. They must not appear as current by default. When authorized historical retrieval is allowed, the result must show the status, status evidence, and successor relationship, if known. Withdrawal from retrieval must not destroy prior citation identity or audit history.

## 5. Confidential and personally identifiable information

**AGENCY DECISION REQUIRED:** approve the classification scheme, lawful basis and purpose, permitted document classes, authorized roles, offline-device rules, retention, disclosure handling, and incident process before ingesting confidential or personally identifiable information (PII).

Baseline rules are:

- source documents and every derived representation inherit at least the source's restrictions unless an authorized classification decision states otherwise;
- existence, title, status, snippets, citations, embeddings, queries, access denials, logs, and usage patterns may themselves disclose protected information;
- access must follow least privilege, need to know, purpose, case, office, time, and collection restrictions required by the agency;
- local availability, cached content, a prior answer, or an index hit never bypasses source authorization;
- restricted content must not enter Git, public services, demonstrations, screenshots, evaluation fixtures, support bundles, or external models without explicit written authority;
- logs should use identifiers and event facts rather than document content or raw queries unless a documented need and access rule requires otherwise; and
- exports, printed copies, removable media, backups, and restored environments retain the source classification and handling rules.

## 6. Storage and system boundaries

| Component | Responsible for | Must not become |
|---|---|---|
| Document repository | Immutable original bytes, version layout, durable source locations, and custody-preserving storage | Git content, an untracked personal folder, or a vector-index payload store |
| PostgreSQL | Derived registry records; identifiers and relationships; provenance assertions; status and validation state; access-control references; ingestion/processing manifests; job state; audit-event references | The authoritative document store, proof of authenticity/effectivity, or the sole copy of originals |
| Vector index | Derived chunks/embeddings, retrieval fields, source pointers, index-generation identity, and only the minimum approved access-filter fields | Authoritative evidence, a permissions authority, a records register, or the only copy of extracted text |
| Git | Policies, code, non-secret configuration, prompts, tests, evaluation definitions, migrations, and runbooks | Storage for originals, restricted excerpts, live metadata, databases, indexes, logs, secrets, or generated reports |
| Backup repository | Protected, versioned recovery copies and recovery metadata within approved boundaries | A less-controlled archive, informal sharing mechanism, or way to defeat retention and disposal |

PostgreSQL metadata is derived, but some records—such as human validation, access decisions, legal holds, and audit references—may not be automatically reproducible. It therefore requires backup, integrity checking, change control, and restoration testing even though it cannot override the original document.

The vector index is disposable and rebuildable. Every entry must resolve through PostgreSQL or a durable manifest to an admitted source `version_id` and checksum. If that link, the user's authorization, or the matching index generation cannot be verified, the entry must not support a result.

### 6.1 Local storage and future NAS

The initial local document repository and any future network-attached storage (NAS) are two implementations of the same governed repository boundary. Moving bytes to a NAS does not change their authority, classification, identifiers, retention, or audit obligations.

Local source storage must be separated from Git worktrees, PostgreSQL volumes, vector-index volumes, model caches, logs, exports, and temporary processing areas. Paths are deployment configuration, not identity; citations must use stable identifiers and checksums rather than machine-specific paths.

A future NAS introduces a network, identity, permission, availability, snapshot, and administrator trust boundary. Before migration, the agency must approve the NAS ownership, physical and network location, access mapping, encryption and key responsibilities, snapshot/backup behavior, failure behavior, monitoring, recovery test, and rollback plan. A mounted share must not be treated as trusted merely because it is on a local network.

## 7. Retention, backup, and disposal

**AGENCY DECISION REQUIRED:** define schedules, legal-hold rules, minimum and maximum retention, recovery point objectives (RPO), recovery time objectives (RTO), backup locations, encryption/key ownership, restore-test frequency, and approved disposal methods for each data class.

Until those decisions exist, real agency documents must not enter a pilot. Baseline expectations are:

- retain authoritative versions according to the agency's records schedule and any legal, audit, investigation, or preservation hold; supersession alone is not authority to delete;
- retain derived data only for an approved operational, audit, or evaluation need and never longer or more broadly than its source authorization permits;
- preserve citation resolution for retained versions and record a tombstone plus disposal authority when a version is lawfully destroyed;
- back up original bytes, non-reconstructible operational metadata, manifests, configuration needed for recovery, and protected audit evidence;
- keep backups logically separated from the primary failure domain and subject to the same or stricter classification and access controls;
- verify backups by scheduled restoration and checksum comparison, not by job-success messages alone; and
- dispose of primary, backup, temporary, exported, and derived copies through an approved, auditable process.

## 8. Audit requirements

The audit design must record enough information to answer who did what, to which document/version, when, from which authorized context, with what result and reason. Required event classes include:

- upload, quarantine, malware/malformed-file disposition, admission, rejection, and checksum verification;
- document/version creation, status or relationship change, reclassification, correction, withdrawal, hold, release, and disposal;
- permission grant, change, revocation, denial, privileged action, and emergency access;
- search, source open, restricted metadata exposure, citation/export/print, and bulk access where agency policy requires them;
- processing, index build/swap/invalidation, failed source resolution, and detected corruption or staleness;
- backup, restore, checksum validation, recovery test, and recovery failure; and
- suspected disclosure, integrity discrepancy, policy exception, incident action, and closure.

Each event should contain an authenticated actor or service identity, timestamp from an approved time source, action, target `document_id`/`version_id`/checksum where applicable, authorization context, outcome, reason, and correlation identifier. Audit records must avoid unnecessary document content and raw queries, be access-controlled, protected from unauthorized alteration, retained under an approved schedule, reviewable by designated personnel, and exportable for an authorized investigation.

Audit logging is not itself authorization, monitoring, or proof that an action was lawful. **AGENCY DECISION REQUIRED:** define review frequency, alert/escalation ownership, privacy constraints, acceptable clock behavior offline, and evidence-handling procedures.

## 9. Expected failure and recovery

| Failure | Required safe behavior | Recovery expectation |
|---|---|---|
| Interrupted or partial upload | Keep the object quarantined; do not assign admitted status or index it | Re-upload from the authorized source and verify size and SHA-256 before admission |
| Checksum mismatch or changed bytes | Stop processing and prevent citation to the mismatched version | Preserve evidence of the discrepancy, reacquire or restore the exact version, and require custodian review |
| Missing or conflicting status metadata | Show `unknown` or `disputed`; do not claim currentness, effectivity, or applicability | Obtain authorized evidence, record the adjudication, invalidate affected outputs, and rebuild derived data |
| Document repository unavailable | Fail closed for source-grounded answers; never substitute an index excerpt as authority | Restore service or a checksum-verified copy, then verify citation resolution before reopening retrieval |
| PostgreSQL unavailable or corrupt | Prevent unsafe writes and any result whose identity, authorization, or provenance cannot be verified | Restore the verified database backup, reconcile it with originals/manifests/audit evidence, then rebuild affected derived state |
| Vector index stale or corrupt | Remove the affected generation from service; do not use orphaned or mismatched hits | Rebuild from admitted versions with named pipeline/tool versions and validate source pointers and access filtering |
| Local disk or NAS failure | Do not silently fall back to uncontrolled copies | Activate the approved recovery location, compare checksums and manifests, and document failover and reconciliation |
| Unauthorized access or disclosure | Stop further exposure, preserve authorized evidence, and follow the agency incident process | Revoke affected access, assess source and derived exposure, notify accountable owners, remediate, and document return to service |
| Backup restore fails | Treat recoverability and stated RPO/RTO as unproven | Escalate, preserve remaining copies, repair the backup process, and complete a successful tested restore before reliance |

Recovery is complete only when authoritative bytes match recorded checksums, citations resolve to exact versions and locations, PostgreSQL state is reconciled, access decisions are current, derived indexes are rebuilt or verified, audit continuity is addressed, and an authorized owner approves return to service. Cached or previously generated answers must not be trusted after a relevant integrity or authorization incident without revalidation.

## 10. Governance and change control

Before production or a real-document pilot, the agency must name owners and approve the unresolved decisions in this document. Exceptions require a recorded scope, authority, reason, compensating procedure, expiration, and reviewer.

Changes to document authority, metadata interpretation, identifiers, checksum handling, custody, storage boundaries, access inheritance, retention, audit, or recovery require review in Git and an explicit migration/rollback plan. No database migration, NAS move, index rebuild, or software release may silently change what an existing citation identifies.

This milestone defines policy only. It does not assert that authentication, authorization, encryption, malware scanning, sandboxing, audit protection, backup, recovery, PostgreSQL, a vector index, local document storage, or NAS integration has been implemented or tested.
