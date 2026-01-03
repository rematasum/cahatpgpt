import logging
from pathlib import Path
from typing import Iterable

from assistant.memory.store import MemoryStore
from assistant.memory.embedding import EmbeddingBackend
from assistant.typing import MemoryKind

logger = logging.getLogger(__name__)


def ingest_notes(
    root: Path,
    allowed_dirs: Iterable[Path],
    store: MemoryStore,
    embedder: EmbeddingBackend,
) -> int:
    root = root.resolve()
    allowed = [d.resolve() for d in allowed_dirs]
    if not any(str(root).startswith(str(a)) for a in allowed):
        raise PermissionError(f"{root} izinli dizin listesinde değil")
    count = 0
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8")
            emb = embedder.embed(text)
            store.add_memory(
                kind=cast_kind("semantic"),
                content=text,
                embedding=emb,
                source=str(path),
                confidence=0.7,
                topic=path.stem,
            )
            count += 1
    logger.info("%s not dosyası eklendi", count)
    return count


def cast_kind(kind: MemoryKind) -> MemoryKind:
    return kind
