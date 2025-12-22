from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from noxis.core import workspace
from noxis.core import orchestrator
from noxis.core import results
from noxis.core.orchestrator import Orchestrator
from noxis.core.results import print_human_results
from noxis.core.workspace import Workspace

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.callback()
def main() -> None:
    """
    Noxis - engenheiro companheiro local-first.
    """
    # Callback raiz: não faz nada por enquanto
    pass


@app.command()
def init(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Caminho do projeto (root)",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Inicializa a Noxis no repositório alvo criando .noxis/ com project.yml, policies.yml e memory.db.
    """
    workspace = Workspace(root=path.resolve())
    orchestrator = Orchestrator()

    results = orchestrator.init_workspace(workspace)

    print_human_results(results, console)
    # exit code MVP: se houver error, retorna != 0
    if any(r.severity == "error" for r in results):
        raise typer.Exit(code=1)


@app.command()
def scan(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Caminho do projeto (root).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Analise o repositório e imprime um relatório do contexto (ProjectModel).
    """
    workspace = Workspace(root=path)
    orchestrator = Orchestrator()

    results = orchestrator.scan(workspace)
    print_human_results(results, console)
    if any(r.severity == "error" for r in results):
        raise typer.Exit(code=1)


@app.command()
def doctor(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Caminho do projeto (root).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Verifica se o ambiente está adequado para o projeto.
    """
    workspace = Workspace(root=path)
    orchestrator = Orchestrator()

    results = orchestrator.doctor(workspace)

    print_human_results(results, console)
    if any(r.severity == "error" for r in results):
        raise typer.Exit(code=1)


@app.command("ai-explain")
def ai_explain(
    path: Path = typer.Option(
        Path("."),
        "--path",
        "-p",
        help="Caminho do projeto(root).",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """
    Explica o estado atual do projeto com base em scan e doctor.
    """
    workspace = Workspace(root=path)
    orchestrator = Orchestrator()

    explanation = orchestrator.ai_explain(workspace)

    console.print("\n[bold cyan]AI Explanation[/bold cyan]\n")
    console.print(explanation)


@app.command("ai-tests")
def ai_tests(
    path: Path = typer.Option(Path("."), "--path", "-p", help="Project root path"),
):
    workspace = Workspace(root=path)
    orchestrator = Orchestrator()
    results = orchestrator.ai_tests(workspace)

    for r in results:
        console.print(r.to_rich())
