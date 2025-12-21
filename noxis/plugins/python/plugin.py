from __future__ import annotations

import shutil
import sys

from noxis.core import results
from noxis.core.results import Result
from noxis.context.model import ProjectModel
from noxis.plugins.base import ActionRequest, Applicability, CapabilitySpec, Plugin


class PythonPlugin(Plugin):
    id = "python"
    version = "0.1.0"
    display_name = "Python"
    supported_languages = ["python"]

    def detect(self, project: ProjectModel) -> Applicability:
        # Heuristica: linguagem detectada pelo scan
        if "python" in (project.languages_detected or []):
            return Applicability(
                is_applicable=True, confidence=1.0, reasons=["Python detected by scan"]
            )

        if project.signals.get("python"):
            return Applicability(
                is_applicable=True,
                confidence=0.7,
                reasons=["Python signals found"],
            )

        return Applicability(
            is_applicable=False,
            confidence=0.0,
            reasons=["No Python signals detected"],
        )

    def capabilities(self, project: ProjectModel) -> list[CapabilitySpec]:
        return [
            CapabilitySpec(
                name="doctor",
                description="Check Python tooling readiness (pip/ruff/pytest).",
                kind="deterministic",
                default_enabled=True,
            ),
            CapabilitySpec(
                name="scan",
                description="Detect Python-specific signals",
            ),
        ]

    def run(self, request: ActionRequest) -> list[Result]:
        handlers = {
            "scan": lambda: self._scan(request.project),
            "doctor": self._doctor,
        }

        handler = handlers.get(request.capability)
        if not handler:
            return [
                Result.warn(request.capability, f"Capability not supported by plugin '{self.id}'")
            ]
        return handler()

    def _doctor(self) -> list[Result]:
        results: list[Result] = []

        python_version = sys.version.split()[0]
        results.append(Result.info("doctor", f"Python detected: {python_version}", sys.executable))

        # pip
        pip_path = shutil.which("pip")
        if pip_path:
            results.append(Result.info("doctor", "pip is avalilable.", pip_path))
        else:
            results.append(
                Result.error("doctor", "pip not found. Install pip to manage Python dependencies.")
            )

        # ruff
        ruff_path = shutil.which("ruff")
        if ruff_path:
            results.append(Result.info("doctor", "ruff is avalilable", ruff_path))
        else:
            results.append(
                Result.warn(
                    "doctor", "ruff not found. Linting will be unavalilable", "pip install ruff"
                )
            )

        # pytest
        pytest_path = shutil.which("pytest")
        if pytest_path:
            results.append(Result.info("doctor", "pytest is available.", pytest_path))
        else:
            results.append(
                Result.warn(
                    "doctor", "pytest not found. Tests cannot be executed.", "pip install pytest"
                )
            )

        return results

    def _scan(self, project: ProjectModel) -> list[Result]:
        results: list[Result] = []

        signals = project.signals.setdefault("python", [])

        for fname in ["pyproject.toml", "requirement.txt", "setup.py", "Pipfile"]:
            path = f"{project.root_path}/{fname}"
            if path not in signals:
                import os

                if os.path.exists(path):
                    signals.append(fname)
                    results.append(Result.info("scan", f"Detected Python signal: {fname}", path))
        if not results:
            results.append(
                Result.info(
                    "scan", "No additional Python-specific signals detected.", project.root_path
                )
            )
        return results
