"""Tela inicial (Menu Principal) do Garfoot limpa e sem redundâncias."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Static

from garfoot.ui.widgets.dos import DosPanel


class MainMenuScreen(Screen[None]):
    """Menu principal limpo com ações claras e comandos consolidados."""

    BINDINGS = [
        ("n", "new_game", "Novo Jogo"),
        ("1", "new_game", "Novo Jogo"),
        ("l", "load_game", "Carregar Jogo"),
        ("2", "load_game", "Carregar Jogo"),
        ("c", "continue_game", "Continuar"),
        ("3", "continue_game", "Continuar"),
        ("f1", "clubs", "Ver Clubes"),
        ("4", "clubs", "Ver Clubes"),
        ("f2", "standings", "Ver Tabela"),
        ("5", "standings", "Ver Tabela"),
        ("f3", "match", "Partida Demo"),
        ("6", "match", "Partida Demo"),
        ("f4", "quit", "Sair"),
        ("7", "quit", "Sair"),
        ("q", "quit", "Sair"),
    ]

    def compose(self) -> ComposeResult:
        state = getattr(self.app, "current_game_state", None)

        if state:
            opts = (
                "[bold green][1 / N][/bold green] NOVO JOGO\n"
                "[bold green][2 / L][/bold green] CARREGAR JOGO\n"
                f"[bold yellow][3 / C][/bold yellow] CONTINUAR CARREIRA ({state.player_team_name})\n"
                "[bold cyan][4 / F1][/bold cyan] VER CLUBES (DATASET 80 TIMES)\n"
                "[bold cyan][5 / F2][/bold cyan] VER TABELA DE CLASSIFICAÇÃO\n"
                "[bold cyan][6 / F3][/bold cyan] SIMULAR PARTIDA DEMO\n"
                "[bold red][7 / Q][/bold red] SAIR DO JOGO"
            )
        else:
            opts = (
                "[bold green][1 / N][/bold green] NOVO JOGO\n"
                "[bold green][2 / L][/bold green] CARREGAR JOGO\n"
                "[bold cyan][3 / F1][/bold cyan] VER CLUBES (DATASET 80 TIMES)\n"
                "[bold cyan][4 / F2][/bold cyan] VER TABELA DE CLASSIFICAÇÃO\n"
                "[bold cyan][5 / F3][/bold cyan] SIMULAR PARTIDA DEMO\n"
                "[bold red][6 / Q][/bold red] SAIR DO JOGO"
            )

        info_text = (
            "[bold white]GARFOOT 2026 — SISTEMA DE GERENCIAMENTO[/bold white]\n"
            "Edição Brasil 2026 | Desenvolvido por Leonardo Garcia\n\n"
            "[bold cyan]ESTRUTURA DE COMPETIÇÃO:[/bold cyan]\n"
            "  • Séries A, B, C e D (80 Clubes Reais)\n"
            "  • Copa do Brasil & Super Campeão\n"
            "  • Mercado de Transferências & Fair Play Financeiro"
        )

        yield Static("GARFOOT 2026 - MENU PRINCIPAL", id="title")

        with Horizontal(id="main-grid"):
            with Vertical(id="left-column"):
                yield DosPanel("OPÇÕES DO JOGO", opts, id="main-menu-panel")
            with Vertical(id="right-column"):
                yield DosPanel("INFORMAÇÕES DA TEMPORADA", info_text, id="season-panel")

        yield DosPanel(
            "COMANDOS",
            "[1-7 / N/L/C / F1-F4] Digite o número ou atalho correspondente   [Q / ESC] Sair",
            id="commands-panel",
        )

    def action_new_game(self) -> None:
        self.app.push_screen("new_game")

    def action_load_game(self) -> None:
        self.app.push_screen("load_game")

    def action_continue_game(self) -> None:
        state = getattr(self.app, "current_game_state", None)
        if state:
            self.app.push_screen("season_hub")
        else:
            self.app.push_screen("clubs")

    def action_clubs(self) -> None:
        self.app.push_screen("clubs")

    def action_standings(self) -> None:
        self.app.push_screen("standings")

    def action_match(self) -> None:
        self.app.push_screen("match")

    def action_quit(self) -> None:
        self.app.exit()
