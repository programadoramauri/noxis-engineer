from __future__ import annotations
from pathlib import Path


class PythonSourceDiscovery:
    IGNORE_DIRS = {".venv", "venv", "__pycache__", ".noxis", ".git", "tests", "dist", "build"}
    IGNORE_FILES = {"__init__.py", "__main__.py"}
    DEPRIORITIZE_PATH_PARTS = {"services", "plugins", "policies", "context", "cli"}

    def discover_best_file(self, root: Path) -> Path | None:
        candidates: list[Path] = []
        for p in root.rglob("*.py"):
            if any(part in self.IGNORE_DIRS for part in p.parts):
                continue
            if p.name in self.IGNORE_FILES:
                continue
            candidates.append(p)
        if not candidates:
            return None

        scored = [(self._score(p), p) for p in candidates]
        scored.sort(key=lambda t: t[0], reverse=True)

        return scored[0][1]

    def _score(self, path: Path) -> int:
        score = 0

        name = path.name

        if name.startswith("_"):
            score -= 5
        if "__main__" in name:
            score -= 10

        if any(part in self.DEPRIORITIZE_PATH_PARTS for part in path.parts):
            score -= 3

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            return -100

        if len(lines) < 10:
            score -= 5
        else:
            score += min(len(lines) // 10, 10)  # até 10

        text = "\n".join(lines)

        if "class " in text:
            score += 5

        if "def " in text:
            score += 5

        return score
