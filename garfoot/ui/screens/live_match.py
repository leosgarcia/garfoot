"""Tela de simulação ao vivo da rodada com 2 séries por tela (estilo Elifoot II)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from garfoot.domain.enums import MatchStatus
from garfoot.domain.game_state import GameState
from garfoot.domain.league import MatchFixture
from garfoot.domain.season import LeagueTier
from garfoot.engine.events import GoalEvent, MatchEvent
from garfoot.engine.match_engine import MatchResult, simulate_match
from garfoot.engine.match_progression import apply_post_match_progression
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.audio import SoundEvent, map_engine_event_to_sound_event, play_ui_sound
from garfoot.ui.widgets.dos import DosPanel


@dataclass
class LiveMatchData:
    """Estrutura com os dados pré-simulados para renderização minuto a minuto."""

    fixture: MatchFixture
    result: MatchResult
    attendance: int
    tier: LeagueTier
    goals: list[GoalEvent]
    events: list[MatchEvent]


class LiveMatchScreen(Screen[None]):
    """Tela de simulação ao vivo com 2 divisões por tela (A/B e C/D)."""

    BINDINGS = [
        ("tab", "toggle_screen_view", "Alternar Divisões"),
        ("1", "show_screen_ab", "Séries A e B"),
        ("2", "show_screen_cd", "Séries C e D"),
        ("space", "finish_fast", "Acelerar / Concluir"),
        ("enter", "finish_and_advance", "Avançar"),
        ("escape", "finish_and_advance", "Sair"),
    ]

    def __init__(self, current_round: int, user_series: str, callback_on_finish: Any = None) -> None:
        super().__init__()
        self.current_round = current_round
        self.user_series = user_series
        self.callback_on_finish = callback_on_finish
        # 0 = Tela 1 (Séries A e B); 1 = Tela 2 (Séries C e D)
        self.view_mode: int = 1 if user_series in ("C", "D") else 0
        self.current_minute: int = 0
        self.is_finished: bool = False
        self.matches_data: dict[LeagueTier, list[LiveMatchData]] = {}

    def compose(self) -> ComposeResult:
        yield Static(f"SIMULAÇÃO DA RODADA {self.current_round} - PARCIAL AO VIVO", id="title")
        yield Static(f"TEMPO DE JOGO: 0' / 90'", id="live-timer-header")

        with Horizontal(id="live-grid"):
            with Vertical(id="live-left-column"):
                yield DosPanel("SÉRIE", "Carregando...", id="live-panel-left")
            with Vertical(id="live-right-column"):
                yield DosPanel("SÉRIE", "Carregando...", id="live-panel-right")

        yield DosPanel(
            "COMANDOS",
            "[TAB / 1 / 2] Alternar Divisões   [ESPAÇO] Acelerar   [ENTER] Ir para Classificação   [ESC] Sair",
            id="commands-panel",
        )

    def on_mount(self) -> None:
        self._prepare_round_simulation()
        self._refresh_screen_view()

        state = self._get_state()
        speed = state.settings.match_speed if state else None

        from garfoot.domain.game_settings import MatchSpeed

        if speed == MatchSpeed.INSTANT:
            self.action_finish_fast()
        else:
            delay = speed.delay_seconds if speed else 0.12
            self.set_interval(delay, self._tick_simulation)

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def _prepare_round_simulation(self) -> None:
        state = self._get_state()
        if not state:
            return

        orchestrator = state.season_orchestrator
        self.matches_data = {
            LeagueTier.SERIE_A: [],
            LeagueTier.SERIE_B: [],
            LeagueTier.SERIE_C: [],
            LeagueTier.SERIE_D: [],
        }

        for tier, champ in orchestrator.championships.items():
            fixtures = [f for f in champ.fixtures if f.round_number == self.current_round and f.status == MatchStatus.SCHEDULED]
            for fix in fixtures:
                home_team = next((t for t in champ.teams if t.name == fix.home_team), None)
                away_team = next((t for t in champ.teams if t.name == fix.away_team), None)

                if home_team and away_team:
                    from garfoot.domain.stable_random import combine_seed
                    match_seed = combine_seed(self.current_round, fix.home_team, fix.away_team, namespace="match-simulation")
                    result = simulate_match(home_team, away_team, seed=match_seed)
                    fix.record_result(result.home_score, result.away_score)
                    apply_post_match_progression(home_team, away_team, result)

                    # Registra estatísticas puras de artilheiros e treinadores
                    from garfoot.domain.statistics import record_match_result_statistics
                    record_match_result_statistics(
                        mgr=state.statistics,
                        result=result,
                        competition_name=tier.value,
                        home_team=home_team,
                        away_team=away_team,
                    )

                    attendance = home_team.estimate_home_income() // (home_team.stadium.average_ticket_price if home_team.stadium else 40)
                    goals = [e for e in result.events if isinstance(e, GoalEvent)]

                    self.matches_data[tier].append(
                        LiveMatchData(
                            fixture=fix,
                            result=result,
                            attendance=max(5000, min(80000, attendance)),
                            tier=tier,
                            goals=goals,
                            events=list(result.events),
                        )
                    )

        state.current_round += 1
        manager = SaveManager()
        manager.save_game(state)

    def _tick_simulation(self) -> None:
        if self.is_finished:
            return

        state = self._get_state()
        sound_enabled = state.settings.sound_enabled if state else True
        sound_mode = state.settings.sound_mode if state else SoundMode.BEEP

        if self.current_minute < 90:
            self.current_minute += 2   # avança de 2 em 2 minutos para fluidez
            self.query_one("#live-timer-header", Static).update(
                f"TEMPO DE JOGO: {self.current_minute}' / 90'"
            )
            self._render_current_matches()

            # Dispara sons da UI para eventos ocorridos no tick atual
            if self.current_minute == 2:
                play_ui_sound(SoundEvent.MATCH_START, sound_enabled, sound_mode, app=self.app)
            elif self.current_minute == 46:
                play_ui_sound(SoundEvent.HALF_TIME, sound_enabled, sound_mode, app=self.app)

            # Verifica eventos de partidas nas ligas
            for match_list in self.matches_data.values():
                for m in match_list:
                    for ev in m.events:
                        if ev.minute in (self.current_minute - 1, self.current_minute):
                            sound_ev = map_engine_event_to_sound_event(ev)
                            if sound_ev:
                                play_ui_sound(sound_ev, sound_enabled, sound_mode, app=self.app)
        else:
            self.current_minute = 90
            self.is_finished = True
            self.query_one("#live-timer-header", Static).update(
                "RODADA FINALIZADA! Pressione [ENTER] para ver a Classificação."
            )
            self._render_current_matches()
            play_ui_sound(SoundEvent.FULL_TIME, sound_enabled, sound_mode, app=self.app)

    def action_toggle_screen_view(self) -> None:
        self.view_mode = 1 - self.view_mode
        self._refresh_screen_view()

    def action_show_screen_ab(self) -> None:
        self.view_mode = 0
        self._refresh_screen_view()

    def action_show_screen_cd(self) -> None:
        self.view_mode = 1
        self._refresh_screen_view()

    def action_finish_fast(self) -> None:
        self.current_minute = 90
        self._tick_simulation()

    def action_finish_and_advance(self) -> None:
        if not self.is_finished:
            self.action_finish_fast()
            return
        self.app.pop_screen()
        if self.callback_on_finish:
            self.callback_on_finish()

    def _refresh_screen_view(self) -> None:
        if self.view_mode == 0:
            left_tier, right_tier = LeagueTier.SERIE_A, LeagueTier.SERIE_B
            left_name, right_name = "SÉRIE A", "SÉRIE B"
        else:
            left_tier, right_tier = LeagueTier.SERIE_C, LeagueTier.SERIE_D
            left_name, right_name = "SÉRIE C", "SÉRIE D"

        self.query_one("#live-panel-left", DosPanel).border_title = f" {left_name} ({self.current_round}ª JORNADA) "
        self.query_one("#live-panel-right", DosPanel).border_title = f" {right_name} ({self.current_round}ª JORNADA) "
        self._render_current_matches()

    def _render_current_matches(self) -> None:
        state = self._get_state()
        user_team_name = state.player_team_name if state else ""

        if self.view_mode == 0:
            left_tier, right_tier = LeagueTier.SERIE_A, LeagueTier.SERIE_B
        else:
            left_tier, right_tier = LeagueTier.SERIE_C, LeagueTier.SERIE_D

        # Renderiza Coluna Esquerda
        left_lines = self._format_division_matches(self.matches_data.get(left_tier, []), user_team_name)
        self.query_one("#live-panel-left", DosPanel).update("\n".join(left_lines))

        # Renderiza Coluna Direita
        right_lines = self._format_division_matches(self.matches_data.get(right_tier, []), user_team_name)
        self.query_one("#live-panel-right", DosPanel).update("\n".join(right_lines))

    def _format_division_matches(self, matches: list[LiveMatchData], user_team_name: str) -> list[str]:
        lines: list[str] = []
        for m in matches:
            is_user = (m.fixture.home_team == user_team_name or m.fixture.away_team == user_team_name)

            # Filtra gols que já aconteceram até o minuto atual
            current_goals = [g for g in m.goals if g.minute <= self.current_minute]
            home_goals = sum(1 for g in current_goals if g.team_name == m.fixture.home_team)
            away_goals = sum(1 for g in current_goals if g.team_name == m.fixture.away_team)

            # Último evento (Gol ou Substituição) para narração no estilo Elifoot II
            last_event_str = ""
            current_events = [e for e in m.events if e.minute <= self.current_minute]
            if current_events:
                last_ev = current_events[-1]
                from garfoot.engine.events import SubstitutionEvent
                if isinstance(last_ev, GoalEvent):
                    short_name = last_ev.player_name.split()[-1] if last_ev.player_name else "Gol"
                    last_event_str = f"[bold yellow]GOL {short_name} {last_ev.minute}'[/bold yellow]"
                elif isinstance(last_ev, SubstitutionEvent):
                    short_in = last_ev.player_in_name.split()[-1]
                    last_event_str = f"[cyan]SUB {short_in} {last_ev.minute}'[/cyan]"

            home_abbr = m.fixture.home_team[:15]
            away_abbr = m.fixture.away_team[:15]

            # Cores para diferenciar Mandante, Visitante e Time Humano
            if m.fixture.home_team == user_team_name:
                home_styled = f"[bold green]{home_abbr:<15}[/bold green]"
                away_styled = f"[white]{away_abbr:<15}[/white]"
                prefix = "[bold green]>[/bold green]"
            elif m.fixture.away_team == user_team_name:
                home_styled = f"[white]{home_abbr:<15}[/white]"
                away_styled = f"[bold green]{away_abbr:<15}[/bold green]"
                prefix = "[bold green]>[/bold green]"
            else:
                home_styled = f"[cyan]{home_abbr:<15}[/cyan]"
                away_styled = f"[yellow]{away_abbr:<15}[/yellow]"
                prefix = " "

            # Placar com destaque em negrito
            placar_str = f"{home_styled} [bold white]{home_goals:>2} x {away_goals:<2}[/bold white] {away_styled}"
            ev_str = f"{last_event_str:<22}" if last_event_str else " " * 12
            line = f"{prefix} {placar_str} | {ev_str} | [dim]{m.attendance:>6,}[/dim]"
            lines.append(line)

        return lines
