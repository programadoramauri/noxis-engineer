from __future__ import annotations

from importlib.resources import files
from pathlib import Path
import yaml
from dataclasses import dataclass


def load_default_policies_yaml() -> str:
    # lê o defaults.yml empacotado
    data = files("noxis.policies").joinpath("defaults.yml").read_text(encoding="utf-8")
    return data


@dataclass
class PolicyRules:
    safe_mode: bool
    allow_repo_write: bool
    allowed_write_paths: list[str]


@dataclass
class Policies:
    rules: PolicyRules


def load_policies(root: Path) -> Policies:
    """
    Load policies from .noxis/policies.yml
    """

    path = root / ".noxis" / "policies.yml"

    if not path.exists():
        raise RuntimeError("policies.yml not found. Run `noxis init` first.")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    rules = data.get("rules", {})

    return Policies(
        rules=PolicyRules(
            safe_mode=bool(rules.get("safe_mode", True)),
            allow_repo_write=bool(rules.get("allow_repo_write", False)),
            allowed_write_paths=list(rules.get("allowed_write_paths", [])),
        )
    )
