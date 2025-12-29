import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


class EmbeddingBackend(Protocol):
    def embed(self, text: str) -> list[float]:
        ...


class DummyEmbedding(EmbeddingBackend):
    def embed(self, text: str) -> list[float]:
        tokens = text.lower().split()
        vocab: dict[str, float] = {}
        for tok in tokens:
            vocab[tok] = vocab.get(tok, 0.0) + 1.0
        size = 64
        vec = [0.0] * size
        for tok, count in vocab.items():
            idx = hash(tok) % size
            vec[idx] += count
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]


class OllamaEmbedding(EmbeddingBackend):
    def __init__(self, base_url: str, model_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

    def embed(self, text: str) -> list[float]:
        requests = _require_requests()
        url = f"{self.base_url}/api/embed"
        payload = {"model": self.model_name, "input": text}
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        embeddings = data.get("embeddings") or data.get("embedding") or []
        return embeddings[0] if isinstance(embeddings, list) and embeddings else []


def _load_sentence_transformer(model_name: str, device: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            "sentence-transformers yüklü değil. requirements.txt'i kurun veya dummy backend kullanın"
        ) from exc
    except OSError as exc:  # pragma: no cover - native lib load issues (e.g., torch DLL)
        raise RuntimeError(
            "sentence-transformers altındaki torch kütüphaneleri yüklenemedi. "
            "Torch/CUDA DLL kurulumunu kontrol edin ya da config'te embedding.backend=dummy yapın."
        ) from exc
    return SentenceTransformer(model_name, device=device if device != "auto" else None)


@dataclass
class SentenceTransformerEmbedding(EmbeddingBackend):
    model_name: str
    device: str = "auto"

    def __post_init__(self) -> None:
        self.model = _load_sentence_transformer(self.model_name, self.device)

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vector.tolist()


def build_embedding(
    backend: str, model_name: str, device: str, base_url: str = "http://localhost:11434"
) -> EmbeddingBackend:
    if backend == "ollama":
        return OllamaEmbedding(base_url=base_url, model_name=model_name)
    if backend == "sentence_transformer":
        try:
            return SentenceTransformerEmbedding(model_name=model_name, device=device)
        except Exception as exc:  # pragma: no cover - runtime fallback
            logger.warning(
                "sentence-transformer yüklenemedi (%s). Dummy embedding'e düşülüyor.", exc
            )
    logger.warning("Dummy embedding backend seçildi. Sonuçlar düşük doğrulukta olabilir.")
    return DummyEmbedding()


def _require_requests():
    try:
        import requests  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - optional path
        raise RuntimeError("requests kütüphanesi kurulu değil. requirements.txt'i yükleyin.") from exc
    return requests
