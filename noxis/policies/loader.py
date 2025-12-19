from __future__ import annotations

from importlib.resources import files

def load_default_policies_yaml() -> str:
    # lê o defaults.yml empacotado
    data = files("noxis.policies").joinpath("defaults.yml").read_text(encoding="utf-8")
    return data
