"""Tela TUI de Gerenciamento de Contratos e Jogadores Livres (Free Agents)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.contract_lifecycle import renew_player_contract, sign_free_agent
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.widgets.dos import DosPanel


class ContractsScreen(Screen[None]):
    """Tela de contratos e mercado de agentes livres do Garfoot."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("tab", "switch_tab", "Alternar Aba"),
        ("r", "renew_contract", "Renovar (3 Anos)"),
        ("f", "sign_free_agent", "Contratar Livre"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.active_tab: str = "squad"  # "squad" | "free_agents"

    def compose(self) -> ComposeResult:
        yield Static("GESTÃO DE CONTRATOS & JOGADORES LIVRES", id="title")
        with Horizontal(id="contracts-grid"):
            yield ListView(id="players-list")
            with Vertical(id="detail-side"):
                yield DosPanel("SITUAÇÃO CONTRATUAL / ATLETA", "Carregando...", id="contract-detail-panel")
                yield DosPanel("SAÚDE SALARIAL DO ELENCO", "Carregando...", id="wage-health-panel")
        yield DosPanel("COMANDOS", "[TAB] Alternar Aba | [R] Renovar (3 Anos) | [F] Contratar Livre | [ESC] Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_switch_tab(self) -> None:
        self.active_tab = "free_agents" if self.active_tab == "squad" else "squad"
        self._refresh_ui()

    def action_renew_contract(self) -> None:
        if self.active_tab != "squad":
            self.app.notify("A renovação só se aplica a jogadores do seu elenco.", severity="warning")
            return

        state = self._get_state()
        if not state:
            return

        user_team = next(
            (c for c in state.season_orchestrator.championships[state.season_orchestrator.championships.keys().__iter__().__next__()].teams if c.name == state.player_team_name),
            None,
        )
        if not user_team:
            for champ in state.season_orchestrator.championships.values():
                t = next((team for team in champ.teams if team.name == state.player_team_name), None)
                if t:
                    user_team = t
                    break

        if not user_team or not user_team.players:
            return

        list_view = self.query_one("#players-list", ListView)
        idx = list_view.index
        if idx is None or idx < 0 or idx >= len(user_team.players):
            return

        target_player = user_team.players[idx]
        try:
            renewed = renew_player_contract(
                player=target_player,
                years=3,
                economic_context=state.economic_context,
                is_protected=True,
                protection_years=1,
            )
            # Substitui no elenco
            for i, p in enumerate(user_team.players):
                if p.name == target_player.name:
                    user_team.players[i] = renewed
                    break

            SaveManager().save_game(state)
            self.app.notify(f"Contrato de {renewed.name} renovado por 3 anos!", title="Renovação Concluída")
            self._refresh_ui()
        except ValueError as err:
            self.app.notify(str(err), severity="warning", title="Renovação Recusada")

    def action_sign_free_agent(self) -> None:
        if self.active_tab != "free_agents":
            self.app.notify("Alterne para a aba de Jogadores Livres [TAB] para contratar.", severity="warning")
            return

        state = self._get_state()
        if not state or not state.free_agents:
            return

        list_view = self.query_one("#players-list", ListView)
        idx = list_view.index
        if idx is None or idx < 0 or idx >= len(state.free_agents):
            return

        free_player = state.free_agents[idx]

        # Encontra o time do usuário
        user_team = None
        for champ in state.season_orchestrator.championships.values():
            t = next((team for team in champ.teams if team.name == state.player_team_name), None)
            if t:
                user_team = t
                break

        if not user_team:
            return

        try:
            sign_free_agent(
                team=user_team,
                player=free_player,
                years=3,
                economic_context=state.economic_context,
            )
            state.free_agents.remove(free_player)
            SaveManager().save_game(state)
            self.app.notify(f"{free_player.name} contratado como Jogador Livre sem taxa de transferência!", title="Reforço Contratado")
            self._refresh_ui()
        except ValueError as err:
            self.app.notify(str(err), severity="warning", title="Contratação Bloqueada")

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        state = self._get_state()
        if not state:
            return

        user_team = None
        for champ in state.season_orchestrator.championships.values():
            t = next((team for team in champ.teams if team.name == state.player_team_name), None)
            if t:
                user_team = t
                break

        if self.active_tab == "squad" and user_team and user_team.players:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(user_team.players):
                self._show_detail(user_team.players[idx], is_free=False)
        elif self.active_tab == "free_agents" and state.free_agents:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(state.free_agents):
                self._show_detail(state.free_agents[idx], is_free=True)

    def _refresh_ui(self) -> None:
        state = self._get_state()
        if not state:
            return

        user_team = None
        for champ in state.season_orchestrator.championships.values():
            t = next((team for team in champ.teams if team.name == state.player_team_name), None)
            if t:
                user_team = t
                break

        list_view = self.query_one("#players-list", ListView)
        list_view.clear()

        if self.active_tab == "squad":
            list_view.border_title = " SEU ELENCO (CONTRATOS) "
            if user_team:
                for p in user_team.players:
                    c = p.contract
                    tag = "EXPIRADO" if c.years_remaining == 0 else f"{c.years_remaining} ano(s)"
                    prot = " [PROT]" if c.is_protected else ""
                    line = f"{p.position.value[:3].upper()} {p.name:<20} OVR:{p.overall:>2} Anos:{tag}{prot}"
                    list_view.append(ListItem(Static(line)))
                if user_team.players:
                    self._show_detail(user_team.players[0], is_free=False)
        else:
            list_view.border_title = f" JOGADORES LIVRES ({len(state.free_agents)}) "
            for p in state.free_agents:
                line = f"{p.position.value[:3].upper()} {p.name:<20} Idade:{p.age:<2} OVR:{p.overall:>2} (Sem Clube)"
                list_view.append(ListItem(Static(line)))
            if state.free_agents:
                self._show_detail(state.free_agents[0], is_free=True)
            else:
                self.query_one("#contract-detail-panel", DosPanel).update("Nenhum jogador livre disponível no mercado.")

        # Atualiza painel de folha salarial
        if user_team:
            from garfoot.domain.squad_rules import calculate_wage_bill, calculate_wage_commitment, classify_wage_health
            bill = calculate_wage_bill(user_team)
            commit = calculate_wage_commitment(user_team)
            health = classify_wage_health(commit)

            self.query_one("#wage-health-panel", DosPanel).update(
                f"Tamanho do Elenco: {len(user_team.players)} / 30\n"
                f"Folha Salarial Anual: R$ {bill:,}\n"
                f"Comprometimento: {commit * 100:.1f}%\n"
                f"Saúde Salarial: {health.value.upper()}"
            )

    def _show_detail(self, player: Player, is_free: bool) -> None:
        c = player.contract
        text = (
            f"Nome: {player.name}\n"
            f"Posição: {player.position.value.upper()}\n"
            f"Idade: {player.age} anos | OVERALL: {player.overall}\n\n"
            f"Salário Atual: R$ {player.salary:,} / ano\n"
            f"Valor de Mercado: R$ {player.market_value:,}\n"
            f"Anos de Contrato Restantes: {c.years_remaining}\n"
            f"Protegido contra Venda: {'SIM' if c.is_protected else 'NÃO'}\n"
            f"Cláusula de Rescisão: R$ {c.release_clause:,}\n\n"
            f"Status: {'LIVRE (SEM TAXA)' if is_free else ('CONTRATO EXPIRADO' if c.years_remaining == 0 else 'CONTRATADO')}"
        )
        self.query_one("#contract-detail-panel", DosPanel).update(text)
