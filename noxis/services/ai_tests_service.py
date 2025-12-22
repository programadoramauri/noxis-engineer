from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from noxis.ai.provider import AIProvider
from noxis.context.loader import load_project
from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.storage.memory import MemoryStore


class AITestsService:
    def run(self, workspace: Workspace) -> list[Result]:
        results: list[Result] = []

        # 1. Garantir baseline
        if not workspace.project_file.exists():
            return [Result.error("ai-tests", "project.yml not found. Run `noxis scan` first.")]

        project = load_project(workspace.root)

        if "python" not in (project.languages_detected or []):
            return [
                Result.warn(
                    "ai-tests",
                    "AI test generation is only supported for Python projects (for now).",
                )
            ]

        # 2. Verificar pytest
        if not shutil.which("pytest"):
            return [
                Result.error(
                    "ai-tests", "pytest not found. Install pytest before generating tests."
                )
            ]

        # 3. Descobrir código Python
        src_dirs = self._discover_python_sources(workspace.root)
        if not src_dirs:
            return [
                Result.warn(
                    "ai-tests",
                    "No Python source directories found. Expected at least one package or module directory.",
                )
            ]

        # 4. Construir prompt
        prompt = self._build_ai_tests_prompt(project, src_dirs)

        # 5. Chamar IA
        provider = AIProvider()
        generated = provider.generate_tests(prompt)

        # 6. Escrever arquivos
        tests_dir = workspace.root / "tests"
        tests_dir.mkdir(exist_ok=True)

        written_files: list[str] = []
        for fname, content in generated.items():
            # Guardrail básico
            if "/" in fname or "\\" in fname:
                return [
                    Result.error(
                        "ai-tests",
                        f"Generated {len(written_files)} test files.",
                        ", ".join(written_files),
                    )
                ]

            path = tests_dir / fname
            path.write_text(content, encoding="utf-8")
            written_files.append(str(path))

        results.append(
            Result.info(
                "ai-tests", f"Generated {len(written_files)} test files.", ", ".join(written_files)
            )
        )

        # 7. Executar pytest
        proc = subprocess.run(
            ["pytest", "-q", "tests"],
            cwd=str(workspace.root),
            capture_output=True,
            text=True,
        )

        if proc.returncode != 0:
            results.append(
                Result.error(
                    "ai-tests", "Generated tests failed.", proc.stdout + "\n" + proc.stderr
                )
            )
            return results

        # 8. Persistir histórico
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()
            store.record_run(
                "ai-tests", payload={"generated_files": written_files, "sources": src_dirs}
            )
        except Exception:
            pass
        return results

    # ------------------------------------------------------
    # Helpers (extraídos do Orchestrator)
    # ------------------------------------------------------

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
