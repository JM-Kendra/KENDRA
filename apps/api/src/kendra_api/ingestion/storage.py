"""Controlled write-side adapter for immutable original admission."""

import hashlib
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

from kendra_api.ingestion.errors import IngestionError
from kendra_api.ingestion.models import (
    DocumentIdentity,
    IntakeManifest,
    StoredVersion,
    ValidatedPdf,
)
from kendra_api.storage.local import LocalDocumentStore


class LocalDocumentAdmissionStore(LocalDocumentStore):
    """Admission-only store used by the explicitly writable one-off command."""

    def _staging_path(self, ingestion_id: str) -> Path:
        ingestion_id = self._validate_identifier(ingestion_id, "ingestion_id")
        return self._contained(self._root / ".staging" / ingestion_id)

    def source_path(self, document_id: str, version_id: str) -> Path:
        """Resolve an admitted original for internal processing only."""
        return self._source_path(document_id, version_id)

    def discard_unregistered(self, identity: DocumentIdentity) -> None:
        """Remove only this command's known-unregistered admission after a race."""
        source = self._source_path(identity.document_id, identity.version_id)
        manifest = self._manifest_path(identity.document_id, identity.version_id)
        source.unlink(missing_ok=True)
        manifest.unlink(missing_ok=True)
        for directory in (source.parent, manifest.parent):
            try:
                directory.rmdir()
            except OSError:
                pass

    def admit(
        self,
        validated: ValidatedPdf,
        intake: IntakeManifest,
        identity: DocumentIdentity,
        pipeline_revision: str,
    ) -> StoredVersion:
        source_path = self._source_path(identity.document_id, identity.version_id)
        manifest_path = self._manifest_path(identity.document_id, identity.version_id)
        if source_path.exists() or manifest_path.exists():
            raise IngestionError("immutable_conflict", "source version already exists")
        staging = self._staging_path(identity.ingestion_id)
        staging_source = staging / "source.pdf"
        staging_manifest = staging / "manifest.json"
        source_linked = False
        try:
            staging.mkdir(parents=True, exist_ok=False)
            digest = hashlib.sha256()
            byte_length = 0
            with validated.path.open("rb") as incoming, staging_source.open("xb") as target:
                for block in iter(lambda: incoming.read(1024 * 1024), b""):
                    target.write(block)
                    digest.update(block)
                    byte_length += len(block)
                target.flush()
                os.fsync(target.fileno())
            if byte_length != validated.byte_length or digest.hexdigest() != validated.sha256:
                raise IngestionError("copy_integrity_failure", "staged original differs from intake")
            payload = {
                "document_id": identity.document_id,
                "version_id": identity.version_id,
                "sha256": validated.sha256,
                "byte_length": validated.byte_length,
                "media_type": validated.media_type,
                "original_filename": validated.original_filename,
                "safe_filename": validated.safe_filename,
                "page_count": validated.page_count,
                "logical_uri": (
                    f"kendra://repository/documents/{identity.document_id}/versions/"
                    f"{identity.version_id}"
                ),
                "provenance_reference": intake.provenance_reference,
                "approval_scope": intake.approval_scope,
                "admission_state": "admitted",
                "admitted_at": datetime.now(UTC).isoformat(),
                "pipeline_revision": pipeline_revision,
            }
            with staging_manifest.open("x", encoding="utf-8") as target:
                json.dump(payload, target, sort_keys=True, separators=(",", ":"))
                target.write("\n")
                target.flush()
                os.fsync(target.fileno())
            source_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            self._contained(source_path.parent)
            self._contained(manifest_path.parent)
            os.link(staging_source, source_path)
            source_linked = True
            try:
                os.link(staging_manifest, manifest_path)
            except Exception:
                source_path.unlink(missing_ok=True)
                source_linked = False
                raise
            source_path.chmod(0o444)
            manifest_path.chmod(0o444)
            return StoredVersion(
                logical_uri=payload["logical_uri"],
                manifest_uri=(
                    f"kendra://repository/manifests/{identity.document_id}/"
                    f"{identity.version_id}"
                ),
            )
        except IngestionError:
            raise
        except FileExistsError as exc:
            raise IngestionError("immutable_conflict", "source version already exists") from exc
        except OSError as exc:
            if source_linked:
                source_path.unlink(missing_ok=True)
            raise IngestionError("admission_failure", "source admission failed safely") from exc
        finally:
            shutil.rmtree(staging, ignore_errors=True)
