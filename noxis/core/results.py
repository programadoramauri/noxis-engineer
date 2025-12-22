from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

Severity = Literal["info", "warn", "error"]


@dataclass(frozen=True)
class Result:
    type: str
    severity: Severity
    message: str
    location: str | None = None

    @staticmethod
    def info(type_: str, message: str, location: str | None = None) -> "Result":
        return Result(type=type_, severity="info", message=message, location=location)

    @staticmethod
    def warn(type_: str, message: str, location: str | None = None) -> "Result":
        return Result(type=type_, severity="warn", message=message, location=location)

    @staticmethod
    def error(type_: str, message: str, location: str | None = None) -> "Result":
        return Result(type=type_, severity="error", message=message, location=location)

    def to_rich(self):
        title = f"[{self.severity.upper()}] {self.type}"

        body = Text(self.message)
        if self.location:
            body.append(f"\n\nLocation: {self.location}", style="dim")

        style_map = {
            "info": "cyan",
            "warn": "yellow",
            "warning": "yellow",
            "error": "red",
            "success": "green",
        }

        style = style_map.get(self.severity, "white")

        return Panel(body, title=title, border_style=style, expand=False)


def print_human_results(results: list[Result], console: Console) -> None:
    table = Table(title="Noxis Results", show_lines=False)
    table.add_column("Severity", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("Message")
    table.add_column("Location")

    for r in results:
        table.add_row(r.severity, r.type, r.message, r.location or "")
    console.print(table)
