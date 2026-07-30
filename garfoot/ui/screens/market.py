"""Tela de mercado de transferências (compras de jogadores)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.season import LeagueTier
from garfoot.domain.transfer_market import (
    TransferListing,
    execute_player_purchase,
    filter_transfer_listings,
    get_available_transfer_market,
)
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.widgets.dos import DosPanel

POS_LETTER_MAP = {
    PlayerPosition.GOALKEEPER: "G",
    PlayerPosition.DEFENDER: "D",
    PlayerPosition.MIDFIELDER: "M",
    PlayerPosition.FORWARD: "A",
}


class TransferMarketScreen(Screen[None]):
    """Tela para listar, filtrar e contratar jogadores no mercado de transferências."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("1", "filter_pos(None)", "Todos"),
        ("2", "filter_pos('GOALKEEPER')", "Goleiros"),
        ("3", "filter_pos('DEFENDER')", "Defensores"),
        ("4", "filter_pos('MIDFIELDER')", "Meias"),
        ("5", "filter_pos('FORWARD')", "Atacantes"),
        ("enter", "buy_selected", "Comprar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.all_listings: list[TransferListing] = []
        self.current_filter_pos: PlayerPosition | None = None

    def compose(self) -> ComposeResult:
        yield Static("MERCADO DE TRANSFERÊNCIAS (COMPRAS)", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="market-list")
            with Vertical(id="club-side"):
                yield DosPanel("FILTRO DE POSIÇÃO", "1 Todos   2 Goleiros   3 Defensores   4 Meias   5 Atacantes", id="filter-panel")
                yield DosPanel("DETALHES DA CONTRATAÇÃO", "Selecione um jogador na lista.", id="market-detail")
        yield DosPanel("COMANDOS", "[1-5] Filtrar Posição   [ENTER] Comprar Jogador   [ESC] Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._load_market()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def _load_market(self) -> None:
        state = self._get_state()
        if not state:
            return

        all_teams: list[Any] = []
        for champ in state.season_orchestrator.championships.values():
            all_teams.extend(champ.teams)

        from garfoot.domain.stable_random import combine_seed
        self.all_listings = get_available_transfer_market(
            teams=all_teams,
            user_team_name=state.player_team_name,
            seed=combine_seed(state.current_round, state.save_name, namespace="ui-transfer-market"),
        )
        self._refresh_list()

    def action_filter_pos(self, pos_str: str | None) -> None:
        if pos_str is None:
            self.current_filter_pos = None
        else:
            self.current_filter_pos = PlayerPosition[pos_str]
        self._refresh_list()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_buy_selected(self) -> None:
        selected_idx = self.query_one("#market-list", ListView).index
        visible = self._visible_listings()
        if selected_idx is None or selected_idx < 0 or selected_idx >= len(visible):
            return

        target_listing = visible[selected_idx]
        state = self._get_state()
        if not state:
            return

        # Encontra o time comprador (usuário) e o vendedor
        all_teams: list[Any] = []
        for champ in state.season_orchestrator.championships.values():
            all_teams.extend(champ.teams)

        buyer = next((t for t in all_teams if t.name == state.player_team_name), None)
        seller = next((t for t in all_teams if t.name == target_listing.seller_team_name), None)

        if not buyer or not seller:
            self.app.notify("Erro ao localizar clubes na transação.", severity="error")
            return

        try:
            execute_player_purchase(buyer, seller, target_listing)
            # Salva o estado pós-compra
            manager = SaveManager()
            manager.save_game(state)

            self.app.notify(
                f"{target_listing.player.name} contratado com sucesso por R$ {target_listing.asking_price:,}!",
                title="Contratação Realizada",
            )
            # Recarrega o mercado para remover o jogador comprado
            self._load_market()
        except ValueError as err:
            self.app.notify(str(err), severity="warning", title="Negociação Recusada")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_buy_selected()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        visible = self._visible_listings()
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(visible):
            self._show_detail(visible[idx])

    def _visible_listings(self) -> list[TransferListing]:
        return filter_transfer_listings(self.all_listings, position=self.current_filter_pos)

    def _refresh_list(self) -> None:
        list_view = self.query_one("#market-list", ListView)
        list_view.clear()
        visible = self._visible_listings()
        list_view.border_title = f" OFERTAS NO MERCADO ({len(visible)}) "

        for listing in visible:
            p = listing.player
            pos_code = POS_LETTER_MAP.get(p.position, "J")
            line = f"{pos_code} {p.name:<22} Idade:{p.age:<2} OVR:{p.overall:>2} R$ {listing.asking_price:>9,}"
            list_view.append(ListItem(Static(line)))

        if visible:
            self._show_detail(visible[0])
        else:
            self.query_one("#market-detail", DosPanel).update("Nenhum jogador encontrado com o filtro selecionado.")

    def _show_detail(self, listing: TransferListing) -> None:
        state = self._get_state()
        buyer_budget = 0
        if state:
            for champ in state.season_orchestrator.championships.values():
                t = next((team for team in champ.teams if team.name == state.player_team_name), None)
                if t:
                    buyer_budget = t.budget
                    break

        p = listing.player
        affordable_tag = "SIM" if buyer_budget >= listing.asking_price else "NÃO (Caixa Insuficiente)"
        rel_clause = p.contract.release_clause

        text = (
            f"Nome: {p.name}\n"
            f"Clube Vendedor: {listing.seller_team_name}\n"
            f"Posição: {p.position.value.upper()}\n"
            f"Idade: {p.age} anos | OVERALL: {p.overall}\n\n"
            f"Ataque: {p.attack:>2} | Defesa: {p.defense:>2}\n"
            f"Fadiga: {p.fitness:>2} | Moral: {p.morale:>2}\n\n"
            f"VALOR DE MERCADO: R$ {p.market_value:,}\n"
            f"PREÇO PEDIDO:    R$ {listing.asking_price:,}\n"
            f"CLÁUSULA RESCISÃO: R$ {rel_clause:,}\n"
            f"Seu Caixa Atual: R$ {buyer_budget:,}\n"
            f"Disponível para Compra: {affordable_tag}"
        )
        self.query_one("#market-detail", DosPanel).update(text)
