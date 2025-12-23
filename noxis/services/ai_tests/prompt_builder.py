from __future__ import annotations
from pathlib import Path


class AITestsPromptBuilder:
    def build_for_file(
        self,
        project,
        target_file: Path,
        root: Path,
        max_chars: int = 12000,
    ) -> str:
        rel_path = target_file.relative_to(root).as_posix()
        code = target_file.read_text(encoding="utf-8", errors="replace")

        if len(code) > max_chars:
            code = code[:max_chars] + "\n\n# ... truncated ...\n"
        return "\n".join(
            [
                "You are an expert Python test engineer.",
                "Generate pytest test for the following project.",
                "",
                "Rules:",
                "- Do NOT modify production code",
                "- Write fast, deterministic tests",
                "- Focus on public functions/classes",
                "- Use mocks only when strictly necessary",
                "- Return ONLY a JSON object mapping filename -> content",
                "- Filename must ne a single .py file (no directories)",
                "",
                f"Project root: {project.root_path}",
                f"Target module: {rel_path}",
                "",
                f"### FILE: {rel_path}",
                code,
            ]
        )
