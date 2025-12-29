import logging
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from assistant.typing import MemoryRecord

logger = logging.getLogger(__name__)


def build_profile(memories: Iterable[MemoryRecord]) -> str:
    topics = Counter(mem["topic"] for mem in memories if mem.get("topic"))
    top_topics = ", ".join(f"{k}: {v}" for k, v in topics.most_common(5)) or "(konu yok)"
    sentiments = Counter(
        "olumlu" if "mutlu" in mem["content"].lower() else "diğer" for mem in memories
    )
    summary_lines = [
        f"Toplanan hafıza sayısı: {len(list(memories))}",
        f"En sık konular: {top_topics}",
        f"Duygu tahmini: {dict(sentiments)}",
    ]
    return "\n".join(summary_lines)


@dataclass
class ReflectionTracker:
    refresh_turns: int
    turns: int = 0
    reflections: list[str] | None = None

    def __post_init__(self) -> None:
        if self.reflections is None:
            self.reflections = []

    def maybe_add_reflection(self, insight: str) -> list[str]:
        self.turns += 1
        if self.turns % self.refresh_turns == 0:
            self.reflections.append(insight)
        return self.reflections
