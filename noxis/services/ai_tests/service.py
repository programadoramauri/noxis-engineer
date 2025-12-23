from __future__ import annotations
from pathlib import Path
import shutil

from noxis.ai.provider import AIProvider
from noxis.context.loader import load_project
from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.storage.memory import MemoryStore

from .source_discovery import PythonSourceDiscovery
from .prompt_builder import AITestsPromptBuilder
from .writer import TestFileWriter
from .pytest_runner import PytestRunner


class AITestsService:
    def __init__(self) -> None:
        self.discovery = PythonSourceDiscovery()
        self.prompt_builder = AITestsPromptBuilder()
        self.writer = TestFileWriter()
        self.pytest = PytestRunner()
        self.provider = AIProvider()

    def run(self, workspace: Workspace) -> list[Result]:
        if not workspace.project_file.exists():
            return [Result.error("ai-tests", "project.yml not found. Run `noxis scan` first.")]
        project = load_project(workspace.root)

        if "python" not in (project.languages_detected or []):
            return [Result.warn("ai-tests", "Only Python projects are supported.")]

        if not shutil.which("pytest"):
            return [Result.error("ai-tests", "pytest not found")]

        py_files = self.discovery.discover_files(workspace.root)
        if not py_files:
            return [Result.warn("ai-tests", "No Python source directories found.")]

        target = py_files[0]  # MVP: exatamente 1 arquivo
        test_filename = self._test_filename_for_target(target, workspace.root)

        prompt = self.prompt_builder.build_for_file(
            project=project, target_file=target, root=workspace.root
        )

        generated = self.provider.generate_tests(prompt)

        if len(generated) != 1:
            merged = "\n\n".join(generated.values())
            generated = {test_filename: merged}
        else:
            content = next(iter(generated.values()))
            generated = {test_filename: content}

        try:
            written = self.writer.write(workspace.root, generated)
        except ValueError as exc:
            return [Result.error("ai-tests", str(exc))]

        ok, output = self.pytest.run(workspace.root)
        if not ok:
            return [Result.error("ai-tests", "Generated tests failed.", output)]

        self._persist_run(workspace, written, target)

        return [
            Result.info(
                "ai-tests", f"Generated and validated {len(written)} test files.", written[0]
            )
        ]

    def _test_filename_for_target(self, target: Path, root: Path) -> str:
        rel = target.relative_to(root).as_posix()
        base = rel.replace("/", "_").replace(".py", "")
        return f"test_{base}.py"

    def _persist_run(self, workspace: Workspace, files: list[str], target: Path) -> None:
        try:
            store = MemoryStore(workspace.memory_db_file)
            store.initialize()
            store.record_run(
                "ai-tests", payload={"generated_files": files, "target": target.as_posix()}
            )
        except Exception:
            pass
