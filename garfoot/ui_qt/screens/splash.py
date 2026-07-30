"""Tela de abertura PySide6 do Garfoot."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


BANNER_DOS_GARFOOT = r"""
  ██████╗   █████╗  ██████╗  ███████╗ ██████╗  ██████╗ ████████╗
 ██╔════╝  ██╔══██╗ ██╔══██╗ ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝
 ██║  ███╗ ███████║ ██████╔╝ █████╗  ██║   ██║██║   ██║   ██║   
 ██║   ██║ ██╔══██║ ██╔══██╗ ██╔══╝  ██║   ██║██║   ██║   ██║   
 ╚██████╔╝ ██║  ██║ ██║  ██║ ██║     ╚██████╔╝╚██████╔╝   ██║   
  ╚═════╝  ╚═╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝      ╚═════╝  ╚═════╝    ╚═╝   
"""

SPLASH_SUBTITLE = "FUTEBOL DE GERENCIAMENTO - EDIÇÃO BRASIL 2026"
SPLASH_CREDITS_CONTENT = (
    "DESENVOLVIDO POR: LEONARDO GARCIA\n"
    "(C) 2026 GARFOOT SOFTWARE - INSPIRADO NOS CLÁSSICOS DOS DE FUTEBOL E ELIFOOT"
)
SPLASH_FEATURES_CONTENT = (
    "[COMPETIÇÕES]  * Séries A, B, C e D com 80 Clubes Nacionais\n"
    "               * Copa do Brasil com Fase Preliminar & Super Campeão\n\n"
    "[GESTÃO]       * Mercado de Transferências, Rescisões e Agentes Livres\n"
    "               * Contratos, Salários, Lesões e Chicotadas Psicológicas\n"
    "               * Estádios, Empréstimos Bancários e Fair Play Financeiro"
)
PROMPT_TEXT = ">> PRESSIONE QUALQUER TECLA OU CLIQUE PARA INICIAR <<"


class SplashScreen(QWidget):
    """Splash inicial em estilo Windows clássico com alma de DOS.

    A tela chama ``on_continue`` quando qualquer tecla ou clique é recebido.
    O logo ASCII foi preservado em fonte monoespaçada para manter a identidade
    visual do Garfoot durante a transição para PySide6.
    """

    def __init__(self, on_continue: Callable[[], None] | None = None) -> None:
        super().__init__()
        self.on_continue = on_continue
        self._prompt_visible = True

        self.setObjectName("splashScreen")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._build_layout()

        # Primeiro bloco Qt: mantemos apenas o prompt piscando. O boot em
        # cascata da TUI pode voltar depois se a direção visual pedir.
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_prompt)
        self._blink_timer.start(500)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.banner_label = QLabel(BANNER_DOS_GARFOOT)
        self.banner_label.setObjectName("splashBanner")
        self.banner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.banner_label.setFont(QFont("Courier New", 10, QFont.Weight.Bold))
        layout.addWidget(self.banner_label)

        self.subtitle_label = QLabel(SPLASH_SUBTITLE)
        self.subtitle_label.setObjectName("splashSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.subtitle_label)

        credits = self._make_panel("CRÉDITOS E AUTORIA", SPLASH_CREDITS_CONTENT)
        layout.addWidget(credits)

        features = self._make_panel("RECURSOS DO SISTEMA", SPLASH_FEATURES_CONTENT)
        layout.addWidget(features)

        self.prompt_label = QLabel(PROMPT_TEXT)
        self.prompt_label.setObjectName("splashPrompt")
        self.prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.prompt_label)

    def _make_panel(self, title: str, content: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("classicPanel")
        frame.setFrameShape(QFrame.Shape.Panel)
        frame.setFrameShadow(QFrame.Shadow.Sunken)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("panelTitle")
        layout.addWidget(title_label)

        body_label = QLabel(content)
        body_label.setObjectName("panelBody")
        body_label.setFont(QFont("Courier New", 9))
        body_label.setWordWrap(True)
        layout.addWidget(body_label)
        return frame

    def _toggle_prompt(self) -> None:
        self._prompt_visible = not self._prompt_visible
        self.prompt_label.setVisible(self._prompt_visible)

    def _continue(self) -> None:
        self._blink_timer.stop()
        if self.on_continue is not None:
            self.on_continue()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        self._continue()
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self._continue()
        event.accept()
