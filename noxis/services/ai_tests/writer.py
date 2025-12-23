from __future__ import annotations
from pathlib import Path


class TestFileWriter:
    def write(self, root: Path, files: dict[str, str]) -> list[str]:
        tests_dir = root / "tests"
        tests_dir.mkdir(exist_ok=True)

        written: list[str] = []

        for name, content in files.items():
            if "/" in name or "\\" in name:
                raise ValueError(f"Invalid test filename: {name}")

            path = tests_dir / name
            path.write_text(content, encoding="utf-8")
            written.append(str(path))
        return written
