import json
import logging
from pathlib import Path
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


@app.command()
def chat(
    config: Path = typer.Option(Path("config/settings.yaml"), help="Ayar dosyası"),
    message: str | None = typer.Option(None, help="Tek seferlik mesaj (boşsa etkileşimli mod)"),
):
    settings = load_settings(config)
    setup_logging(settings.paths.log_dir)
    engine = ConversationEngine(settings=settings)
    console.print(Panel("Mustafa'nın Yerel Asistanı - Tek Akış Sohbet"))

    def handle_turn(user_text: str) -> None:
        response = engine.chat(user_text)
        console.print(f"[bold green]Asistan:[/bold green] {response.content}")

    if message:
        handle_turn(message)
        raise typer.Exit()

    while True:
        user_text = console.input("[bold cyan]Mustafa> ")
        if user_text.strip().lower() in {"quit", "exit"}:
            break
        handle_turn(user_text)


@app.command()
def ingest_notes_cmd(
    path: Path = typer.Argument(..., help="Not dizini"),
    config: Path = typer.Option(Path("config/settings.yaml")),
):
    settings = load_settings(config)
    setup_logging(settings.paths.log_dir)
    engine = ConversationEngine(settings=settings)
    count = ingest_notes(
        root=path,
        allowed_dirs=[settings.security.allow_notes_dir],
        store=engine.memory_store,
        embedder=engine.embedding,
    )
    console.print(f"{count} not eklendi")


@app.command()
def run_command(
    command: str = typer.Argument(..., help="İzinli komut"),
    config: Path = typer.Option(Path("config/settings.yaml")),
):
    settings = load_settings(config)
    setup_logging(settings.paths.log_dir)
    output = run_allowed(command=command, allowlist_path=settings.security.allow_commands)
    console.print(output)


@app.command()
def profile(
    config: Path = typer.Option(Path("config/settings.yaml")),
):
    settings = load_settings(config)
    setup_logging(settings.paths.log_dir)
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
