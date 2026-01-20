from __future__ import annotations
from pathlib import Path
from noxis.storage.memory import MemoryStore


class AITestsTargetHistory:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def already_tested(self) -> set[str]:
        runs = self.store.get_recent_runs("ai-tests", limit=100)
        tested: set[str] = set()

        for run in runs:
            payload = run.get("payload") or {}
            target = payload.get("target")
            if target:
                tested.add(target)

        return tested

    def mark_tested(self, target: Path) -> None:
        pass
