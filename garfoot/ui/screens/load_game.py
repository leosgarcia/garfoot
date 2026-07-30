"""Tela de Carregar Jogo na TUI."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.game_state import SaveMetadata
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.widgets.dos import DosPanel


class LoadGameScreen(Screen[None]):
    """Tela para listar e carregar um jogo salvo previamente."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("enter", "load_selected", "Carregar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.save_manager = SaveManager()
        self.saves: list[SaveMetadata] = []

    def compose(self) -> ComposeResult:
        yield Static("CARREGAR JOGO SALVO", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="save-list")
            with Vertical(id="club-side"):
                yield DosPanel("DETALHES DO SAVE", "Selecione um arquivo de save.", id="save-detail")
        yield DosPanel("COMANDOS", "ENTER Carregar Save   ESC Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_list()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_load_selected(self) -> None:
        selected_idx = self.query_one("#save-list", ListView).index
        if selected_idx is not None and 0 <= selected_idx < len(self.saves):
            meta = self.saves[selected_idx]
            try:
                state = self.save_manager.load_game(meta.filepath)
                setattr(self.app, "current_game_state", state)
                self.app.notify(f"Save '{state.save_name}' carregado!", title="Sucesso")
                self.app.switch_screen("season_hub")
            except Exception as err:
                self.app.notify(f"Erro ao carregar save: {err}", severity="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_load_selected()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            idx = event.list_view.index
            if idx is not None and 0 <= idx < len(self.saves):
                self._show_detail(self.saves[idx])

    def _refresh_list(self) -> None:
        list_view = self.query_one("#save-list", ListView)
        list_view.clear()
        self.saves = self.save_manager.list_saves()
        list_view.border_title = f" SAVES ENCONTRADOS ({len(self.saves)}) "

        if not self.saves:
            self.query_one("#save-detail", DosPanel).update("Nenhum jogo salvo foi encontrado.")
            return

        for meta in self.saves:
            label = f"{meta.save_name:<20} | {meta.player_team_name}"
            list_view.append(ListItem(Static(label)))

        self._show_detail(self.saves[0])

    def _show_detail(self, meta: SaveMetadata) -> None:
        text = (
            f"Nome do Save: {meta.save_name}\n"
            f"Clube: {meta.player_team_name}\n"
            f"Temporada: {meta.season_year}\n"
            f"Rodada Atual: {meta.current_round}\n"
            f"Salvo em: {meta.saved_at[:19].replace('T', ' ')}\n\n"
            f"Arquivo:\n{meta.filepath}"
        )
        self.query_one("#save-detail", DosPanel).update(text)
