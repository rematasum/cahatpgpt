import logging
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence

from assistant.typing import MemoryRecord

logger = logging.getLogger(__name__)


def build_profile(memories: Iterable[MemoryRecord]) -> str:
    memory_list = list(memories)
    topics = Counter(mem["topic"] for mem in memory_list if mem.get("topic"))
    top_topics = ", ".join(f"{k}: {v}" for k, v in topics.most_common(5)) or "(konu yok)"
    sentiments = Counter(
        "olumlu" if "mutlu" in mem["content"].lower() else "diğer" for mem in memory_list
    )
    summary_lines = [
        f"Toplanan hafıza sayısı: {len(memory_list)}",
        f"En sık konular: {top_topics}",
        f"Duygu tahmini: {dict(sentiments)}",
    ]
    return "\n".join(summary_lines)


def build_profile_report(memories: Sequence[MemoryRecord]) -> str:
    kinds = Counter(mem["kind"] for mem in memories)
    topics = Counter(mem["topic"] for mem in memories if mem.get("topic"))
    sources = Counter(mem["source"] for mem in memories if mem.get("source"))
    lines = ["Profil Raporu:", "Türlere göre sayım: " + ", ".join(f"{k}={v}" for k, v in kinds.items())]
    lines.append("En sık konular: " + (", ".join(f"{k}: {v}" for k, v in topics.most_common(5)) or "(yok)"))
    lines.append("Kaynak dağılımı: " + (", ".join(f"{k}: {v}" for k, v in sources.most_common(5)) or "(yok)"))
    return "\n".join(lines)


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
