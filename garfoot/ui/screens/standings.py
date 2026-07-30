"""Tela de classificação com 2 divisões simultâneas por tela (estilo Elifoot II)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from garfoot.domain.game_state import GameState
from garfoot.domain.season import LeagueTier
from garfoot.ui.widgets.dos import DosPanel


class StandingsScreen(Screen[None]):
    """Mostra a tabela de classificação dividida em 2 divisões por tela (A/B e C/D)."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("tab", "toggle_screen_view", "Alternar Divisões"),
        ("1", "show_screen_ab", "Séries A e B"),
        ("2", "show_screen_cd", "Séries C e D"),
        ("enter", "back", "Continuar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        # 0 = Tela 1 (Séries A e B); 1 = Tela 2 (Séries C e D)
        self.view_mode: int = 1

    def compose(self) -> ComposeResult:
        yield Static("CLASSIFICAÇÃO GERAL DAS SÉRIES", id="title")
        with Horizontal(id="live-grid"):
            with Vertical(id="live-left-column"):
                yield DosPanel("SÉRIE", "Carregando...", id="standings-panel-left")
            with Vertical(id="live-right-column"):
                yield DosPanel("SÉRIE", "Carregando...", id="standings-panel-right")

        yield DosPanel(
            "COMANDOS",
            "[TAB / 1 / 2] Alternar Par de Divisões (A/B ou C/D)   [ENTER / ESC] Continuar",
            id="commands-panel",
        )

    def on_mount(self) -> None:
        state = self._get_state()
        if state:
            # Se o jogador humano está na Série D ou C, abre por padrão na Tela 2 (C/D)
            user_team_name = state.player_team_name
            orchestrator = state.season_orchestrator
            in_cd = any(
                t.name == user_team_name
                for tier in (LeagueTier.SERIE_C, LeagueTier.SERIE_D)
                for t in orchestrator.championships[tier].teams
            )
            self.view_mode = 1 if in_cd else 0

        self._render_tables()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_toggle_screen_view(self) -> None:
        self.view_mode = 1 - self.view_mode
        self._render_tables()

    def action_show_screen_ab(self) -> None:
        self.view_mode = 0
        self._render_tables()

    def action_show_screen_cd(self) -> None:
        self.view_mode = 1
        self._render_tables()

    def _render_tables(self) -> None:
        state = self._get_state()
        user_team_name = state.player_team_name if state else ""

        if self.view_mode == 0:
            left_tier, right_tier = LeagueTier.SERIE_A, LeagueTier.SERIE_B
            left_name, right_name = "SÉRIE A", "SÉRIE B"
        else:
            left_tier, right_tier = LeagueTier.SERIE_C, LeagueTier.SERIE_D
            left_name, right_name = "SÉRIE C", "SÉRIE D"

        self.query_one("#standings-panel-left", DosPanel).border_title = f" {left_name} "
        self.query_one("#standings-panel-right", DosPanel).border_title = f" {right_name} "

        if state:
            orchestrator = state.season_orchestrator
            left_champ = orchestrator.championships.get(left_tier)
            right_champ = orchestrator.championships.get(right_tier)

            left_lines = self._format_championship_standings(left_champ, user_team_name) if left_champ else ["Sem dados."]
            right_lines = self._format_championship_standings(right_champ, user_team_name) if right_champ else ["Sem dados."]
        else:
            left_lines = ["Nenhum save ativo."]
            right_lines = ["Nenhum save ativo."]

        self.query_one("#standings-panel-left", DosPanel).update("\n".join(left_lines))
        self.query_one("#standings-panel-right", DosPanel).update("\n".join(right_lines))

    def _format_championship_standings(self, champ: Any, user_team_name: str) -> list[str]:
        standings = champ.standings()
        lines = ["POS CLUBE                    J  V  E  D GP:GC PTS"]

        for idx, st in enumerate(standings, start=1):
            prefix = ">" if st.team_name == user_team_name else " "
            name_abbr = st.team_name[:22]
            lines.append(
                f"{prefix}{idx:>2} {name_abbr:<22} {st.played:>2} {st.wins:>2} {st.draws:>2} {st.losses:>2} {st.goals_for:>2}:{st.goals_against:<2} {st.points:>3}"
            )

        return lines
