from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ProjectModel:
    root_path: str
    repo_type: str  # "single" | "mono"
    languages_detected: list[str]
    signals: dict[str, list[str]]

    def to_yaml(self) -> str:
        payload = {
            "root_path": self.root_path,
            "repo_type": self.repo_type,
            "languages_detected": self.languages_detected,
            "signals": self.signals,
        }
        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)

    @classmethod
    def from_yaml(cls, path: Path) -> "ProjectModel":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        return cls(
            root_path=data["root_path"],
            repo_type=data["repo_type"],
            languages_detected=data.get("languages_detected", []),
            signals=data.get("signals", {}),
        )
