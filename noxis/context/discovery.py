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

    found: dict[str, list[str]] = {k: [] for k in patterns}
    for lang, files in patterns.items():
        for f in files:
            p = root / f
            if p.exists():
                found[lang].append(str(p.relative_to(root)))

    languages = [k for k, v in found.items() if k in ("python", "php", "lua", "node") and v]
    # repo_type MVP: mono se tiver múltiplos "roots" tipicos
    repo_type = "mono" if (root / "packages").exists() or (root / "apps").exists() else "single"

    # reduz signals só para entradas relevantes
    signals = {k: v for k, v in found.items() if v}

    return ProjectModel(
        root_path=str(root),
        repo_type=repo_type,
        languages_detected=languages,
        signals=signals
    )
