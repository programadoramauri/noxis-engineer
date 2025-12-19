from __future__ import annotations

import json

from pathlib import Path

from noxis.context.discovery import discover_project
from noxis.core.results import Result
from noxis.policies.loader import load_default_policies_yaml
from noxis.storage.memory import MemoryStore
from noxis.core.workspace import Workspace

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
            
            results.append(Result.info("scan", "Recorded scan run in memory.db", str(workspace.memory_db_file)))
        except Exception as exc: # noqa: BLE001
            # não falha o scan por telemetria local
            results.append(Result.warn("scan", f"Could not record run in memory.db: {exc}", str(workspace.memory_db_file)))
        return results
