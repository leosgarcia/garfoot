"""Tela TUI da Caixa de Entrada da Diretoria (Board Inbox) para tomada de decisões."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import ListItem, ListView, Static

from garfoot.domain.board_inbox import (
    BoardMessage,
    BoardMessageOption,
    BoardMessageStatus,
    BoardMessageType,
    process_board_decision,
)
from garfoot.domain.game_state import GameState
from garfoot.ui.widgets.dos import DosPanel

TYPE_LABELS = {
    BoardMessageType.RESULTS_WARNING: "[TÉCNICO/DESEMPENHO]",
    BoardMessageType.FINANCIAL_ALERT: "[ALERTA FINANCEIRO]",
    BoardMessageType.INVESTMENT_RESPONSE: "[INVESTIMENTO]",
    BoardMessageType.SEASON_CONGRATULATIONS: "[RECONHECIMENTO]",
    BoardMessageType.BOARD_ULTIMATUM: "[ULTIMATO DA DIRETORIA]",
}

STATUS_LABELS = {
    BoardMessageStatus.PENDING: "[bold yellow]PENDENTE[/bold yellow]",
    BoardMessageStatus.ACCEPTED: "[bold green]ACEITO[/bold green]",
    BoardMessageStatus.REJECTED: "[bold red]RECUSADO[/bold red]",
    BoardMessageStatus.EXPIRED: "[bold dim]EXPIRADO[/bold dim]",
    BoardMessageStatus.INFO_READ: "[bold white]LIDO[/bold white]",
}


class BoardInboxScreen(Screen[None]):
    """Tela interativa da Caixa de Entrada da Diretoria com lista e tomada de decisão."""

    BINDINGS = [
        ("escape", "back", "Voltar"),
        ("1", "select_option(0)", "Opção 1"),
        ("2", "select_option(1)", "Opção 2"),
        ("a", "select_option(0)", "Opção 1"),
        ("b", "select_option(1)", "Opção 2"),
        ("enter", "confirm_selection", "Confirmar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.selected_msg_idx: int = 0
        self.selected_opt_idx: int = 0

    def compose(self) -> ComposeResult:
        yield Static("CAIXA DE ENTRADA DA DIRETORIA - COMUNICADOS E DECISÕES", id="title")
        with Horizontal(id="clubs-grid"):
            yield ListView(id="board-msg-list")
            with Vertical(id="club-side"):
                yield DosPanel("COMUNICADO OFICIAL", "Selecione uma mensagem.", id="board-msg-detail")
                yield DosPanel("DECISÃO DO GESTOR", "Nenhuma opção selecionada.", id="board-options-panel")
        yield DosPanel("COMANDOS", "[1/2 / A/B] Selecionar Opção   [ENTER] Confirmar Decisão   [ESC] Voltar", id="commands-panel")

    def on_mount(self) -> None:
        self._refresh_ui()

    def _get_state(self) -> GameState | None:
        return getattr(self.app, "current_game_state", None)

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        if event.item is not None:
            list_view = self.query_one("#board-msg-list", ListView)
            if list_view.index is not None:
                self.selected_msg_idx = list_view.index
                self.selected_opt_idx = 0
                self._update_detail_panels()

    def action_select_option(self, opt_idx: int) -> None:
        state = self._get_state()
        if not state or not state.board_inbox.messages:
            return

        if 0 <= self.selected_msg_idx < len(state.board_inbox.messages):
            msg = state.board_inbox.messages[self.selected_msg_idx]
            if msg.status == BoardMessageStatus.PENDING and 0 <= opt_idx < len(msg.options):
                self.selected_opt_idx = opt_idx
                self._update_detail_panels()

    def action_confirm_selection(self) -> None:
        state = self._get_state()
        if not state or not state.board_inbox.messages:
            return

        if 0 <= self.selected_msg_idx < len(state.board_inbox.messages):
            msg = state.board_inbox.messages[self.selected_msg_idx]
            if msg.status == BoardMessageStatus.PENDING and msg.options:
                opt = msg.options[min(self.selected_opt_idx, len(msg.options) - 1)]
                process_board_decision(state, msg.id, opt.id)
                self.app.notify(f"Decisão confirmada: {opt.text}", severity="information")
                self._refresh_ui()

    def action_back(self) -> None:
        self.app.pop_screen()

    def _refresh_ui(self) -> None:
        state = self._get_state()
        list_view = self.query_one("#board-msg-list", ListView)
        list_view.clear()

        if not state or not state.board_inbox.messages:
            list_view.border_title = " MENSAGENS (0) "
            list_view.append(ListItem(Static("(Nenhuma mensagem na caixa de entrada)")))
            self.query_one("#board-msg-detail", DosPanel).update("Nenhuma mensagem pendente.")
            self.query_one("#board-options-panel", DosPanel).update("Sem opções de decisão.")
            return

        inbox = state.board_inbox
        list_view.border_title = f" COMUNICADOS ({inbox.unread_count()} PENDENTES) "

        for msg in inbox.messages:
            type_tag = TYPE_LABELS.get(msg.message_type, "[DIRETORIA]")
            status_tag = STATUS_LABELS.get(msg.status, "")
            line = f"{type_tag:<22} R{msg.round_created:>2} {msg.title:<30} {status_tag}"
            list_view.append(ListItem(Static(line)))

        if 0 <= self.selected_msg_idx < len(inbox.messages):
            list_view.index = self.selected_msg_idx
        else:
            list_view.index = 0
            self.selected_msg_idx = 0

        self._update_detail_panels()

    def _update_detail_panels(self) -> None:
        state = self._get_state()
        if not state or not state.board_inbox.messages:
            return

        inbox = state.board_inbox
        if not (0 <= self.selected_msg_idx < len(inbox.messages)):
            return

        msg = inbox.messages[self.selected_msg_idx]
        status_text = STATUS_LABELS.get(msg.status, str(msg.status))
        type_str = TYPE_LABELS.get(msg.message_type, "COMUNICADO")

        detail_text = (
            f"[bold white]{msg.title.upper()}[/bold white]\n"
            f"Tipo: {type_str} | Status: {status_text} | Criado na Rodada {msg.round_created}\n"
            f"------------------------------------------------------------------------------\n"
            f"{msg.content}"
        )
        if msg.expires_at_round and msg.status == BoardMessageStatus.PENDING:
            detail_text += f"\n\n[bold yellow]ATENÇÃO: Resposta exigida até a Rodada {msg.expires_at_round}![/bold yellow]"

        self.query_one("#board-msg-detail", DosPanel).update(detail_text)

        # Atualiza painel de opções de decisão
        if msg.status != BoardMessageStatus.PENDING:
            opt_text = f"Decisão já encerrada com status {status_text}."
            if msg.selected_option_id:
                sel_opt = next((o for o in msg.options if o.id == msg.selected_option_id), None)
                if sel_opt:
                    opt_text += f"\nOpção Escolhida: [bold white]{sel_opt.text}[/bold white]"
        elif not msg.options:
            opt_text = "Comunicado puramente informativo (sem decisões requeridas)."
        else:
            opt_lines = ["OPÇÕES DE RESPOSTA DA DIRETORIA:\n"]
            for idx, opt in enumerate(msg.options):
                prefix = "[bold yellow]>[/bold yellow]" if idx == self.selected_opt_idx else " "
                opt_lines.append(
                    f"{prefix} [{idx + 1} / {'A' if idx == 0 else 'B'}] [bold white]{opt.text}[/bold white]\n"
                    f"    Efeito: {opt.description}\n"
                )
            opt_lines.append("\nPressione [1/2] ou [A/B] para selecionar e [ENTER] para confirmar.")
            opt_text = "\n".join(opt_lines)

        self.query_one("#board-options-panel", DosPanel).update(opt_text)
