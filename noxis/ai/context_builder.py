from __future__ import annotations

from typing import Iterable

from typing import Any

from noxis.core.results import Result
from noxis.context.model import ProjectModel
from noxis.ai.history import summarize_scan_changes, summarize_doctor_changes


def build_ai_context(scan_state, doctor_state, scan_history, doctor_history) -> str:
    """
    Constrói um contexto enxuto e factual para IA.

    scan_state: dict salvo em project_state['last_scan']
    doctor_state: dict salvo em project_state['last_soctor']
    """

    lines: list[str] = []

    lines.append("You are an expert Python software engineer.")
    lines.append("Explain the current state of the project clearly and concisely.")
    lines.append("Be practical: list what is OK, what is missing, and what to do next.")
    lines.append("")

    # --- Scan state ---
    if not scan_state:
        lines.append("Scan summary: NOT AVAILABLE.")
        lines.append("Action: Ask the developer to run `noxis scan -p .` first.")
        lines.append("")
    else:
        root_path = scan_state.get("root_path", "unknown")
        repo_type = scan_state.get("repo_type", "unknown")
        languages = scan_state.get("languages_detected") or []
        signals = scan_state.get("signals") or {}
        lines.append("Project summary:")
        lines.append(f"- Root path: {root_path}")
        lines.append(f"- Repo type: {repo_type}")
        lines.append(f"- Languages detected: {', '.join(languages) if languages else 'none'}")
        lines.append("")

        if signals:
            lines.append("Detected signals:")
            for group, items in signals.items():
                if not items:
                    continue
                joined = ", ".join(str(x) for x in items)
                lines.append(f"- {group}: {joined}")
            lines.append("")

    # --- Doctor state ---
    if not doctor_state:
        lines.append("Doctor checks: NOT AVAILABLE")
        lines.append("Action: Ask the developer to run `noxis doctor -p .`. next.")
        lines.append("")
    else:
        results = doctor_state.get("results") or []
        lines.append("Doctor checks (from last doctor):")
        if not results:
            lines.append("- (no doctor results stored)")
        else:
            for r in results:
                sev = (r.get("severity") or "info").upper()
                msg = r.get("message") or ""
                loc = r.get("location") or ""
                if loc:
                    lines.append(f"- [{sev}] {msg} ({loc})")
                else:
                    lines.append(f"- [{sev}] {msg}")
        lines.append("")

    lines.append("Change summary (most recent vs previous):")
    lines.append("Scan changes:")
    lines.append(summarize_scan_changes(scan_history))
    lines.append("")
    lines.append("Doctor changes:")
    lines.append(summarize_doctor_changes(doctor_history))
    lines.append("")

    lines.append("Now explain the situation and recommend next steps.")
    return "\n".join(lines)
