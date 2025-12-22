from __future__ import annotations

import hashlib

from noxis.ai.context_builder import build_ai_context
from noxis.ai.provider import AIProvider
from noxis.context.loader import load_project
from noxis.core.project_state import ProjectState
from noxis.core.workspace import Workspace
from noxis.storage.memory import MemoryStore


class AIExplainService:
    def run(self, workspace: Workspace) -> str:
        if not workspace.project_file.exists():
            raise RuntimeError("project.yml not found. Run `noxis scan` first.")

        project = load_project(workspace.root)
        store = MemoryStore(workspace.memory_db_file)
        store.initialize()

        recent_scans = store.get_recent_runs("scan", limit=3)
        recent_doctors = store.get_recent_runs("doctor", limit=3)

        state = ProjectState(store)
        scan_state = state.last_scan()
        doctor_state = state.last_doctor()

        prompt = build_ai_context(
            scan_state=scan_state,
            doctor_state=doctor_state,
            scan_history=recent_scans,
            doctor_history=recent_doctors,
        )

        provider = AIProvider()
        response = provider.explain(prompt)

        try:
            prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            store.record_ai_explanation(prompt_hash=prompt_hash, response=response)
        except Exception:
            pass

        return response
