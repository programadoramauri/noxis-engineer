from __future__ import annotations

from pathlib import Path
from noxis.ai.provider import AIProvider


class AITestRepairLoop:
    def __init__(self, provider: AIProvider, max_attempts: int = 2) -> None:
        self.provider = provider
        self.max_attempts = max_attempts

    def attempt_repair(
        self,
        *,
        project,
        target_file: Path,
        test_file: Path,
        pytest_error: str,
        root: Path,
    ) -> dict[str, str] | None:
        """
        Returns new {filename: content} or None if repair failed.
        """
        prompt = self._build_prompt(
            project=project,
            target_file=target_file,
            test_file=test_file,
            pytest_error=pytest_error,
            root=root,
        )

        response = self.provider.generate_tests(prompt)
        if not response:
            return None

        content = "\n\n".join(response.values())
        return {test_file.name: content}

    def _build_prompt(
        self,
        *,
        project,
        target_file: Path,
        test_file: Path,
        pytest_error: str,
        root: Path,
        max_chars: int = 12000,
    ) -> str:
        target_code = target_file.read_text(encoding="utf-8", errors="replace")
        test_code = test_file.read_text(encoding="utf-8", errors="replace")

        if len(target_code) > max_chars:
            target_code = target_code[:max_chars] + "\n# ... truncated ..."
        if len(test_code) > max_chars:
            test_code = test_code[:max_chars] + "\n ... truncated ..."

        return "\n".join(
            [
                "You are an expert Python test engineer.",
                "The following pytest FAILED.Fix the test WITHOUT modifying production code.",
                "",
                "Rules:",
                "- Do NOT change production code",
                "- Fix only the test",
                "- Keep tests deterministic",
                "- Return ONLY a JSON mapping filename -> content",
                "",
                f"Project root: {project.root_path}",
                "",
                "### TARGET FILE",
                target_file.relative_to(root).as_posix(),
                target_code,
                "",
                "### FAILED TEST FILE",
                test_file.name,
                test_code,
                "",
                "### PYTEST ERROR OUTPUT",
                pytest_error,
            ]
        )
