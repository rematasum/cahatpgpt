from pathlib import Path
from assistant.memory.store import MemoryStore
from assistant.memory.embedding import DummyEmbedding


def test_memory_add_and_retrieve(tmp_path: Path):
    db = tmp_path / "memory.sqlite"
    store = MemoryStore(db)
    embedder = DummyEmbedding()
    vec = embedder.embed("deneme metni")
    store.add_memory(
        kind="episodic",
        content="Mustafa kahve seviyor",
        embedding=vec,
        source="test",
        confidence=0.9,
        topic="tercih",
    )
    results = store.topk_similar(vec, ["episodic"], top_k=1, min_similarity=0.1)
    assert len(results) == 1
    mem, score = results[0]
    assert "kahve" in mem["content"]
    assert score > 0
