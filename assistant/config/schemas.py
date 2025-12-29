from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class Paths:
    data_dir: Path
    db_file: Path
    log_dir: Path
    summaries_dir: Path


@dataclass
class LLMSettings:
    provider: Literal["ollama", "lmstudio", "dummy"]
    model: str
    temperature: float = 0.6
    max_tokens: int = 512
    base_url: str = "http://localhost:11434"


@dataclass
class EmbeddingSettings:
    backend: Literal["sentence_transformer", "dummy"]
    model_name: str
    device: Literal["cpu", "cuda", "auto"] = "auto"


@dataclass
class MemorySettings:
    top_k: int = 6
    min_similarity: float = 0.25
    decay_halflife_days: int = 30
    temporal_truth_key: str = "topic"


@dataclass
class ProfileSettings:
    refresh_turns: int = 5
    summary_max_tokens: int = 256


@dataclass
class SecuritySettings:
    allow_notes_dir: Path = Path("notes")
    allow_commands: Path = Path("config/allowlist.yaml")


@dataclass
class UISettings:
    stream: bool = True
    system_prompt: str = ""


@dataclass
class Settings:
    environment: Literal["dev", "prod", "test"]
    paths: Paths
    llm: LLMSettings
    embedding: EmbeddingSettings
    memory: MemorySettings
    profile: ProfileSettings
    security: SecuritySettings
    ui: UISettings

    @classmethod
    def from_dict(cls, data: dict) -> "Settings":
        return cls(
            environment=data.get("environment", "dev"),
            paths=Paths(**_map_path_fields(data["paths"])),
            llm=LLMSettings(**data["llm"]),
            embedding=EmbeddingSettings(**data["embedding"]),
            memory=MemorySettings(**data["memory"]),
            profile=ProfileSettings(**data["profile"]),
            security=SecuritySettings(**_map_path_fields(data["security"])),
            ui=UISettings(**data["ui"]),
        )

    def ensure_dirs(self) -> None:
        self.paths.data_dir.mkdir(parents=True, exist_ok=True)
        self.paths.log_dir.mkdir(parents=True, exist_ok=True)
        self.paths.summaries_dir.mkdir(parents=True, exist_ok=True)
        self.paths.db_file.parent.mkdir(parents=True, exist_ok=True)


def _map_path_fields(mapping: dict) -> dict:
    result = {}
    for key, value in mapping.items():
        result[key] = Path(value) if isinstance(value, str) else value
    return result
