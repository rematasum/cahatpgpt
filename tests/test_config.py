from pathlib import Path
from assistant.config.loader import load_settings


def test_load_settings(tmp_path: Path):
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
          top_k: 2
          min_similarity: 0.1
          decay_halflife_days: 10
          temporal_truth_key: topic
        profile:
          refresh_turns: 2
          summary_max_tokens: 10
        security:
          allow_notes_dir: notes
          allow_commands: config/allowlist.yaml
        ui:
          stream: false
          system_prompt: test
        """,
        encoding="utf-8",
    )
    settings = load_settings(cfg)
    assert settings.environment == "test"
    assert settings.paths.data_dir.exists()
    assert settings.paths.db_file.parent.exists()
