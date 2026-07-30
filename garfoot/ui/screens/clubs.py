"""Telas de listagem e detalhes de clubes."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.ui.data import load_clubs
from garfoot.ui.widgets.dos import DosPanel


class ClubsScreen(Screen[None]):
    """Lista os clubes do dataset por série."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("a", "set_series('A')", "Série A"),
        ("b", "set_series('B')", "Série B"),
        ("c", "set_series('C')", "Série C"),
        ("d", "set_series('D')", "Série D"),
        ("enter", "open_selected", "Detalhes"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.clubs = load_clubs()
        self.series = "A"

    def compose(self) -> ComposeResult:
        yield Static("CLUBES", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="club-list")
            with Vertical(id="club-side"):
                yield DosPanel("FILTRO", "A Série A\nB Série B\nC Série C\nD Série D\nENTER Detalhes", id="filter-panel")
                yield DosPanel("DETALHE", "Selecione um clube.", id="club-detail")

    def on_mount(self) -> None:
        self._refresh_list()

    def action_set_series(self, series: str) -> None:
        self.series = series
        self._refresh_list()

    def action_open_selected(self) -> None:
        selected = self.query_one("#club-list", ListView).index
        visible = self._visible_clubs()
        if selected is not None and 0 <= selected < len(visible):
            self._show_detail(visible[selected])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        visible = self._visible_clubs()
        index = event.list_view.index
        if index is not None and 0 <= index < len(visible):
            self._show_detail(visible[index])

    def action_back(self) -> None:
        self.app.pop_screen()

    def _visible_clubs(self) -> list[dict[str, object]]:
        return [club for club in self.clubs if club.get("series") == self.series]

    def _refresh_list(self) -> None:
        list_view = self.query_one("#club-list", ListView)
        list_view.clear()
        list_view.border_title = f" SÉRIE {self.series} "
        for club in self._visible_clubs():
            label = f"{club.get('abbreviation', '---'):<4} {club['name']}"
            list_view.append(ListItem(Static(label)))
        self.query_one("#club-detail", DosPanel).update("Selecione um clube.")

    def _show_detail(self, club: dict[str, object]) -> None:
        stadium = club.get("stadium") or {}
        players = club.get("players") or []
        coach = club.get("coach") or "A confirmar"
        notes = club.get("review_notes") or []

        if players:
            squad_info = f"[Elenco Real - {len(players)} jogadores]"
        else:
            squad_info = "[Elenco Gerado (Ranking CBF) - 16 jogadores]"

        text = (
            f"{club['name']}\n"
            f"{club['city']} - {club['state']}\n"
            f"Série: {club['series']}\n"
            f"Sigla: {club.get('abbreviation')} ({club.get('abbreviation_status')})\n"
            f"Cores: {', '.join(club.get('colors', []))}\n"
            f"Técnico: {coach}\n\n"
            f"Estádio: {stadium.get('name', 'A confirmar')}\n"
            f"Cidade: {stadium.get('city', 'A confirmar')}\n"
            f"Capacidade: {stadium.get('capacity', 0)}\n\n"
            f"Fonte do Elenco:\n{squad_info}"
        )
        if notes:
            text += "\n\nREVISÃO:\n" + "\n".join(f"- {note}" for note in notes[:4])
        self.query_one("#club-detail", DosPanel).update(text)
