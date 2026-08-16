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
    assert "do-not-expose" not in repr(settings)
    assert "do-not-expose" not in str(settings.model_dump())
    assert "do-not-expose" in settings.postgres_dsn


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
