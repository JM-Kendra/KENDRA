"""Document storage interfaces and implementations."""

from kendra_api.storage.base import DocumentStore, StoredSource
from kendra_api.storage.local import LocalDocumentStore

__all__ = ["DocumentStore", "LocalDocumentStore", "StoredSource"]
