from __future__ import annotations
from pathlib import Path
import re


class AITestsPromptBuilder:
    PUBLIC_FUNC_RE = re.compile(r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)
    PUBLIC_CLASS_RE = re.compile(r"^class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE)

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

        public_funcs = [f for f in self.PUBLIC_FUNC_RE.findall(code) if not f.startswith("_")]
        public_classes = [c for c in self.PUBLIC_CLASS_RE.findall(code) if not c.startswith("_")]

        api_lines: list[str] = []
        for c in public_classes:
            api_lines.append(f"- class {c}")
        for f in public_funcs:
            api_lines.append(f"- def {f}(...)")

        api_section = (
            "\n".join(api_lines) if api_lines else "No public functions or classes were detected."
        )

        return "\n".join(
            [
                "You are an expert Python test engineer.",
                "",
                "Your task is to write pytest tests for ONE specific Python source file.",
                "",
                "========================",
                "TARGET",
                "========================",
                f"Project root: {project.root_path}",
                f"Target file: {target_file}",
                f"Repository type: {project.repo_type}",
                "",
                "========================",
                "STRICT RULES (MANDATORY)",
                "========================",
                "You MUST follow ALL rules below. Violating any rule makes the answer invalid.",
                "",
                "1. Test ONLY the PUBLIC BEHAVIOR of the target file.",
                "   - Do NOT access database tables directly.",
                "   - Do NOT use sqlite3, cursors or raw SQL unless the target file exposes them publicly.",
                "   - Do NOT inspect private attributes or internal state.",
                "",
                "2. Use ONLY public methods and documented behavior.",
                "   - If behavior is unclear, write conservative tests that assert return values, not implementation details.",
                "   - Do NOT invent exceptions that are not explicity raised by the code.",
                "",
                "3. Do NOT write trivial or placeholder tests.",
                "   - NEVER use `assert True`.",
                "   - Every test must validate meaningful behavior.",
                "",
                "4. Do NOT modify production code.",
                "   - Write tests only.",
                "",
                "5. File and output rules:",
                "   - Return a SINGLE pytest file.",
                "   - The filename MUST be a plain filename (example: test_memoty_store.py).",
                "   - Do NOT include directories in filenames.",
                "   - The content MUST returned values instead of raised exceptions.",
                "",
                "6. Error handling:",
                "   - Do NOT expect JSONDecodeError, sqlite3.Error, or similar exception unless the code raises them.",
                "   - Prefer asserting returned values instesad of raised of raised exceptions.",
                "",
                "7. Imports:",
                "   - Import ONLY what is required."
                "   - All imports used in the test MUST be explicitly declared.",
                "",
                "=========================",
                "TEST DESIGN GUIDELINES",
                "=========================",
                "- Prefer small, focused tests.",
                "- Use pytest fixtures when appropriate.",
                "- Tests must pass against the current implementation.",
                "- Assume the implementation is correct; your job is to validate behavior, not redesigm it.",
                "",
                "=========================",
                "OUTPUT FORMAT (CRITICAL)",
                "=========================",
                "Return ONLY a valid JSON object in this exact shape:",
                "",
                "{",
                '   "test_filename.py": "<full pytest file content>"',
                "}",
                "",
                "Do NOT include explanations, markdown, or comments outside the JSON.",
                "Do NOT include ``` fences.",
            ]
        )
