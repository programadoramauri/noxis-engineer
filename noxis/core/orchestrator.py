from __future__ import annotations

from noxis.core.results import Result
from noxis.core.workspace import Workspace
from noxis.services.init_service import InitService

from noxis.services.ai_tests_service import AITestsService
from noxis.services.scan_service import ScanService
from noxis.services.doctor_service import DoctorService
from noxis.services.ai_explain_service import AIExplainService


class Orchestrator:
    def init_workspace(self, workspace: Workspace) -> list[Result]:
        return InitService().run(workspace)

    def scan(self, workspace: Workspace) -> list[Result]:
        return ScanService().run(workspace)

    def doctor(self, workspace: Workspace) -> list[Result]:
        return DoctorService().run(workspace)

    def ai_explain(self, workspace: Workspace) -> str:
        return AIExplainService().run(workspace)

    def ai_tests(self, workspace: Workspace) -> list[Result]:
        return AITestsService().run(workspace)
