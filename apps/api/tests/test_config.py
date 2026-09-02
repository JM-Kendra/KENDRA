from pathlib import Path

import pytest
from pydantic import ValidationError

from kendra_api.config import Settings


def test_settings_are_typed_and_secret_safe() -> None:
    settings = Settings(
        _env_file=None,
        postgres_port=5544,
        postgres_password="do-not-expose",
        document_store_root=Path("/srv/kendra-documents"),
    )

    assert settings.postgres_port == 5544
    assert settings.document_store_root == Path("/srv/kendra-documents")
    assert settings.extraction_completeness_policy == "native-primary-detection-v1"
    assert settings.extraction_candidate_minimum_agreement == 0.90
    assert "do-not-expose" not in repr(settings)
    assert "do-not-expose" not in str(settings.model_dump())
    assert "do-not-expose" in settings.postgres_dsn


def test_extraction_completeness_policy_default_matches_adr_007() -> None:
    # docs/adr/007-native-primary-detection.md Section 2.3 (accepted 2026-08-19):
    # "KENDRA_EXTRACTION_COMPLETENESS_POLICY=native-primary-detection-v1". This
    # default was stale (still the pre-ADR-007 value) until Milestone 13 round 5
    # -- a fresh clone's own untouched .env.example produced extraction_conflict
    # failures on 3 of 9 demonstration documents as a direct result.
    settings = Settings(
        _env_file=None,
        postgres_password="do-not-expose",
        document_store_root=Path("/srv/kendra-documents"),
    )

    assert settings.extraction_completeness_policy == "native-primary-detection-v1"


def test_postgres_password_must_be_supplied() -> None:
    with pytest.raises(ValidationError, match="postgres_password"):
        Settings(_env_file=None)


def test_document_store_root_must_be_absolute() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            postgres_password="test-only",
            document_store_root=Path("relative/path"),
        )
