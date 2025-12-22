from __future__ import annotations

from noxis.context.loader import load_project
from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.plugins.manager import PluginManager
from noxis.plugins.base import ActionRequest
from noxis.storage.memory import MemoryStore


class DoctorService:
    def run(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        try:
            workspace.state_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            return [Result.error("doctor", f"Failed to create .noxis directory: {exc}")]

        try:
            project = load_project(workspace.root)
        except Exception as exc:  # noqa: BLE001
            return [Result.error("doctor", f"Project discovery failed: {exc}")]

        manager = PluginManager()
        plugins = manager.load_all()

        applicable_plugins: list = []

        for plugin in plugins:
            app = plugin.detect(project)
            if app.is_applicable:
                applicable_plugins.append(plugin)
                results.append(
                    Result.info(
                        "doctor",
                        f"Plugin applicable: {plugin.id} (confidence={app.confidence})",
                        ", ".join(app.reasons),
                    )
                )

        if not applicable_plugins:
            results.append(
                Result.warn(
                    "doctor",
                    "No applicable plugins found for this project.",
                    project.root_path,
                )
            )

        for plugin in applicable_plugins:
            capabilities = {c.name for c in plugin.capabilities(project)}
            if "doctor" not in capabilities:
                continue

            plugin_results = plugin.run(
                ActionRequest(
                    capability="doctor",
                    project=project,
                    options={},
                )
            )
            results.extend(plugin_results)

        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()

            payload = {
                "results": [
                    {"severity": r.severity, "message": r.message, "location": r.location}
                    for r in results
                ]
            }

            store.record_run("doctor", payload=payload)
            store.set_state("last_doctor", payload)
        except Exception:
            pass

        return results
