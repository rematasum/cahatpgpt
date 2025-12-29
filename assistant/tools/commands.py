import logging
import subprocess
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


def load_allowlist(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_allowed(command: str, allowlist_path: Path) -> str:
    allowlist = load_allowlist(allowlist_path)
    allowed_cmds = allowlist.get("commands", []) if allowlist else []
    if command not in allowed_cmds:
        raise PermissionError(f"Komut izinli değil: {command}")
    logger.info("Running allowed command: %s", command)
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    return result.stdout
