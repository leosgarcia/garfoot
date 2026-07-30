"""Tela de opções e configurações do jogo."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.game_settings import MatchSpeed
from garfoot.domain.game_state import GameState
from garfoot.persistence.save_manager import SaveManager
from garfoot.ui.widgets.dos import DosPanel

SPEED_OPTIONS: list[tuple[str, MatchSpeed, str]] = [
    ("Lenta", MatchSpeed.SLOW, "Delay longo entre os minutos (0.45s/tick)"),
    ("Normal", MatchSpeed.NORMAL, "Delay padrão para acompanhar a partida (0.25s/tick)"),
    ("Rápida", MatchSpeed.FAST, "Animação acelerada (0.08s/tick)"),
    ("Instantânea", MatchSpeed.INSTANT, "Sem delay - resultado final imediato sem animação"),
]


class OptionsScreen(Screen[None]):
    """Tela de configurações do jogo em estilo DOS / Textual."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("1", "select_speed(0)", "Lenta"),
        ("2", "select_speed(1)", "Normal"),
        ("3", "select_speed(2)", "Rápida"),
        ("4", "select_speed(3)", "Instantânea"),
        ("s", "toggle_sound", "Alternar Som"),
        ("enter", "confirm_selection", "Confirmar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.selected_index: int = 1  # Padrão Normal (índice 1)

    def compose(self) -> ComposeResult:
        yield Static("CONFIGURAÇÕES DO JOGO", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="speed-list")
            with Vertical(id="club-side"):
                yield DosPanel("OPÇÕES RÁPIDAS", "1 Lenta   2 Normal   3 Rápida   4 Instantânea\nS Alternar Áudio (SIM/NÃO)", id="filter-panel")
                yield DosPanel("DETALHES DA OPÇÃO", "Selecione uma velocidade.", id="speed-detail")
        yield DosPanel("COMANDOS", "[1-4 / ENTER] Velocidade   [S] Alternar Som (On/Off)   [ESC] Voltar", id="commands-panel")

    def on_mount(self) -> None:
        state = self._get_state()
        if state:
            current_speed = state.settings.match_speed
            for idx, (_, speed_enum, _) in enumerate(SPEED_OPTIONS):
                if speed_enum == current_speed:
                    self.selected_index = idx
                    break

        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_select_speed(self, index: int) -> None:
        if 0 <= index < len(SPEED_OPTIONS):
            self.selected_index = index
            self._apply_and_save_speed()

    def action_confirm_selection(self) -> None:
        selected_idx = self.query_one("#speed-list", ListView).index
        if selected_idx is not None and 0 <= selected_idx < len(SPEED_OPTIONS):
            self.selected_index = selected_idx
            self._apply_and_save_speed()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.action_confirm_selection()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(SPEED_OPTIONS):
            self.selected_index = idx
            self._update_detail(idx)

    def action_toggle_sound(self) -> None:
        state = self._get_state()
        if state:
            state.settings.sound_enabled = not state.settings.sound_enabled
            manager = SaveManager()
            manager.save_game(state)
            status_str = "ATIVADOS" if state.settings.sound_enabled else "DESATIVADOS"
            self.app.notify(f"Efeitos sonoros: {status_str}", title="Configuração de Som")
        self._refresh_ui()

    def _apply_and_save_speed(self) -> None:
        state = self._get_state()
        selected_tuple = SPEED_OPTIONS[self.selected_index]
        new_speed = selected_tuple[1]

        if state:
            state.settings.match_speed = new_speed
            manager = SaveManager()
            manager.save_game(state)
            self.app.notify(
                f"Velocidade da partida alterada para: {selected_tuple[0].upper()}",
                title="Configurações Salvas",
            )

        self._refresh_ui()

    def _refresh_ui(self) -> None:
        list_view = self.query_one("#speed-list", ListView)
        list_view.clear()
        list_view.border_title = " VELOCIDADE DAS PARTIDAS AO VIVO "

        for idx, (label, speed_enum, _) in enumerate(SPEED_OPTIONS):
            tag = " [SELECIONADA]" if idx == self.selected_index else ""
            line = f"{idx + 1}. {label:<16}{tag}"
            list_view.append(ListItem(Static(line)))

        self._update_detail(self.selected_index)

    def _update_detail(self, index: int) -> None:
        label, speed_enum, desc = SPEED_OPTIONS[index]
        state = self._get_state()
        current_saved_speed = state.settings.match_speed.value.upper() if state else "NORMAL"
        sound_status = "LIGADO (Beep)" if (state and state.settings.sound_enabled) else "DESLIGADO"

        text = (
            f"OPÇÃO: {label.upper()}\n\n"
            f"Valor do Enum: {speed_enum.value}\n"
            f"Delay entre Ticks: {speed_enum.delay_seconds} segundos\n\n"
            f"Descrição:\n{desc}\n\n"
            f"Velocidade Salva: {current_saved_speed}\n"
            f"Efeitos Sonoros (S): {sound_status}"
        )
        self.query_one("#speed-detail", DosPanel).update(text)
