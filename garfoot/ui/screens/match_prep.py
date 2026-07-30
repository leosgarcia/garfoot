"""Tela de gestão do clube e preparação tática estilo Elifoot II / DOS."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.season import LeagueTier
from garfoot.domain.team import Formation, Team
from garfoot.ui.widgets.dos import DosPanel

# Mapeamento de Esquemas Táticos com atalhos F1 a F6
TACTICS_MAP: list[tuple[str, tuple[int, int, int]]] = [
    ("F1", (3, 4, 3)),
    ("F2", (4, 3, 3)),
    ("F3", (4, 4, 2)),
    ("F4", (4, 5, 1)),
    ("F5", (5, 3, 2)),
    ("F6", (3, 5, 2)),
]

# Sigla de 1 letra idêntica ao Elifoot II: G, D, M, A
POS_LETTER_MAP = {
    PlayerPosition.GOALKEEPER: "G",
    PlayerPosition.DEFENDER: "D",
    PlayerPosition.MIDFIELDER: "M",
    PlayerPosition.FORWARD: "A",
}


class MatchPrepScreen(Screen[None]):
    """Tela de gestão do clube, finanças e preparação tática idêntica ao Elifoot II."""

    BINDINGS = [
        ("escape", "back", "Voltar ao Hub"),
        ("f1", "set_tactics(0)", "F1 3-4-3"),
        ("f2", "set_tactics(1)", "F2 4-3-3"),
        ("f3", "set_tactics(2)", "F3 4-4-2"),
        ("f4", "set_tactics(3)", "F4 4-5-1"),
        ("f5", "set_tactics(4)", "F5 5-3-2"),
        ("f6", "set_tactics(5)", "F6 3-5-2"),
        ("1", "set_tactics(0)", "1 3-4-3"),
        ("2", "set_tactics(1)", "2 4-3-3"),
        ("3", "set_tactics(2)", "3 4-4-2"),
        ("4", "set_tactics(3)", "4 4-5-1"),
        ("5", "set_tactics(4)", "5 5-3-2"),
        ("6", "set_tactics(5)", "6 3-5-2"),
        ("a", "auto_select", "Escalar Melhores"),
        ("j", "start_match", "Jogar Rodada"),
        ("enter", "start_match", "Jogar Rodada"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.formation_idx: int = 2  # Padrão 4-4-2 (F3)
        self.selected_starters: set[str] = set()

    def compose(self) -> ComposeResult:
        yield Static("GARFOOT 2026 - GESTÃO DO CLUBE E TÁTICA", id="title")
        with Horizontal(id="match-grid"):
            # Coluna Esquerda: Elenco com letras G, D, M, A e Atributos/Valores
            yield ListView(id="squad-list")

            # Coluna Direita: Informações do Clube e Táticas Estilo Elifoot II
            with Vertical(id="club-side"):
                yield DosPanel("CLUBE", "Carregando...", id="club-info-panel")
                yield DosPanel("TÁTICAS", "Carregando...", id="tactics-list-panel")

        # Painéis Inferiores: Confronto da Rodada e Finanças
        with Horizontal(id="prep-bottom-grid"):
            yield DosPanel("CONFRONTO DA RODADA", "Carregando...", id="fixture-info-panel")
            yield DosPanel("FINANÇAS DO CLUBE", "Carregando...", id="finance-info-panel")

        yield DosPanel(
            "COMANDOS",
            "[ESPAÇO] Alternar Titular   [F1-F6 / 1-6] Esquema Tático   [A] Auto Escalar   [ENTER / J] Jogar Rodada   [ESC] Voltar",
            id="commands-panel",
        )

    def on_mount(self) -> None:
        team = self._get_user_team()
        if team:
            if team.starting_player_names:
                self.selected_starters = set(team.starting_player_names)
            else:
                self._auto_select_starters(team)

            current_fmt = (team.formation.defenders, team.formation.midfielders, team.formation.forwards)
            for idx, (_, fmt) in enumerate(TACTICS_MAP):
                if fmt == current_fmt:
                    self.formation_idx = idx
                    break

        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def _get_user_team(self) -> Team | None:
        state = self._get_state()
        if not state:
            return None
        serie_d = state.season_orchestrator.championships.get(LeagueTier.SERIE_D)
        if not serie_d:
            return None
        return next((t for t in serie_d.teams if t.name == state.player_team_name), None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_set_tactics(self, idx: int) -> None:
        if 0 <= idx < len(TACTICS_MAP):
            self.formation_idx = idx
            team = self._get_user_team()
            if team:
                d, m, f = TACTICS_MAP[idx][1]
                team.formation = Formation(defenders=d, midfielders=m, forwards=f)
            self._refresh_ui()

    def action_auto_select(self) -> None:
        team = self._get_user_team()
        if team:
            self._auto_select_starters(team)
            self._refresh_ui()
            self.app.notify("Titulares escalados automaticamente!", title="Tática")

    def _auto_select_starters(self, team: Team) -> None:
        available_players = [p for p in team.players if p.is_available]
        sorted_players = sorted(available_players, key=lambda p: p.overall, reverse=True)
        self.selected_starters = {p.name for p in sorted_players[:11]}
        team.starting_player_names = [p.name for p in sorted_players[:11]]

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        team = self._get_user_team()
        if not team:
            return

        idx = event.list_view.index
        ordered_players = sorted(team.players, key=lambda x: (x.position.value, x.name not in self.selected_starters, -x.overall))
        if idx is not None and 0 <= idx < len(ordered_players):
            player = ordered_players[idx]

            if player.is_injured:
                rem_rounds = player.injury.rounds_remaining if player.injury else 1
                self.app.notify(
                    f"{player.name} está lesionado ({player.injury.description if player.injury else 'Lesão'})! Indisponível por {rem_rounds} rodada(s).",
                    severity="error",
                    title="Jogador Indisponível",
                )
                return

            if player.name in self.selected_starters:
                self.selected_starters.remove(player.name)
            else:
                if len(self.selected_starters) >= 11:
                    self.app.notify("Você já selecionou 11 titulares! Remova um para incluir outro.", severity="warning")
                    return
                self.selected_starters.add(player.name)

            team.starting_player_names = list(self.selected_starters)
            self._refresh_ui()

    def action_start_match(self) -> None:
        team = self._get_user_team()
        if team:
            d, m, f = TACTICS_MAP[self.formation_idx][1]
            team.formation = Formation(defenders=d, midfielders=m, forwards=f)
            team.starting_player_names = list(self.selected_starters)

        self.dismiss(True)

    def _refresh_ui(self) -> None:
        state = self._get_state()
        team = self._get_user_team()
        if not state or not team:
            return

        serie_d = state.season_orchestrator.championships.get(LeagueTier.SERIE_D)
        standings = serie_d.standings() if serie_d else []

        # Encontra posição do clube do jogador e pontos na tabela
        user_pos = 1
        user_pts = 0
        for i, st in enumerate(standings, start=1):
            if st.team_name == team.name:
                user_pos = i
                user_pts = st.points
                break

        # 1. Painel CLUBE (Topo Direito)
        stadium_cap = user_team_stadium_cap = team.stadium.capacity if team.stadium else 20000
        club_info_text = (
            f"{team.name.upper():<25} SÉRIE D\n"
            f"Técnico: Humano\n"
            f"{user_pos}º lugar    {user_pts} pontos\n"
            f"Estádio: {stadium_cap:,} lugares"
        )
        self.query_one("#club-info-panel", DosPanel).update(club_info_text)

        # 2. Painel TÁTICAS (Opções F1 a F6 com destaque para a selecionada)
        tactics_lines = ["SISTEMAS TÁTICOS (F1-F6):", ""]
        for idx, (key, fmt) in enumerate(TACTICS_MAP):
            prefix = ">" if idx == self.formation_idx else " "
            label = f"{key} {fmt[0]}-{fmt[1]}-{fmt[2]}"
            tactics_lines.append(f"{prefix} {label}")
        tactics_lines.append("")
        tactics_lines.append(f"Titulares: {len(self.selected_starters)}/11 | OVR: {team.squad_strength}")
        self.query_one("#tactics-list-panel", DosPanel).update("\n".join(tactics_lines))

        # 3. Lista de Elenco Estilo Elifoot II (Coluna Esquerda)
        list_view = self.query_one("#squad-list", ListView)
        list_view.clear()
        list_view.border_title = f" ELENCO DO {team.name.upper()} ({len(self.selected_starters)}/11) "

        # Ordena rigorosamente por Posição solicitada: Goleiro (0), Defesa (1), Meio Campo (2), Atacante (3)
        pos_order = {
            PlayerPosition.GOALKEEPER: 0,
            PlayerPosition.DEFENDER: 1,
            PlayerPosition.MIDFIELDER: 2,
            PlayerPosition.FORWARD: 3,
        }
        ordered_players = sorted(
            team.players,
            key=lambda x: (pos_order.get(x.position, 9), x.name not in self.selected_starters, -x.overall)
        )
        
        pos_names = {
            PlayerPosition.GOALKEEPER: "--- GOLEIROS ---",
            PlayerPosition.DEFENDER: "--- DEFESAS ---",
            PlayerPosition.MIDFIELDER: "--- MEIO-CAMPO ---",
            PlayerPosition.FORWARD: "--- ATACANTES ---",
        }

        current_pos = None

        for p in ordered_players:
            if p.position != current_pos:
                current_pos = p.position
                header_text = pos_names.get(current_pos, "--- JOGADORES ---")
                header_item = ListItem(Static(f"[bold cyan]{header_text}[/bold cyan]"))
                header_item.disabled = True
                list_view.append(header_item)

            pos_letter = POS_LETTER_MAP.get(p.position, "J")
            if p.is_injured and p.injury:
                tag = f"LES {p.injury.rounds_remaining}R"
            elif p.name in self.selected_starters:
                tag = "[T]   "
            else:
                tag = "      "

            val = f"${p.value:,}" if p.value else "$500,000"
            line = f"{pos_letter} {p.name:<22} OVR:{p.overall:>2} FIT:{p.fitness:>2} {val:>10} {tag}"
            list_view.append(ListItem(Static(line)))

        # 4. Painel CONFRONTO DA RODADA (Inferior Esquerdo)
        next_fixture = None
        if serie_d and state.current_round <= 38:
            next_fixture = next(
                (f for f in serie_d.fixtures if f.round_number == state.current_round and (f.home_team == team.name or f.away_team == team.name)),
                None,
            )

        if next_fixture:
            is_home = next_fixture.home_team == team.name
            mando_str = "CASA" if is_home else "FORA"
            adv_name = next_fixture.away_team if is_home else next_fixture.home_team

            adv_pos = 1
            adv_pts = 0
            for i, st in enumerate(standings, start=1):
                if st.team_name == adv_name:
                    adv_pos = i
                    adv_pts = st.points
                    break

            fixture_text = (
                f"{adv_name.upper():<25} ({mando_str})\n"
                f"{adv_pos}º lugar    {adv_pts} pontos\n"
                f"{state.current_round}ª JORNADA"
            )
        else:
            fixture_text = "Nenhuma partida agendada."

        self.query_one("#fixture-info-panel", DosPanel).update(fixture_text)

        # 5. Painel FINANÇAS DO CLUBE (Inferior Direito)
        wage_bill = sum(p.salary for p in team.players) if team.players else 20000
        income_est = team.estimate_home_income()
        finance_text = (
            f"Caixa/Dinheiro:   ${team.budget:,}\n"
            f"Folha Salarial:   ${wage_bill:,}\n"
            f"Renda Estimada:   ${income_est:,}"
        )
        self.query_one("#finance-info-panel", DosPanel).update(finance_text)
