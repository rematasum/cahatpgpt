import time
from collections import defaultdict
from typing import Iterable, Sequence

from assistant.typing import MemoryRecord


def decay_confidence(confidence: float, created_at: float, half_life_days: int) -> float:
    age_days = (time.time() - created_at) / 86400
    decay_factor = 0.5 ** (age_days / half_life_days)
    return max(0.0, min(1.0, confidence * decay_factor))


def choose_temporal_truth(memories: list[MemoryRecord]) -> list[MemoryRecord]:
    # Yeni ve yüksek güvenli olanları öne çıkar
    sorted_memories = sorted(memories, key=lambda m: (m["confidence"], m["created_at"]), reverse=True)
    return sorted_memories


def format_memory_snippet(mem: MemoryRecord) -> str:
    created_ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(mem["created_at"]))
    topic = f" | konu: {mem['topic']}" if mem.get("topic") else ""
    version = ""
    metadata = mem.get("metadata") or {}
    if metadata:
        ver = metadata.get("version")
        if ver:
            version = f" | sürüm: v{ver}"
    return f"[{created_ts}] {mem['kind']} (güven {mem['confidence']:.2f}{topic}{version}) -> {mem['content']} (kaynak: {mem['source']})"


def temporal_versions(memories: Sequence[MemoryRecord]) -> dict[str, list[MemoryRecord]]:
    topics: defaultdict[str, list[MemoryRecord]] = defaultdict(list)
    for mem in memories:
        topic = mem.get("topic") or "genel"
        topics[topic].append(mem)
    for topic, items in topics.items():
        items.sort(key=lambda m: m["created_at"], reverse=True)
    return topics


def render_temporal_report(memories: Iterable[MemoryRecord], half_life_days: int) -> str:
    topics = temporal_versions(list(memories))
    lines: list[str] = []
    for topic, items in topics.items():
        lines.append(f"Konu: {topic}")
        for mem in items:
            decayed = decay_confidence(mem["confidence"], mem["created_at"], half_life_days)
            created_ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(mem["created_at"]))
            version = (mem.get("metadata") or {}).get("version")
            version_txt = f"v{version}" if version else "-"
            lines.append(
                f"  - {created_ts} | {version_txt} | güven: {mem['confidence']:.2f} -> {decayed:.2f} | {mem['content']} (kaynak: {mem['source']})"
            )
    return "\n".join(lines) if lines else "Temporal truth kaydı yok."
