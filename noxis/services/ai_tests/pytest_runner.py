from __future__ import annotations
import subprocess
from pathlib import Path


class PytestRunner:
    def run(self, root: Path) -> tuple[bool, str]:
        proc = subprocess.run(
            ["pytest", "-q", "tests"],
            cwd=str(root),
            capture_output=True,
            text=True,
        )

        output = proc.stdout + "\n" + proc.stderr
        return proc.returncode == 0, output
