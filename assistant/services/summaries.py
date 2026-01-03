import logging
import time
from pathlib import Path
from textwrap import dedent
from typing import Iterable

from assistant.llm.clients import BaseLLMClient
from assistant.memory.store import MemoryStore
from assistant.memory.temporal import render_temporal_report
from assistant.typing import MemoryRecord

logger = logging.getLogger(__name__)


def _build_summary_prompt(memories: Iterable[MemoryRecord], period: str, max_tokens: int) -> str:
    lines = [f"Periyot: {period}"]
    for mem in memories:
        lines.append(f"- ({mem['kind']}, {mem.get('topic') or 'konu yok'}) {mem['content']}")
    context = "\n".join(lines) if lines else "Kayıt yok."
    return dedent(
        f"""
        Aşağıdaki anıları {period} özeti olarak 5 maddeyi geçmeden Türkçe ve kısa biçimde özetle.
        Önemli zaman/konu/sinyal varsa vurgula.
        Maksimum {max_tokens} tokena sığdır.
        {context}
        """
    ).strip()


def summarize_period(
    store: MemoryStore,
    llm: BaseLLMClient,
    period: str,
    summaries_dir: Path,
    max_tokens: int,
) -> Path:
    period = period.lower()
    if period not in {"daily", "weekly"}:
        raise ValueError("period daily veya weekly olmalı")
    now = time.time()
    horizon = 86400 if period == "daily" else 7 * 86400
    memories = store.memories_since(now - horizon)
    prompt = _build_summary_prompt(memories, period, max_tokens)
    summary = llm.generate(system_prompt="Özetleyici", user_prompt=prompt, stream=False).content
    return _write_report(f"{period}-summary", summary, summaries_dir)


def decay_report(store: MemoryStore, summaries_dir: Path, decay_halflife_days: int, label: str) -> Path:
    snapshot = store.decay_snapshot(
        kinds=["episodic", "semantic", "temporal_truth"],
        decay_halflife_days=decay_halflife_days,
    )
    lines = [f"Decay raporu ({label})"]
    for mem, decayed in snapshot:
        lines.append(
            f"- {mem['kind']} | {mem.get('topic') or 'konu yok'} | {mem['confidence']:.2f} -> {decayed:.2f} | {mem['content'][:140]}"
        )
    report = "\n".join(lines)
    return _write_report(f"decay-{label}", report, summaries_dir)


def temporal_truth_report(store: MemoryStore, summaries_dir: Path, decay_halflife_days: int) -> Path:
    memories = store.list_memories(["temporal_truth"])
    report = render_temporal_report(memories, half_life_days=decay_halflife_days)
    return _write_report("temporal-truth", report, summaries_dir)


def _write_report(prefix: str, body: str, summaries_dir: Path) -> Path:
    summaries_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{prefix}-{time.strftime('%Y%m%d-%H%M')}.md"
    path = summaries_dir / filename
    path.write_text(body, encoding="utf-8")
    logger.info("Rapor yazıldı: %s", path)
    return path
