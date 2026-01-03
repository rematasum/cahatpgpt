"""Cognee entegrasyonu için basit adaptörler.

Bu modül, ileride tam Cognee graph/memory API'si bağlanabilsin diye hazırlanmış stub/fascade.
"""

import logging
from dataclasses import dataclass
from typing import Any, Protocol

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


def build_cognee_client(
    enabled: bool, endpoint: str | None = None, notes_graph: str | None = None, memory_graph: str | None = None
) -> CogneeClient:
    # Gelecekte: gerçek Cognee HTTP istemcisi burada oluşturulacak.
    if enabled and endpoint:
        return HTTPCogneeClient(endpoint=endpoint, notes_graph=notes_graph, memory_graph=memory_graph)
    return DummyCogneeClient()


@dataclass
class HTTPCogneeClient(CogneeClient):
    endpoint: str
    notes_graph: str | None = None
    memory_graph: str | None = None

    def ingest_note(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        graph = self.notes_graph or self.memory_graph
        if not graph:
            logger.debug("Cognee ingest skipped: graph tanımlı değil")
            return
        requests = _require_requests()
        url = f"{self.endpoint.rstrip('/')}/ingest"
        payload = {"graph": graph, "text": text, "metadata": metadata or {}}
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        logger.debug("Cognee ingest ok: %s", graph)

    def query(self, text: str, top_k: int = 5) -> list[str]:
        graph = self.memory_graph or self.notes_graph
        if not graph:
            logger.debug("Cognee query skipped: graph yok")
            return []
        requests = _require_requests()
        url = f"{self.endpoint.rstrip('/')}/query"
        payload = {"graph": graph, "query": text, "top_k": top_k}
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("results") if isinstance(data, dict) else data
        snippets: list[str] = []
        if isinstance(items, list):
            for item in items[:top_k]:
                if isinstance(item, str):
                    snippets.append(item)
                elif isinstance(item, dict):
                    text_val = item.get("text") or item.get("content") or item.get("summary")
                    src = item.get("source") or item.get("id")
                    if text_val:
                        snippets.append(f"{text_val} (kaynak: {src})" if src else text_val)
        return snippets


def _require_requests():
    try:
        import requests  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional path
        raise RuntimeError("requests kütüphanesi kurulu değil. requirements.txt'i yükleyin.") from exc
    return requests
