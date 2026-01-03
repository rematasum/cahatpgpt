import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from assistant.typing import MemoryKind, MemoryRecord
from assistant.utils import cosine_similarity, now_ts

logger = logging.getLogger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,
    created_at REAL NOT NULL,
    source TEXT,
    confidence REAL DEFAULT 0.5,
    topic TEXT,
    metadata TEXT
);
"""


class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        logger.info("Memory DB ready at %s", db_path)

    def add_message(self, role: str, content: str) -> None:
        self.conn.execute(
            "INSERT INTO messages(role, content, created_at) VALUES (?, ?, ?)",
            (role, content, now_ts()),
        )
        self.conn.commit()

    def add_memory(
        self,
        kind: MemoryKind,
        content: str,
        embedding: list[float],
        source: str,
        confidence: float = 0.6,
        topic: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO memories(kind, content, embedding, created_at, source, confidence, topic, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                kind,
                content,
                json.dumps(embedding),
                now_ts(),
                source,
                confidence,
                topic,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.conn.commit()
        memory_id = cur.lastrowid
        logger.debug("Added memory %s (%s)", memory_id, kind)
        return int(memory_id)

    def list_memories(self, kinds: Iterable[MemoryKind]) -> list[MemoryRecord]:
        placeholders = ",".join("?" for _ in kinds)
        cur = self.conn.execute(
            f"SELECT id, kind, content, embedding, created_at, source, confidence, topic FROM memories WHERE kind IN ({placeholders})",
            tuple(kinds),
        )
        rows = cur.fetchall()
        results: list[MemoryRecord] = []
        for row in rows:
            embedding = json.loads(row[3]) if row[3] else []
            results.append(
                MemoryRecord(
                    id=row[0],
                    kind=row[1],
                    content=row[2],
                    embedding=embedding,
                    created_at=row[4],
                    source=row[5] or "",
                    confidence=row[6] or 0.0,
                    topic=row[7],
                )
            )
        return results

    def topk_similar(
        self,
        query_embedding: list[float],
        kinds: Iterable[MemoryKind],
        top_k: int,
        min_similarity: float,
    ) -> list[tuple[MemoryRecord, float]]:
        memories = self.list_memories(kinds)
        scored: list[tuple[MemoryRecord, float]] = []
        for mem in memories:
            score = cosine_similarity(mem["embedding"], query_embedding)
            if score >= min_similarity:
                scored.append((mem, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def close(self) -> None:
        self.conn.close()
