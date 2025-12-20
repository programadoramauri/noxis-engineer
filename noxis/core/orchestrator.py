from __future__ import annotations

import json
import shutil
import sys
import hashlib

from pathlib import Path

from noxis.context.discovery import discover_project
from noxis.core.results import Result
from noxis.policies.loader import load_default_policies_yaml
from noxis.storage.memory import MemoryStore
from noxis.core.workspace import Workspace
from noxis.ai.provider import AIProvider
from noxis.core.project_state import ProjectState
from noxis.ai.context_builder import build_ai_context

class Orchestrator:
    def init_workspace(self, workspace: Workspace) -> list [Result]:
        results: list[Result] = []

        # 1) Create .noxis/
        try:
            workspace.state_dir.mkdir(parents=True, exist_ok=True)
            results.append(Result.info("init", "Created/verified .noxis directory.", str(workspace.state_dir)))
        except Excetion as exc: # noqa: BLE001
            return [Result.error("init", f"Failed to create .noxis directory: {exc}")]

        # 2) Write policies.yml (if missing)
        results.extend(self._ensure_policies(workspace))

        # 3) Discovery and write project.yml
        results.extend(self._write_project(workspace))

        # 4) Init SQLite memory.db
        results.extend(self._ensure_memory_db(workspace))

        return results

    def _ensure_policies(self, workspace: Workspace) -> list[Result]:
        if workspace.policies_file.exists():
            return [Result.info("init", "policies.yml already exists.", str(workspace.policies_file))]

        try:
            default_yaml = load_default_policies_yaml()
            workspace.policies_file.write_text(default_yaml, encoding="utf-8")
            return [Result.info("init", "Created policies.yml from defaults.", str(workspace.policies_file))]
        except Exception as exc: # noqa: BLE001
            return [Result.error("init", f"Failed to write policies.yml: {exc}")]

    def _write_project(self, workspace: Workspace) -> list[Result]:
        try:
            project_model = discover_project(workspace.root)
            content = project_model.to_yaml()
            workspace.project_file.write_text(content, encoding="utf-8")
            return [Result.info("init", "Created/updated project.yml.", str(workspace.project_file))]
        except Exception as exc: # noqa: BLE001
            return [Result.error("init", f"Failed to write project.yml: {exc}")]

    def _ensure_memory_db(self, workspace: Workspace) -> list[Result]:
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()
            return [Result.info("init", "initialize memory.db.", str(workspace.memory_db_file))]
        except Exception as exc: # noqa: BLE001
            return [Result.error("init", f"Failed to initialize memory.db: {exc}")]

    def _doctor_python(self) -> list[Result]:
        results: list[Result] = []

        #pip
        if shutil.which("pip"):
            results.append(
                Result.info(
                    "doctor",
                    "pip is available.",
                    shutil.which("pip",)
                )
            )
        else:
            results.append(
                Result.error(
                    "doctor",
                    "pip not found. Install pip to manage Python dependencies."
                )
            )

        if shutil.which("ruff"):
            results.append(
                Result.info(
                    "doctor",
                    "ruff is available.",
                    shutil.which("ruff",)
                )
            )
        else:
            results.append(
                Result.warn(
                    "doctor",
                    "ruff not found. Linting wil be unavailable.",
                    "pip install ruff",
                )
            )

        if shutil.which("pytest"):
            results.append(
                Result.info(
                    "doctor",
                    "pytest is available.",
                    shutil.which("pytest",)
                )
            )
        else:
            results.append(
                Result.warn(
                    "doctor",
                    "pytest not found. Tests cannot be executed.",
                    "pip install pytest",
                )
            )
        return results

    def scan(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        # Garante .noxis/ (scan pode ser rodado antes do init)
        try:
            workspace.state_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc: # noqa BLE001
            return [Result.error("scan", f"Project discovery failed: {exc}")]
        
        # Descoberta
        try:
            project_model = discover_project(workspace.root)
        except Exception as exc: # noqa: BLE001
            return [Result.error("scan", f"Project discovery failed: {exc}")]
        
        # Persistir baseline do projeto (.noxis/project.yml)
        try:
            workspace.project_file.write_text(
                project_model.to_yaml(),
                encoding="utf-8"
            )
            results.append(
                Result.info(
                    "scan",
                    "Updated .noxis/project.yml.",
                    str(workspace.project_file),
                )
            )
        except Exception as exc: # noqa BLE001
            results.append(
                Result.warn(
                    "scan",
                    f"Could not update project.yml: {exc}",
                    str(workspace.project_file)
                )
            )

        # Resultados humanos (úteis no dia 1)
        langs = project_model.languages_detected or []
        results.append(
            Result.info(
                "scan",
                f"Detected languages: {', '.join(langs) if langs else 'none'}",
                project_model.root_path,
            )
        )

        results.append(Result.info("scan", f"Repo type: {project_model.repo_type}", project_model.root_path))

        # Sinais detectados (arquivos-chave)
        signals = project_model.signals or {}
        if not signals:
            results.append(
                Result.warn(
                    "scan",
                    "No known project signals detected",
                    project_model.root_path
                )
            )
        else:
            for group, items in signals.items():
                results.append(
                    Result.info(
                        "scan",
                        f"Signals[{group}]: {', '.join(items)}",
                        project_model.root_path
                    )
                )

        # Persistência leve para auto-alimentação (histórico)
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize() #idempotente
            store.record_run(
                command="scan",
                payload={
                    "root_path": project_model.root_path,
                    "repo_type": project_model.repo_type,
                    "languages_detected": project_model.languages_detected,
                    "signals": project_model.signals,
                }
            )

            store.set_state(
                "last_scan",
                {
                    "root_path": project_model.root_path,
                    "repo_type": project_model.repo_type,
                    "languages_detected": project_model.languages_detected,
                    "signals": project_model.signals
                }
            )
            
            results.append(Result.info("scan", "Recorded scan run in memory.db", str(workspace.memory_db_file)))
        except Exception as exc: # noqa: BLE001
            # não falha o scan por telemetria local
            results.append(Result.warn("scan", f"Could not record run in memory.db: {exc}", str(workspace.memory_db_file)))
        return results

    def doctor(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        python_version = sys.version.split()[0]
        results.append(
            Result.info(
                "doctor",
                f"Python detected: {python_version}",
                sys.executable,
            )
        )

        venv_path = workspace.root / ".venv"
        if venv_path.exists():
            results.append(
                Result.info(
                    "doctor",
                    "Virtual environment detected (.venv).",
                    str(venv_path),
                )
            )
        else:
            results.append(
                Result.warn(
                    "doctor",
                    "No project.yml found. Run `noxis scan` first.",
                    str(workspace.project_file)
                )
            )
            return results

        try:
            project_yaml = workspace.project_file.read_text(encoding="utf-8")
        except Exception as exc: # noqa: BLE001
            results.append(
                Result.error(
                    "doctor",
                    f"Failed to read project.yml: {exc}",
                    str(workspace.project_file)
                )
            )
        # Heuristica simples: detectar python no baseline
        if "python" in project_yaml:
            results.extend(self._doctor_python())

        store = MemoryStore(workspace.memory_db_file)
        store.set_state(
            "last_doctor",
            {
                "results": [
                    {
                        "severity": r.severity,
                        "message": r.message,
                        "location": r.location
                    }
                    for r in results
                ]
            }
        )

        return results

    def ai_explain(self, workspace:Workspace) -> str:
        # 1. Garantir baseline
        if not workspace.project_file.exists():
            raise RuntimeError("project.yml not found. Run `noxis scan` first.")

        store = MemoryStore(workspace.memory_db_file)
        store.initialize()

        state = ProjectState(store)

        scan_state = state.last_scan()
        doctor_state = state.last_doctor()

        # 4. Construir contexto para IA
        prompt = build_ai_context(scan_state=scan_state, doctor_state=doctor_state)

        # 5. Chamar provider
        provider = AIProvider()
        response = provider.explain(prompt)

        # 6. Persistir na memória
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()

            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()

            store.record_ai_explanation(
                prompt_hash=prompt_hash,
                response=response
            )
        except Exception:
            # IA nunca quebra fluxo principal
            pass
        return response
