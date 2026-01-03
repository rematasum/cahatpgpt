import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from assistant.config.loader import load_settings
from assistant.logging_config import setup_logging
from assistant.services.conversation import ConversationEngine
from assistant.tools.notes import ingest_notes
from assistant.tools.commands import run_allowed

app = typer.Typer(add_completion=False)
console = Console()


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def chat(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Ayar dosyası (opsiyonel, yoksa varsayılan kullanılır)"
    ),
    config_path: Optional[Path] = typer.Argument(
        None, help="Ayar dosyası (opsiyonel, --config yerine kullanılabilir)"
    ),
    message: Optional[str] = typer.Option(
        None, help="Tek seferlik mesaj (boşsa etkileşimli mod)"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="LLM ve hafıza adımlarını ayrıntılı göster"),
):
    extra_cfg = Path(ctx.args[0]) if ctx.args else None
    chosen_config = config or config_path or extra_cfg or Path("config/settings.yaml")
    settings = load_settings(chosen_config)
    setup_logging(settings.paths.log_dir, environment=settings.environment, verbose=verbose)
    engine = ConversationEngine(settings=settings)
    console.print(Panel("Mustafa'nın Yerel Asistanı - Tek Akış Sohbet"))

    def handle_turn(user_text: str) -> None:
        response = engine.chat(user_text, verbose=verbose)
        console.print(f"[bold green]Asistan:[/bold green] {response.content}")

    if message:
        handle_turn(message)
        raise typer.Exit()

    while True:
        user_text = console.input("[bold cyan]Mustafa> ")
        if user_text.strip().lower() in {"quit", "exit"}:
            break
        handle_turn(user_text)


@app.command("ingest-notes")
def ingest_notes_cmd(
    path: Optional[Path] = typer.Option(None, "--path", "-p", help="Not dizini"),
    path_arg: Optional[Path] = typer.Argument(
        None, help="Not dizini (opsiyonel pozisyonel kullanım için)"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Ayar dosyası (opsiyonel, yoksa varsayılan kullanılır)"
    ),
    config_path: Optional[Path] = typer.Argument(
        None, help="Ayar dosyası (opsiyonel, --config yerine kullanılabilir)", hidden=True
    ),
    ):
    chosen_path = path or path_arg
    if not chosen_path:
        raise typer.BadParameter("Not dizini belirtilmeli (--path veya pozisyonel).")
    chosen_config = config or config_path or Path("config/settings.yaml")
    settings = load_settings(chosen_config)
    setup_logging(settings.paths.log_dir, environment=settings.environment)
    engine = ConversationEngine(settings=settings)
    count = ingest_notes(
        root=chosen_path,
        allowed_dirs=[settings.security.allow_notes_dir],
        store=engine.memory_store,
        embedder=engine.embedding,
    )
    console.print(f"{count} not eklendi")


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run_command(
    ctx: typer.Context,
    command: str = typer.Argument(..., help="İzinli komut"),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Ayar dosyası (opsiyonel, yoksa varsayılan kullanılır)"
    ),
    config_path: Optional[Path] = typer.Argument(
        None, help="Ayar dosyası (opsiyonel, --config yerine kullanılabilir)", hidden=True
    ),
):
    extra_cfg = Path(ctx.args[0]) if ctx.args else None
    chosen_config = config or config_path or extra_cfg or Path("config/settings.yaml")
    settings = load_settings(chosen_config)
    setup_logging(settings.paths.log_dir, environment=settings.environment)
    output = run_allowed(command=command, allowlist_path=settings.security.allow_commands)
    console.print(output)


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def profile(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="Ayar dosyası (opsiyonel, yoksa varsayılan kullanılır)"
    ),
    config_path: Optional[Path] = typer.Argument(
        None, help="Ayar dosyası (opsiyonel, --config yerine kullanılabilir)", hidden=True
    ),
):
    extra_cfg = Path(ctx.args[0]) if ctx.args else None
    chosen_config = config or config_path or extra_cfg or Path("config/settings.yaml")
    settings = load_settings(chosen_config)
    setup_logging(settings.paths.log_dir, environment=settings.environment)
    engine = ConversationEngine(settings=settings)
    summary = engine.profile_summary()
    console.print(summary)


@app.command()
def plan():
    with open(Path("docs/PLAN.md"), "r", encoding="utf-8") as f:
        console.print(f.read())


@app.command()
def checklist():
    with open(Path("docs/CHECKLIST.md"), "r", encoding="utf-8") as f:
        console.print(f.read())


if __name__ == "__main__":
    app()
