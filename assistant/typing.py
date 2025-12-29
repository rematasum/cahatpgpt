from typing import Literal, TypedDict

MemoryKind = Literal["episodic", "semantic", "temporal_truth"]


class MemoryRecord(TypedDict):
    id: int | None
    kind: MemoryKind
    content: str
    embedding: list[float]
    created_at: float
    source: str
    confidence: float
    topic: str | None
