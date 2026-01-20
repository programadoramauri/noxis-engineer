from __future__ import annotations

from pathlib import Path
from noxis.storage.memory import MemoryStore


class AITestTargetRegistry:
    STATE_KEY = "ai_tests_targets"

    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def get_tested(self) -> set[str]:
        state = self.store.get_state(self.STATE_KEY) or {}
        return set(state.get("tested", []))

    def mark_tested(self, target: Path) -> None:
        tested = self.get_tested()
        tested.add(target.as_posix())
        self.store.set_state(self.STATE_KEY, {"tested": sorted(tested)})

    def is_tested(self, target: Path) -> bool:
        return target.as_posix() in self.get_tested()
