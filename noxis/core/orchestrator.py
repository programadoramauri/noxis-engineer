from __future__ import annotations

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
