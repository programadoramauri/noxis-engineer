from __future__ import annotations

from noxis.plugins.base import Plugin
from noxis.plugins.python.plugin import PythonPlugin


class PluginManager:
    """
    MVP: registro estático.
    Evolução natural: entrypoints / discovery dinâmica.
    """

    def load_all(self) -> list[Plugin]:
        return [PythonPlugin()]
