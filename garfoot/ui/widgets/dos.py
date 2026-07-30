"""Widgets visuais com sabor de terminal antigo."""

from __future__ import annotations

from textual.widget import Widget
from textual.widgets import Static


class DosPanel(Static):
    """Painel simples com borda e título em estilo DOS."""

    DEFAULT_CSS = """
    DosPanel {
        border: solid $accent;
        padding: 0 1;
        background: $surface;
        color: $text;
    }
    """

    def __init__(self, title: str, content: str = "", *, id: str | None = None) -> None:
        super().__init__(content, id=id)
        self.border_title = f" {title} "


class NumberedMenu(Static):
    """Menu numerado, controlado pelo teclado."""

    def __init__(self, items: list[str], *, id: str | None = None) -> None:
        self.items = items
        super().__init__(self._render_menu(), id=id)

    def _render_menu(self) -> str:
        return "\n".join(f"F{index + 1}  {item}" for index, item in enumerate(self.items))

    def set_items(self, items: list[str]) -> None:
        self.items = items
        self.update(self._render_menu())


class Spacer(Widget):
    """Espaco flexivel para composicoes densas."""
