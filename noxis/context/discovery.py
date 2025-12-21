from __future__ import annotations

from pathlib import Path

from noxis.context.model import ProjectModel


def discover_project(root: Path) -> ProjectModel:
    # Heurística MVP: sinais por aarquivos conhecidos
    patterns = {
        "python": ["pyproject.toml", "requirements.txt", "setup.py", "Pipfile"],
        "php": ["composer.json"],
        "lua": [".luacheckrc", "rockspec", "rocks.toml"],
        "node": ["package.json"],
        "docker": ["Dockerfile", "docker-compose.yml", "compose.yml"],
    }

    found: dict[str, list[str]] = {}
    for group, files in patterns.items():
        hits: list[str] = []
        for f in files:
            p = root / f
            if p.exists():
                hits.append(str(p.relative_to(root)))
        if hits:
            found[group] = hits
    languages = []
    for k in ("python", "php", "lua", "node"):
        if k in found:
            languages.append(k)

    repo_type = "mono" if (root / "packages").exists() or (root / "apps").exists() else "single"

    return ProjectModel(
        root_path=str(root), repo_type=repo_type, languages_detected=languages, signals=found
    )
