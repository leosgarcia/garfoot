"""Tela de criação de Novo Jogo na TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Input, ListItem, ListView, Static

from garfoot.domain.cup import KnockoutCup
from garfoot.domain.game_state import GameState
from garfoot.domain.league import Championship
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.data import load_clubs, load_teams
from garfoot.ui.widgets.dos import DosPanel


class NewGameScreen(Screen[None]):
    """Tela para escolher o clube e iniciar um novo jogo (obrigatoriamente na Série D)."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("enter", "confirm", "Iniciar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.raw_clubs = load_clubs()
        self.teams = load_teams()
        self.series = "D"

    def compose(self) -> ComposeResult:
        yield Static("NOVO JOGO - ESCOLHA SEU CLUBE (SÉRIE D)", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="club-list")
            with Vertical(id="club-side"):
                yield DosPanel(
                    "NOME DO SAVE",
                    "",
                    id="save-name-panel",
                )
                yield Input(placeholder="Digite o nome do save (ex: Meu Save)", id="save-name-input")
                yield DosPanel("DETALHES DO CLUBE", "Selecione um clube.", id="club-detail")
        yield DosPanel("COMANDOS", "Regra Garfoot: Início obrigatório na Série D   ENTER Confirmar   ESC Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_list()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Disparado quando o usuário aperta ENTER em um item da lista."""
        self.action_confirm()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        """Disparado conforme o usuário navega com as setas pela lista."""
        if event.item is not None:
            visible = self._visible_clubs()
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(visible):
                self._show_detail(visible[idx])

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Disparado quando o usuário aperta ENTER no campo Nome do Save."""
        self.action_confirm()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_confirm(self) -> None:
        selected_idx = self.query_one("#club-list", ListView).index
        visible_clubs = self._visible_clubs()
        if selected_idx is None or selected_idx < 0 or selected_idx >= len(visible_clubs):
            return

        chosen_club = visible_clubs[selected_idx]
        save_name_input = self.query_one("#save-name-input", Input).value.strip()
        save_name = save_name_input if save_name_input else f"Carreira {chosen_club['name']}"

        # Monta a temporada inicial
        orchestrator = self._create_initial_orchestrator()

        game_state = GameState(
            save_name=save_name,
            player_team_name=chosen_club["name"],
            current_season=2026,
            current_round=1,
            season_orchestrator=orchestrator,
        )

        # Salva o jogo inicial
        manager = SaveManager()
        manager.save_game(game_state)

        # Registra o estado no app e abre o hub da temporada
        setattr(self.app, "current_game_state", game_state)
        self.app.notify(f"Novo jogo criado: {chosen_club['name']}!", title="Sucesso")
        self.app.switch_screen("season_hub")

    def _visible_clubs(self) -> list[dict[str, object]]:
        return [club for club in self.raw_clubs if club.get("series") == self.series]

    def _refresh_list(self) -> None:
        list_view = self.query_one("#club-list", ListView)
        list_view.clear()
        list_view.border_title = " SÉRIE D (DIVISÃO INICIAL) "
        visible = self._visible_clubs()
        for club in visible:
            label = f"{club.get('abbreviation', '---'):<4} {club['name']}"
            list_view.append(ListItem(Static(label)))
        if visible:
            self._show_detail(visible[0])

    def _show_detail(self, club: dict[str, object]) -> None:
        stadium = club.get("stadium") or {}
        players = club.get("players") or []
        coach = club.get("coach") or "A confirmar"

        text = (
            f"{club['name']}\n"
            f"{club['city']} - {club['state']}\n"
            f"Série: {club['series']}\n"
            f"Sigla: {club.get('abbreviation')} ({club.get('abbreviation_status')})\n"
            f"Cores: {', '.join(club.get('colors', []))}\n"
            f"Técnico: {coach}\n\n"
            f"Estádio: {stadium.get('name', 'A confirmar')}\n"
            f"Cidade: {stadium.get('city', 'A confirmar')}\n"
            f"Capacidade: {stadium.get('capacity', 0):,}\n\n"
            f"Elenco: {len(players)} jogadores cadastrados"
        )
        self.query_one("#club-detail", DosPanel).update(text)

    def _create_initial_orchestrator(self) -> SeasonOrchestrator:
        teams_a = [t for t in self.teams if any(c["name"] == t.name and c["series"] == "A" for c in self.raw_clubs)]
        teams_b = [t for t in self.teams if any(c["name"] == t.name and c["series"] == "B" for c in self.raw_clubs)]
        teams_c = [t for t in self.teams if any(c["name"] == t.name and c["series"] == "C" for c in self.raw_clubs)]
        teams_d = [t for t in self.teams if any(c["name"] == t.name and c["series"] == "D" for c in self.raw_clubs)]

        champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams_a)
        champ_b = Championship(name="Série B 2026", season_year=2026, teams=teams_b)
        champ_c = Championship(name="Série C 2026", season_year=2026, teams=teams_c)
        champ_d = Championship(name="Série D 2026", season_year=2026, teams=teams_d)

        copa = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=self.teams)
        cbf_ranking = {t.name: idx for idx, t in enumerate(self.teams, start=1)}

        orchestrator = SeasonOrchestrator(
            season_year=2026,
            championships={
                LeagueTier.SERIE_A: champ_a,
                LeagueTier.SERIE_B: champ_b,
                LeagueTier.SERIE_C: champ_c,
                LeagueTier.SERIE_D: champ_d,
            },
            copa_do_brasil=copa,
        )

        orchestrator.start_new_season(cbf_ranking=cbf_ranking, seed=42)
        return orchestrator
