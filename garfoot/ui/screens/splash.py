"""Tela de Abertura / Intro Splash Screen retrô do Garfoot (estilo DOS / MS-DOS)."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

# Banner ASCII de 6 linhas exato para a palavra GARFOOT
# G - A - R - F - O - O - T
ASCII_BANNER = r"""
 ██████╗  █████╗ ██████╗ ██████xFF██████╗  ██████╗ ██████╗ ████████╗
██╔════╝ ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
██║  ███╗███████║██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║   ██║   
██║   ██║██╔══██║██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██║   ██║   ██║   
╚██████╔╝██║  ██║██║  ██║██║     ██║     ╚██████╔╝╚██████╔╝   ██║   
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   
""".replace("██████xFF", "███████╗")

ASCII_BANNER_GARFOOT = r"""
  ____  ____  ____  _____ ____  ____ _____ 
 / ___|/ ___||  _ \|  ___/ ___|/ ___|_   _|
| |  _ | |  _| |_) | |_ | |  _| |  _| | |  
| |_| || |_| |  _ <|  _|| |_| | |_| | | |  
 \____(_)____|_| \_\_|   \____|\____| |_|  
"""

# Letras FIGlet / Slant extremamente claras de 6 linhas para G - A - R - F - O - O - T:
BANNER_GARFOOT_PRECISE = r"""
  ██████╗  █████╗ ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗
 ██╔════╝ ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
 ██║  ███╗███████║██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║   ██║   
 ██║   ██║██╔══██║██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██║   ██║   ██║   
 ╚██████╔╝██║  ██║██║  ██║██║     ██║     ╚██████╔╝╚██████╔╝   ██║   
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   
"""

# Vamos redesenhar caractere por caractere manualmente em fonte ANSI Block perfeita para G-A-R-F-O-O-T:
BANNER_EXACT_GARFOOT = r"""
 █▀▀▀▀█ █▀▀▀█ █▀▀▀█ █▀▀▀▀ █▀▀▀█ █▀▀▀█ ▀▀█▀▀
 █ ▀▀██ █▀▀▀█ █▀▀▀█ █▀▀▀  █   █ █   █   █  
 █▄▄▄██ █   █ █   █ █    ▄█▄▄▄█ █▄▄▄█   █  
