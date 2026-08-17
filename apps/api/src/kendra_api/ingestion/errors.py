"""Typed ingestion failures with content-safe error codes."""


class IngestionError(Exception):
    """An expected fail-closed ingestion error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
