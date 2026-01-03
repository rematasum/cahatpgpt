from pathlib import Path

from assistant.config.loader import load_settings
from assistant.services.conversation import ConversationEngine


def _write_settings(tmp_path: Path) -> Path:
    cfg = tmp_path / "settings.yaml"
    cfg.write_text(
        """
environment: test
paths:
  data_dir: data
  db_file: data/memory.sqlite
  log_dir: logs
  summaries_dir: data/summaries
llm:
  provider: dummy
  model: dummy
  temperature: 0.1
  max_tokens: 10
  base_url: http://localhost
embedding:
  backend: dummy
  model_name: dummy
  device: cpu
memory:
  top_k: 3
  min_similarity: 0.0
  decay_halflife_days: 30
  temporal_truth_key: topic
profile:
  refresh_turns: 2
  summary_max_tokens: 64
security:
  allow_notes_dir: notes
  allow_commands: config/allowlist.yaml
ui:
  stream: false
  system_prompt: test prompt
""",
        encoding="utf-8",
    )
    return cfg


def test_temporal_and_episodic_memories_created(tmp_path: Path):
    cfg = _write_settings(tmp_path)
    settings = load_settings(cfg)
    engine = ConversationEngine(settings=settings, db_path=tmp_path / "memory.sqlite")

    engine.chat("Gamze'nin sigorta geçişi 10 Ocak'ta bitecek")

    memories = engine.memory_store.list_memories(["episodic", "temporal_truth"])
    kinds = {mem["kind"] for mem in memories}
    assert "episodic" in kinds
    assert "temporal_truth" in kinds


def test_retrieve_context_returns_snippet(tmp_path: Path):
    cfg = _write_settings(tmp_path)
    settings = load_settings(cfg)
    engine = ConversationEngine(settings=settings, db_path=tmp_path / "memory.sqlite")

    engine.chat("Bugün moralim bozuk")
    snippets = engine.retrieve_context("moral")

    assert snippets, "retrieve_context en az bir özet döndürmeli"
