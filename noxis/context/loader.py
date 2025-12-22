from pathlib import Path

from noxis.context.discovery import discover_project
from noxis.context.model import ProjectModel


def load_project(root: Path) -> ProjectModel:
    project_file = root / ".noxis" / "project.yml"

    if project_file.exists():
        return ProjectModel.from_yaml(project_file)

    # fallback (MVP / campatibilidade)
    return discover_project(root)
