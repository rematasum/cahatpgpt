import os
from pathlib import Path

from .schemas import Settings
from .yaml_loader import load_yaml_text


def _load_yaml(path: Path):
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        text = path.read_text(encoding="utf-8")
        return load_yaml_text(text)
    else:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


def load_settings(path: str | Path) -> Settings:
    resolved = Path(path)
    data = _load_yaml(resolved)
    settings = Settings.from_dict(data)
    env = os.getenv("ASSISTANT_ENV")
    if env:
        settings.environment = env  # type: ignore[assignment]
    settings.ensure_dirs()
    return settings
