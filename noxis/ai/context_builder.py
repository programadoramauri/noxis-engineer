from __future__ import annotations

from typing import Iterable

from noxis.core.results import Result
from noxis.context.model import ProjectModel

def build_ai_context(
    project: ProjectModel,
        doctor_results: Iterable[Result],
) -> str:
    """
    Constrói um contexto enxuto e factual para IA.
    """

    lines: list[str] = []

    lines.append("You are an expert Python software engineer.")
    lines.append("Explain the current state of the project clearly and concisely.")
    lines.append("")
    lines.append("Project summary:")
    lines.append(f"- Root path: {project.root_path}")
    lines.append(f"- Repo type: {project.repo_type}")
    lines.append(f"- Languages detected: {', '.join(project.languages_detected)}")
    lines.append("")

    if project.signals:
        lines.append("Detected signals:")
        for group, items in project.signals.items():
            lines.append(f"- {group}: {', '.join(items) }")

        lines.append("")

    lines.append("Doctor checks:")
    for r in doctor_results:
        lines.append(f"- [{r.severity.upper()}] {r.message}")
    lines.append("")
    lines.append(
        "Explain what is working, what is missing, and what the developer should do next."
    )
    return "\n".join(lines)
