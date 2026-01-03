"""Cognee entegrasyonu için basit adaptörler.

Bu modül, ileride tam Cognee graph/memory API'si bağlanabilsin diye hazırlanmış stub/fascade.
"""

import logging
from dataclasses import dataclass
from typing import Any, Iterable, Protocol

logger = logging.getLogger(__name__)


class CogneeClient(Protocol):
    def ingest_note(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        ...

    def query(self, text: str, top_k: int = 5) -> list[str]:
        ...


@dataclass
class DummyCogneeClient(CogneeClient):
    """Şimdilik dummy: gerçek Cognee endpoint yokken boş sonuç döner."""

    def ingest_note(self, text: str, metadata: dict[str, Any] | None = None) -> None:  # pragma: no cover - stub
        logger.debug("Cognee dummy ingest: %s", metadata or {})

    def query(self, text: str, top_k: int = 5) -> list[str]:  # pragma: no cover - stub
        logger.debug("Cognee dummy query: %s", text)
        return []


def build_cognee_client(enabled: bool, endpoint: str | None = None) -> CogneeClient:
    # Gelecekte: gerçek Cognee HTTP istemcisi burada oluşturulacak.
    if enabled and endpoint:
        logger.warning("Cognee gerçek istemci henüz uygulanmadı; dummy dönüyor.")
    return DummyCogneeClient()
