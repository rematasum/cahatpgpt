import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable

from assistant.memory.temporal import decay_confidence

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

    def last_messages(self, limit: int = 6) -> list[tuple[str, str]]:
        cur = self.conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        rows.reverse()
        return [(r[0], r[1]) for r in rows]

    def list_memories(self, kinds: Iterable[MemoryKind]) -> list[MemoryRecord]:
        kinds = list(kinds)
        placeholders = ",".join("?" for _ in kinds)
        cur = self.conn.execute(
            f"""SELECT id, kind, content, embedding, created_at, source, confidence, topic, metadata
            FROM memories WHERE kind IN ({placeholders})""",
            tuple(kinds),
        )
        rows = cur.fetchall()
        results: list[MemoryRecord] = []
        for row in rows:
            embedding = json.loads(row[3]) if row[3] else []
            metadata = json.loads(row[8]) if row[8] else {}
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
                    metadata=metadata,
                )
            )
        return results

    def memories_since(
        self,
        since_ts: float,
        kinds: Iterable[MemoryKind] | None = None,
    ) -> list[MemoryRecord]:
        kinds = list(kinds or ["episodic", "semantic", "temporal_truth"])
        placeholders = ",".join("?" for _ in kinds)
        cur = self.conn.execute(
            f"""SELECT id, kind, content, embedding, created_at, source, confidence, topic, metadata
            FROM memories WHERE kind IN ({placeholders}) AND created_at >= ?""",
            (*kinds, since_ts),
        )
        rows = cur.fetchall()
        results: list[MemoryRecord] = []
        for row in rows:
            results.append(
                MemoryRecord(
                    id=row[0],
                    kind=row[1],
                    content=row[2],
                    embedding=json.loads(row[3]) if row[3] else [],
                    created_at=row[4],
                    source=row[5] or "",
                    confidence=row[6] or 0.0,
                    topic=row[7],
                    metadata=json.loads(row[8]) if row[8] else {},
                )
            )
        return results

    def decay_snapshot(
        self, kinds: Iterable[MemoryKind], decay_halflife_days: int
    ) -> list[tuple[MemoryRecord, float]]:
        rows = self.list_memories(kinds)
        snapshot: list[tuple[MemoryRecord, float]] = []
        for mem in rows:
            decayed = decay_confidence(mem["confidence"], mem["created_at"], decay_halflife_days)
            snapshot.append((mem, decayed))
        return snapshot

    def topk_similar(
        self,
        query_embedding: list[float],
        kinds: Iterable[MemoryKind],
        top_k: int,
        min_similarity: float,
        decay_halflife_days: int | None = None,
    ) -> list[tuple[MemoryRecord, float]]:
        memories = self.list_memories(list(kinds))
        scored: list[tuple[MemoryRecord, float]] = []
        for mem in memories:
            similarity = cosine_similarity(mem["embedding"], query_embedding)
            if similarity < min_similarity:
                continue
            conf = mem["confidence"]
            if decay_halflife_days:
                conf = decay_confidence(conf, mem["created_at"], decay_halflife_days)
            score = similarity * conf
            scored.append((mem, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def close(self) -> None:
        self.conn.close()
