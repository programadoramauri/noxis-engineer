from __future__ import annotations

from noxis.context.discovery import discover_project
from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.plugins.manager import PluginManager
from noxis.plugins.base import ActionRequest
from noxis.storage.memory import MemoryStore


class ScanService:
    def run(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        try:
            workspace.state_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            return [Result.error("scan", f"Failed to create .noxis directory: {exc}")]

        try:
            project_model = discover_project(workspace.root)
        except Exception as exc:  # noqa: BLE001
            return [Result.error("scan", f"Project discovery failed: {exc}")]

        manager = PluginManager()
        plugins = manager.load_all()

        for plugin in plugins:
            applicability = plugin.detect(project_model)
            if not applicability.is_applicable:
                continue

            capabilities = {c.name for c in plugin.capabilities(project_model)}
            if "scan" not in capabilities:
                continue

            results.append(
                Result.info(
                    "scan",
                    f"Running scan for plugin: {plugin.id}",
                    ", ".join(applicability.reasons),
                )
            )

            plugin_results = plugin.run(
                ActionRequest(
                    capability="scan",
                    project=project_model,
                    options={},
                )
            )
            results.extend(plugin_results)

        # Persist project.yml
        try:
            workspace.project_file.write_text(project_model.to_yaml(), encoding="utf-8")
            results.append(
                Result.info(
                    "scan",
                    "Updated .noxis/project.yml.",
                    str(workspace.project_file),
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                Result.warn(
                    "scan", f"Could not update project.yml: {exc}", str(workspace.project_file)
                )
            )

        # Human summary
        langs = project_model.languages_detected or []
        results.append(
            Result.info(
                "scan",
                f"Detected languages: {', '.join(langs) if langs else 'none'}",
                project_model.root_path,
            )
        )

        results.append(
            Result.info(
                "scan",
                f"Repo type: {project_model.repo_type}",
                project_model.root_path,
            )
        )

        for group, items in (project_model.signals or {}).items():
            results.append(
                Result.info(
                    "scan",
                    f"Signals[{group}]: {', '.join(items)}",
                    project_model.root_path,
                )
            )

        # Persist state + history
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()

            payload = {
                "root_path": project_model.root_path,
                "repo_type": project_model.repo_type,
                "languages_detected": project_model.languages_detected,
                "signals": project_model.signals,
            }

            store.record_run("scan", payload=payload)
            store.set_state("last_scan", payload)

            results.append(
                Result.info(
                    "scan",
                    "Recorded scan run in memory.db.",
                    str(workspace.memory_db_file),
                )
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                Result.warn(
                    "scan",
                    f"Could not record scan state: {exc}",
                    str(workspace.memory_db_file),
                )
            )

        return results
