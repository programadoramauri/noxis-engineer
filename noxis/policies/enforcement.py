from __future__ import annotations
from pathlib import Path

from noxis.core.results import Result


class WritePolicyViolation(Exception):
    pass


class WritePolicyEnforcer:
    def __init__(self, *, allow_repo_write: bool, allowed_paths: list[str], root: Path) -> None:
        self.allow_repo_write = allow_repo_write
        self.allowed_paths = [root / p for p in allowed_paths]
        self.root = root

    def validate_write(self, path: Path) -> None:
        path = path.resolve()

        if not self.allow_repo_write:
            raise WritePolicyViolation("Repository write operations are disabled by policy.")

        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed.resolve())
                return
            except ValueError:
                continue

        raise WritePolicyViolation(
            f"Write tp `{path}` is not allowed by policy. Allowed paths: {self.allowed_paths}"
        )
