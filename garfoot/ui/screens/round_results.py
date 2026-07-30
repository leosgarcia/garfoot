"""Tela de exibição dos resultados da rodada e narração detalhada da partida."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.league import MatchFixture
from garfoot.engine.commentary import narrate_summary
from garfoot.engine.match_engine import MatchResult
from garfoot.ui.widgets.dos import DosPanel


class RoundResultsScreen(Screen[None]):
    """Exibe os placares de todas as partidas da rodada e detalhes do jogo."""

    BINDINGS = [
        ("escape", "confirm", "Continuar"),
        ("enter", "confirm", "Continuar"),
    ]

    def __init__(
        self,
        round_number: int,
        fixtures: list[MatchFixture],
        user_team_name: str,
        match_results: list[tuple[MatchFixture, MatchResult]],
    ) -> None:
        super().__init__()
        self.round_number = round_number
        self.fixtures = fixtures
        self.user_team_name = user_team_name
        self.match_results = match_results

    def compose(self) -> ComposeResult:
        yield Static(f"RESULTADOS DA RODADA {self.round_number}", id="title")
        with Horizontal(id="match-grid"):
            yield ListView(id="fixtures-list")
            with Vertical(id="club-side"):
                yield DosPanel("DETALHES DA PARTIDA", "Selecione um jogo na lista.", id="fixture-detail-panel")
        yield DosPanel("COMANDOS", "Seta Cima/Baixo Navegar   ENTER / ESC Continuar para o Hub", id="commands-panel")

    def on_mount(self) -> None:
        list_view = self.query_one("#fixtures-list", ListView)
        list_view.clear()
        list_view.border_title = f" RODADA {self.round_number} - SÉRIE D "

        user_idx = 0
        for idx, (fix, result) in enumerate(self.match_results):
            prefix = ">" if (fix.home_team == self.user_team_name or fix.away_team == self.user_team_name) else " "
            if prefix == ">":
                user_idx = idx

            placar = f"{fix.home_team:<24} {result.home_score:>2} x {result.away_score:<2} {fix.away_team}"
            line = f"{prefix} {placar}"
            list_view.append(ListItem(Static(line)))

        if self.match_results:
            self._show_match_detail(self.match_results[user_idx][0], self.match_results[user_idx][1])

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self.match_results):
            fix, result = self.match_results[idx]
            self._show_match_detail(fix, result)

    def action_confirm(self) -> None:
        self.app.pop_screen()

    def _show_match_detail(self, fixture: MatchFixture, result: MatchResult) -> None:
        # Usa a narração oficial da engine de comentários
        summary_lines = narrate_summary(result)
        summary_text = "\n".join(summary_lines[:15])

        text = (
            f"PARTIDA: {fixture.home_team} x {fixture.away_team}\n"
            f"PLACAR FINAL: {result.home_score} x {result.away_score}\n"
            f"Posse de Bola: {result.home_possession:.0%} x {result.away_possession:.0%}\n"
            f"Chutes no Alvo: {result.home_shots_on_target} x {result.away_shots_on_target}\n"
            f"Faltas / Cartões: {len(result.events)} eventos de jogo\n\n"
            f"SÚMULA DA PARTIDA:\n{summary_text}"
        )
        self.query_one("#fixture-detail-panel", DosPanel).update(text)