"""

# Banner FIGlet Ansishade limpo e 100% correto sem ambiguidade:
BANNER_FIGLET_GARFOOT = r"""
   ___   _   ___ ___ _____  ___ _____ 
  / __| /_\ | _ \ __| __/ _ \ _ \_   _|
 | (_ |/ _ \|   / _|| _| (_) | (_) || |  
  \___/_/ \_\_|_|_| |_| \___/ \___/ |_|  
"""

BANNER_CLEAN = r"""
 ██████╗  █████╗ ██████╗ ███████╗██████╗  ██████╗ ██████╗ ████████╗
██╔════╝ ██╔══██╗██╔══██╗██╔════╝██╔══██╗██╔═══██╗██╔═══██╗╚══██╔══╝
██║  ███╗███████║██████╔╝█████╗  ██████╔╝██║   ██║██║   ██║   ██║   
██║   ██║██╔══██║██╔══██╗██╔══╝  ██╔═══╝ ██║   ██║██║   ██║   ██║   
╚██████╔╝██║  ██║██║  ██║██║     ██║     ╚██████╔╝╚██████╔╝   ██║   
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   
"""

# Desenho manual limpo em caixa DOS (G A R F O O T)
BANNER_DOS_GARFOOT = r"""
  ██████╗   █████╗  ██████╗  ███████╗ ██████╗  ██████╗ ████████╗
 ██╔════╝  ██╔══██╗ ██╔══██╗ ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝
 ██║  ███╗ ███████║ ██████╔╝ █████╗  ██║   ██║██║   ██║   ██║   
 ██║   ██║ ██╔══██║ ██╔══██╗ ██╔══╝  ██║   ██║██║   ██║   ██║   
 ╚██████╔╝ ██║  ██║ ██║  ██║ ██║     ╚██████╔╝╚██████╔╝   ██║   
  ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   
"""

SPLASH_SUBTITLE = "FUTEBOL DE GERENCIAMENTO — EDIÇÃO BRASIL 2026"

SPLASH_CREDITS_HEADER = "CRÉDITOS E AUTORIA"
SPLASH_CREDITS_CONTENT = """DESENVOLVIDO POR: [bold yellow]LEONARDO GARCIA[/bold yellow]
(C) 2026 GARFOOT SOFTWARE — INSPIRADO NOS CLÁSSICOS DOS DE FUTEBOL E ELIFOOT"""

SPLASH_FEATURES_HEADER = "RECURSOS DO SISTEMA"
SPLASH_FEATURES_CONTENT = """[bold cyan][COMPETIÇÕES][/bold cyan]  [bold yellow]*[/bold yellow] Séries A, B, C e D com 80 Clubes Nacionais
                [bold yellow]*[/bold yellow] Copa do Brasil com Fase Preliminar & Super Campeão

[bold cyan][GESTÃO][/bold cyan]       [bold yellow]*[/bold yellow] Mercado de Transferências, Rescisões e Agentes Livres
                [bold yellow]*[/bold yellow] Contratos, Salários, Lesões e [bold yellow]Chicotadas Pisicológicas[/bold yellow]
                [bold yellow]*[/bold yellow] Estádios, Empréstimos Bancários e Fair Play Financeiro"""

SPLASH_PROMPT_VISIBLE = "[bold yellow]>> PRESSIONE QUALQUER TECLA OU ENTER PARA INICIAR <<[/bold yellow]"
SPLASH_PROMPT_HIDDEN = "[bold black]>> PRESSIONE QUALQUER TECLA OU ENTER PARA INICIAR <<[/bold black]"


class SplashOpeningScreen(Screen[None]):
    """Tela de Abertura vibrante com estilo DOS, efeito boot em cascata e prompt piscando."""

    BINDINGS = [
        ("enter", "continue", "Iniciar"),
        ("space", "continue", "Iniciar"),
        ("escape", "continue", "Iniciar"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._blink_state = True
        self._boot_step = 0
        self._boot_timer: Timer | None = None
        self._blink_timer: Timer | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="splash-container"):
            yield Static("", id="splash-banner")
            yield Static("", id="splash-subtitle")
            yield Static("", id="splash-credits-panel")
            yield Static("", id="splash-features-panel")
            yield Static("", id="splash-prompt")

    def on_mount(self) -> None:
        """Inicia o efeito de boot em cascata (revelando blocos a cada 80ms)."""
        self._boot_timer = self.set_interval(0.08, self._step_boot_animation)

    def _step_boot_animation(self) -> None:
        """Aparece elemento a elemento sequencialmente estilo boot do DOS."""
        self._boot_step += 1

        if self._boot_step == 1:
            self.query_one("#splash-banner", Static).update(BANNER_DOS_GARFOOT)
        elif self._boot_step == 2:
            self.query_one("#splash-subtitle", Static).update(SPLASH_SUBTITLE)
        elif self._boot_step == 3:
            panel = self.query_one("#splash-credits-panel", Static)
            panel.update(SPLASH_CREDITS_CONTENT)
            panel.border_title = f" {SPLASH_CREDITS_HEADER} "
        elif self._boot_step == 4:
            panel = self.query_one("#splash-features-panel", Static)
            panel.update(SPLASH_FEATURES_CONTENT)
            panel.border_title = f" {SPLASH_FEATURES_HEADER} "
        elif self._boot_step >= 5:
            self.query_one("#splash-prompt", Static).update(SPLASH_PROMPT_VISIBLE)
            if self._boot_timer:
                self._boot_timer.stop()
                self._boot_timer = None
            # Inicia o piscar (blink) do prompt
            self._blink_timer = self.set_interval(0.5, self._toggle_blink)

    def _toggle_blink(self) -> None:
        """Alterna a visibilidade do prompt em intervalo regular."""
        self._blink_state = not self._blink_state
        prompt_widget = self.query_one("#splash-prompt", Static)
        if self._blink_state:
            prompt_widget.update(SPLASH_PROMPT_VISIBLE)
        else:
            prompt_widget.update(SPLASH_PROMPT_HIDDEN)

    def on_key(self, event: Any) -> None:
        """Pressionar qualquer tecla cancela a animação imediatamente e avança para o menu."""
        self.action_continue()

    def action_continue(self) -> None:
        """Avança para o Menu Principal de forma segura e limpa."""
        if self._boot_timer:
            self._boot_timer.stop()
            self._boot_timer = None
        if self._blink_timer:
            self._blink_timer.stop()
            self._blink_timer = None
        self.app.switch_screen("main")
