from __future__ import annotations
from pathlib import Path

from noxis.policies.enforcement import WritePolicyEnforcer, WritePolicyViolation
from noxis.policies.loader import load_policies
from noxis.core.results import Result


class TestFileWriter:
    def write(self, root: Path, files: dict[str, str]) -> list[str]:
        policies = load_policies(root)

        enforcer = WritePolicyEnforcer(
            allow_repo_write=policies.rules.allow_repo_write,
            allowed_paths=policies.rules.allowed_write_paths,
            root=root,
        )

        written: list[str] = []

        for filename, content in files.items():
            path = (root / "tests" / filename).resolve()

            try:
                enforcer.validate_write(path)
            except WritePolicyViolation as exc:
                raise ValueError(str(exc))

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(str(path))

        return written
