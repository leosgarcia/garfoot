"""Tela de partida demonstrativa com narração."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Static

from garfoot.engine.commentary import narrate_match, narrate_summary
from garfoot.engine.match_engine import simulate_match
from garfoot.ui.data import load_teams
from garfoot.ui.demo import make_demo_team
from garfoot.ui.widgets.dos import DosPanel


class MatchScreen(Screen[None]):
    """Simula uma partida demo e mostra a narração."""

    BINDINGS = [("escape", "back", "Voltar"), ("r", "rerun", "Repetir")]

    def __init__(self) -> None:
        super().__init__()
        self.seed = 7

    def compose(self) -> ComposeResult:
        yield Static("PARTIDA AO VIVO", id="title")
        with Horizontal(id="match-grid"):
            yield DosPanel("NARRAÇÃO", "", id="commentary-panel")
            yield DosPanel("PLACAR", "", id="score-panel")
        yield DosPanel("COMANDOS", "R Nova simulação   ESC Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._simulate()

    def action_rerun(self) -> None:
        self.seed += 1
        self._simulate()

    def action_back(self) -> None:
        self.app.pop_screen()

    def _simulate(self) -> None:
        teams = load_teams()
        # Escolhe dois clubes reais do dataset (ex: Ath. Paranaense e Coritiba, ou os 2 primeiros)
        home = teams[0] if teams else make_demo_team("GARFOOT", 72)
        away = teams[20] if len(teams) > 20 else (teams[1] if len(teams) > 1 else make_demo_team("RIVAL", 65))

        result = simulate_match(home, away, seed=self.seed)
        lines = narrate_match(result, seed=self.seed)
        self.query_one("#commentary-panel", DosPanel).update("\n".join(lines[-22:]))
        self.query_one("#score-panel", DosPanel).update(
            f"{result.home_team_name} {result.home_score}\n"
            f"{result.away_team_name} {result.away_score}\n\n"
            f"Chutes: {result.shots_home} x {result.shots_away}\n"
            f"Posse: {result.possession_home:.0%} x {result.possession_away:.0%}\n"
            f"Cartões: {result.cards_home} x {result.cards_away}\n\n"
            f"Seed: {self.seed}\n\n"
            f"{narrate_summary(result)}"
        )
