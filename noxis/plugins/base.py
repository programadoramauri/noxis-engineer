from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Literal

from noxis.core.results import Result
from noxis.context.model import ProjectModel

CapabilityKind = Literal["deterministic", "ai"]


@dataclass(frozen=True)
class Applicability:
    is_applicable: bool
    confidence: float
    reasons: list[str]
    scope_hints: list[str] | None = None


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    description: str
    kind: CapabilityKind = "deterministic"
    default_enabled: bool = True
    inputs: dict[str, Any] | None = None


@dataclass(frozen=True)
class ActionRequest:
    capability: str
    project: ProjectModel
    options: dict[str, Any]
    artifacts: dict[str, Any] | None = None


class Plugin(Protocol):
    id: str
    version: str
    display_name: str
    supported_language: list[str]

    def detect(self, project: ProjectModel) -> Applicability: ...
    def capabilities(self, project: ProjectModel) -> list[CapabilitySpec]: ...
    def run(self, request: ActionRequest) -> list[Result]: ...

