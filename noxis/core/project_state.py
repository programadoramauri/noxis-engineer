from __future__ import annotations

from noxis.storage.memory import MemoryStore

class ProjectState:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store
    def last_scan(self) -> dict | None:
        return self.store.get_state("last_scan")
    
    def last_doctor(self) -> dict | None:
        return self.store.get_state("last_doctor")
