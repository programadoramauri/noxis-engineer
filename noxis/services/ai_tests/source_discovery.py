from __future__ import annotations
from pathlib import Path


class PythonSourceDiscovery:
    IGNORE_DIRS = {".venv", "venv", "__pycache__", ".noxis", ".git", "tests", "dist", "build"}

    def discover_files(self, root: Path) -> list[str]:
        files: list[str] = []

        for p in root.rglob("*.py"):
            if any(part in self.IGNORE_DIRS for part in p.parts):
                continue
            if p.name == "__init__.py":
                continue

            files.append(p)
        files.sort(key=lambda f: f.stat().st_size if f.exists() else 10**9)
        return files
