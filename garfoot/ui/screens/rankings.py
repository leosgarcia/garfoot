"""Tela de estatísticas e rankings de artilheiros e treinadores em estilo DOS / Textual."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.game_state import GameState
from garfoot.ui.widgets.dos import DosPanel

RANKING_VIEWS = [
    ("Artilheiros Geral", "GERAL", "scorers"),
    ("Artilheiros Série A", "Série A", "scorers"),
    ("Artilheiros Série B", "Série B", "scorers"),
    ("Artilheiros Série C", "Série C", "scorers"),
    ("Artilheiros Série D", "Série D", "scorers"),
    ("Treinadores Geral", "GERAL", "coaches"),
    ("Treinadores Série A", "Série A", "coaches"),
    ("Treinadores Série B", "Série B", "coaches"),
    ("Treinadores Série C", "Série C", "coaches"),
    ("Treinadores Série D", "Série D", "coaches"),
]


class RankingsScreen(Screen[None]):
    """Tela de Rankings Estatísticos do Garfoot (Artilharia e Treinadores)."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("1", "select_view(0)", "Artilheiros Geral"),
        ("2", "select_view(1)", "Artilheiros Série A"),
        ("3", "select_view(4)", "Artilheiros Série D"),
        ("4", "select_view(5)", "Treinadores Geral"),
        ("5", "select_view(9)", "Treinadores Série D"),
        ("tab", "next_view", "Próxima Visão"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.view_index: int = 0

    def compose(self) -> ComposeResult:
        yield Static("RANKINGS E ESTATÍSTICAS DA TEMPORADA", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="rankings-list")
            with Vertical(id="club-side"):
                yield DosPanel("VISÃO SELECIONADA", "Use 1-5 ou TAB para navegar.", id="filter-panel")
                yield DosPanel("LEGENDA DAS COLUNAS", "", id="detail-panel")
        yield DosPanel("COMANDOS", "[1-5 / TAB] Mudar Visão de Ranking   [ESC] Voltar ao Hub", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_next_view(self) -> None:
        self.view_index = (self.view_index + 1) % len(RANKING_VIEWS)
        self._refresh_ui()

    def action_select_view(self, index: int) -> None:
        if 0 <= index < len(RANKING_VIEWS):
            self.view_index = index
            self._refresh_ui()

    def _refresh_ui(self) -> None:
        label, comp, rtype = RANKING_VIEWS[self.view_index]
        state = self._get_state()

        self.query_one("#filter-panel", DosPanel).update(
            f"RANKING ATIVO: {label.upper()}\nCompetição: {comp} | Tipo: {rtype.upper()}"
        )

        list_view = self.query_one("#rankings-list", ListView)
        list_view.clear()
        list_view.border_title = f" {label.upper()} "

        if not state:
            return

        stats = state.statistics

        if rtype == "scorers":
            comp_filter = None if comp == "GERAL" else comp
            top_scorers = stats.build_top_scorers_ranking(competition=comp_filter, limit=20)

            self.query_one("#detail-panel", DosPanel).update(
                "COLUNAS: POS | JOGADOR                | CLUBE            | GOLS | JOGOS | MÉDIA"
            )

            if not top_scorers:
                list_view.append(ListItem(Static("Ainda não há gols registrados nesta competição.")))
            else:
                for idx, sc in enumerate(top_scorers, start=1):
                    p_name = sc.player_name[:20]
                    c_name = sc.team_name[:16]
                    line = f"{idx:>2}º  {p_name:<20} {c_name:<16} {sc.goals:>4}G  {sc.appearances:>5}J  {sc.goals_per_game:>5.2f}"
                    list_view.append(ListItem(Static(line)))

        else:  # coaches
            comp_filter = None if comp == "GERAL" else comp
            top_coaches = stats.build_coach_ranking(competition=comp_filter, limit=20)

            self.query_one("#detail-panel", DosPanel).update(
                "COLUNAS: POS | TREINADOR              | CLUBE            | J | V | E | D |  APROV%"
            )

            if not top_coaches:
                list_view.append(ListItem(Static("Ainda não há estatísticas de treinadores suficientes.")))
            else:
                for idx, c in enumerate(top_coaches, start=1):
                    c_name = c.coach_name[:20]
                    t_name = (c.team_name or "Sem Clube")[:16]
                    line = f"{idx:>2}º  {c_name:<20} {t_name:<16} {c.matches:>2}J {c.wins:>2}V {c.draws:>2}E {c.losses:>2}D  {c.win_percentage:>5.1f}%"
                    list_view.append(ListItem(Static(line)))
