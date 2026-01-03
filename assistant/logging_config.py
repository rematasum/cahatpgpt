import logging
import logging.config
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(log_dir: Path, environment: str = "dev") -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "assistant.log"

    console_level = "DEBUG" if environment == "dev" else "INFO"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": console_level,
                "rich_tracebacks": False,
                "markup": True,
                "show_time": False,
                "show_path": False,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "standard",
                "filename": str(log_file),
                "level": "DEBUG",
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if environment == "dev" else "INFO",
        },
    }

    logging.config.dictConfig(config)
