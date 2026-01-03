from pathlib import Path

from assistant.llm.clients import DummyLLMClient
from assistant.memory.embedding import DummyEmbedding
from assistant.memory.store import MemoryStore
from assistant.services.summaries import decay_report, summarize_period, temporal_truth_report


def _seed(store: MemoryStore):
    embedder = DummyEmbedding()
    vec = embedder.embed("örnek not")
    store.add_memory(
        kind="semantic",
        content="Mustafa sabah koşusu yaptı",
        embedding=vec,
        source="test-note.md",
        confidence=0.8,
        topic="alışkanlık",
    )
    store.add_memory(
        kind="episodic",
        content="Asistan hava durumunu paylaştı",
        embedding=vec,
        source="conversation",
        confidence=0.7,
        topic="hava",
    )
    store.add_memory(
        kind="temporal_truth",
        content="Bugün hava güneşli",
        embedding=vec,
        source="conversation",
        confidence=0.9,
        topic="hava",
        metadata={"version": 1},
    )


def test_summary_and_reports(tmp_path: Path):
    db = tmp_path / "memory.sqlite"
    store = MemoryStore(db)
    _seed(store)
    llm = DummyLLMClient()

    summary_path = summarize_period(
        store=store,
        llm=llm,
        period="daily",
        summaries_dir=tmp_path,
        max_tokens=128,
    )
    assert summary_path.exists()
    decay_path = decay_report(
        store=store,
        summaries_dir=tmp_path,
        decay_halflife_days=30,
        label="daily",
    )
    assert decay_path.exists()
    temporal_path = temporal_truth_report(
        store=store,
        summaries_dir=tmp_path,
        decay_halflife_days=30,
    )
    assert temporal_path.exists()
