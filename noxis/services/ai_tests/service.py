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
from .repair_loop import AITestRepairLoop
from .target_registry import AITestTargetRegistry


class AITestsService:
    def __init__(self) -> None:
        self.discovery = PythonSourceDiscovery()
        self.prompt_builder = AITestsPromptBuilder()
        self.writer = TestFileWriter()
        self.pytest = PytestRunner()
        self.provider = AIProvider()
        self.repair = AITestRepairLoop(self.provider)

    def run(self, workspace: Workspace, *, force: bool = False) -> list[Result]:
        results: list[Result] = []
        if not workspace.project_file.exists():
            return [Result.error("ai-tests", "project.yml not found. Run `noxis scan` first.")]
        project = load_project(workspace.root)

        if "python" not in (project.languages_detected or []):
            return [Result.warn("ai-tests", "Only Python projects are supported.")]

        if not shutil.which("pytest"):
            return [Result.error("ai-tests", "pytest not found")]

        store = MemoryStore(workspace.memory_db_file)
        store.initialize()
        registry = AITestTargetRegistry(store)

        target = self._select_target(workspace.root, registry, force=force)
        if not target:
            return [
                Result.warn(
                    "ai-tests",
                    "No new Python files available for test generation.",
                )
            ]

        if force:
            results.append(
                Result.info(
                    "ai-tests",
                    "Force mode enabled: regenerating tests for an already tested target.",
                )
            )

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

        attempts = 0
        while not ok and attempts < self.repair.max_attempts:
            attempts += 1

            repaired = self.repair.attempt_repair(
                project=project,
                target_file=target,
                test_file=Path(written[0]),
                pytest_error=output,
                root=workspace.root,
            )

            if not repaired:
                break

            self.writer.write(workspace.root, repaired)
            ok, output = self.pytest.run(workspace.root)

        if not ok:
            return [
                Result.error(
                    "ai-tests",
                    f"Tests failed after {attempts} repair attempt(s).",
                    output,
                )
            ]

        registry.mark_tested(target)
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

    def _select_target(
        self, root: Path, registry: AITestTargetRegistry, *, force: bool
    ) -> Path | None:
        ranked = self.discovery.discover_ranked_files(root)

        if not ranked:
            return None

        if force:
            return ranked[0]

        for candidate in ranked:
            if not registry.is_tested(candidate):
                return candidate

        return None
