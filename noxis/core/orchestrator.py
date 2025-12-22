from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

from noxis.ai.context_builder import build_ai_context
from noxis.ai.provider import AIProvider
from noxis.context.discovery import discover_project
from noxis.core import results
from noxis.core.project_state import ProjectState
from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.policies.loader import load_default_policies_yaml
from noxis.storage.memory import MemoryStore
from noxis.plugins.manager import PluginManager
from noxis.plugins.base import ActionRequest
from noxis.context.loader import load_project


class Orchestrator:
    # ---------------------------------------------------------------------
    # INIT
    # ---------------------------------------------------------------------

    def init_workspace(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        try:
            workspace.state_dir.mkdir(parents=True, exist_ok=True)
            results.append(
                Result.info("init", "Created/verified .noxis directory.", str(workspace.state_dir))
            )
        except Exception as exc:  # noqa: BLE001
            return [Result.error("init", f"Failed to create .noxis directory: {exc}")]

        results.extend(self._ensure_policies(workspace))
        results.extend(self._write_project(workspace))
        results.extend(self._ensure_memory_db(workspace))

        return results

    def _ensure_policies(self, workspace: Workspace) -> list[Result]:
        if workspace.policies_file.exists():
            return [
                Result.info("init", "policies.yml already exists.", str(workspace.policies_file))
            ]

        try:
            default_yaml = load_default_policies_yaml()
            workspace.policies_file.write_text(default_yaml, encoding="utf-8")
            return [
                Result.info(
                    "init", "Created policies.yml from defaults.", str(workspace.policies_file)
                )
            ]
        except Exception as exc:  # noqa: BLE001
            return [Result.error("init", f"Failed to write policies.yml: {exc}")]

    def _write_project(self, workspace: Workspace) -> list[Result]:
        try:
            project_model = discover_project(workspace.root)
            workspace.project_file.write_text(project_model.to_yaml(), encoding="utf-8")
            return [
                Result.info("init", "Created/updated project.yml.", str(workspace.project_file))
            ]
        except Exception as exc:  # noqa: BLE001
            return [Result.error("init", f"Failed to write project.yml: {exc}")]

    def _ensure_memory_db(self, workspace: Workspace) -> list[Result]:
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()
            return [Result.info("init", "Initialized memory.db.", str(workspace.memory_db_file))]
        except Exception as exc:  # noqa: BLE001
            return [Result.error("init", f"Failed to initialize memory.db: {exc}")]

    # ---------------------------------------------------------------------
    # SCAN (PLUGINIZED)
    # ---------------------------------------------------------------------

    def scan(self, workspace: Workspace) -> list[Result]:
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

    # ---------------------------------------------------------------------
    # DOCTOR (PLUGINIZED)
    # ---------------------------------------------------------------------

    def doctor(self, workspace: Workspace) -> list[Result]:
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

    # ---------------------------------------------------------------------
    # AI EXPLAIN
    # ---------------------------------------------------------------------

    def ai_explain(self, workspace: Workspace) -> str:
        project = load_project(workspace.root)
        if not workspace.project_file.exists():
            raise RuntimeError("project.yml not found. Run `noxis scan` first.")

        store = MemoryStore(workspace.memory_db_file)
        store.initialize()

        recent_scans = store.get_recent_runs("scan", limit=3)
        recent_doctors = store.get_recent_runs("doctor", limit=3)

        state = ProjectState(store)
        scan_state = state.last_scan()
        doctor_state = state.last_doctor()

        prompt = build_ai_context(
            scan_state=scan_state,
            doctor_state=doctor_state,
            scan_history=recent_scans,
            doctor_history=recent_doctors,
        )

        provider = AIProvider()
        response = provider.explain(prompt)

        try:
            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            store.record_ai_explanation(prompt_hash=prompt_hash, response=response)
        except Exception:
            pass

        return response

    def ai_tests(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        # 1. Garantir baseline
        if not workspace.project_file.exists():
            return [Result.error("ai-tests", "project.yml not found. Run `noxis scan first.`")]

        # 2. Carregar ProjectModel
        from noxis.context.loader import load_project

        project = load_project(workspace.root)

        if "python" not in (project.languages_detected or []):
            return [
                Result.warn(
                    "ai-tests",
                    "AI test generation is only supported for Python projects (for now).",
                )
            ]

        # 3. Verificar pytest
        if not shutil.which("pytest"):
            return [
                Result.error(
                    "ai-tests",
                    "pytest not found. Install pytest before generating tests.",
                )
            ]

        # 4. Descobrir código testável
        src_dirs = self._discover_python_sources(workspace.root)
        if not src_dirs:
            return [
                Result.warn(
                    "ai-tests",
                    "No Python source directories found. Expected at least one package or module directory.",
                )
            ]

        # 5, Construir prompt
        prompt = self._build_ai_tests_prompt(project, src_dirs)

        # 6. Chamar IA
        provider = AIProvider()
        generated = provider.generate_tests(prompt)

        # 7. Escrever arquivos
        tests_dir = workspace.root / "tests"
        tests_dir.mkdir(exist_ok=True)

        written_files = []
        for fname, content in generated.items():
            path = tests_dir / fname

            path.write_text(content, encoding="utf-8")
            written_files.append(str(path))

        results.append(
            Result.info(
                "ai-tests",
                f"Generated {len(written_files)} test files.",
                ", ".join(written_files),
            )
        )

        # 8. Executar pytest
        import subprocess

        proc = subprocess.run(
            ["pytest", "-q"],
            cwd=str(workspace.root),
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            results.append(
                Result.error(
                    "ai-tests",
                    "Generated tests failed.",
                    proc.stdout + "\n" + proc.stderr,
                )
            )
            return results
        results.append(Result.info("ai-tests", "All generated tests passed."))

        # 9. Persistir histórico
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()
            store.record_run(
                "ai-tests", payload={"generated_files": written_files, "sources": src_dirs}
            )
        except Exception:
            pass

        return results

    def _discover_python_sources(self, root: Path) -> list[str]:
        ignore = {".venv", "venv", "__pycache__", ".noxis", ".git", "tests", "dist", "build"}

        sources: list[str] = []

        for item in root.iterdir():
            if not item.is_dir():
                continue
            if item.name in ignore:
                continue

            has_py_files = any(p.suffix == ".py" for p in item.glob("*.py"))
            has_init = (item / "__init__.py").exists()

            if has_py_files or has_init:
                sources.append(str(item))
        return sources

    def _build_ai_tests_prompt(self, project, src_dirs: list[str]) -> str:
        lines = [
            "You are an expert Python test engineer.",
            "Generate pytest tests for the following project.",
            "",
            f"Project root: {project.root_path}",
            f"Source directories: {', '.join(src_dirs)}",
            "",
            "Rules",
            "- Do NOT modify production code",
            "- Write only pytest-compatible tests",
            "- Prefer simple, deterministic tests",
            "- Use mocks when necessary",
            "- Assume code is correct: test expected behavior",
            "",
            "Return files as JSON mapping filename -> content.",
        ]

        return "\n".join(lines)
