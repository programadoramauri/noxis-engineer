from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def state_dir(self) -> Path:
        return self.root / ".noxis"

    @property
    def project_file(self) -> Path:
        return self.state_dir / "project.yml"

    @property
    def policies_file(self) -> Path:
        return self.state_dir / "policies.yml"

    @property
    def memory_db_file(self) -> Path:
        return self.state_dir / "memory.db"
