import math
import time
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
    return f"[{created_ts}] {mem['kind']} (güven {mem['confidence']:.2f}{topic}) -> {mem['content']} (kaynak: {mem['source']})"
