"""Menu principal PySide6 do Garfoot."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


MENU_OPTIONS: tuple[tuple[str, str], ...] = (
    ("Novo Jogo", "new_game"),
    ("Carregar Jogo", "load_game"),
    ("Continuar Carreira", "season_hub"),
    ("Ver Clubes", "clubs"),
    ("Classificação", "standings"),
    ("Partida Demo", "match_demo"),
)

PLACEHOLDER_TITLES: dict[str, str] = {
    "new_game": "Novo Jogo - em desenvolvimento",
    "load_game": "Carregar Jogo - em desenvolvimento",
    "season_hub": "Continuar Carreira - em desenvolvimento",
    "clubs": "Clubes - em desenvolvimento",
    "standings": "Classificação - em desenvolvimento",
    "match_demo": "Partida Demo - em desenvolvimento",
}


class MainMenuScreen(QWidget):
    """Menu principal com botões grandes em estilo Windows clássico."""

    def __init__(self, on_select: Callable[[str], None], on_quit: Callable[[], None]) -> None:
        super().__init__()
        self.on_select = on_select
        self.on_quit = on_quit
        self.buttons: dict[str, QPushButton] = {}

        self.setObjectName("mainMenuScreen")
        self._build_layout()

    def _build_layout(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(16)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("GARFOOT 2026 - MENU PRINCIPAL")
        title.setObjectName("mainMenuTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        subtitle = QLabel("Edição Brasil 2026 | Desenvolvido por Leonardo Garcia")
        subtitle.setObjectName("mainMenuSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(subtitle)

        panel = QFrame()
        panel.setObjectName("mainMenuPanel")
        panel.setFrameShape(QFrame.Shape.Panel)
        panel.setFrameShadow(QFrame.Shadow.Raised)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 22, 24, 22)
        panel_layout.setSpacing(10)

        for label, target in MENU_OPTIONS:
            button = QPushButton(label)
            button.setObjectName("mainMenuButton")
            button.setMinimumHeight(42)
            button.clicked.connect(lambda _checked=False, screen=target: self.on_select(screen))
            self.buttons[target] = button
            panel_layout.addWidget(button)

        quit_button = QPushButton("Sair")
        quit_button.setObjectName("mainMenuButton")
        quit_button.setMinimumHeight(42)
        quit_button.clicked.connect(self.on_quit)
        self.buttons["quit"] = quit_button
        panel_layout.addWidget(quit_button)

        outer.addWidget(panel)

        info = QLabel(
            "Séries A, B, C e D com 80 clubes nacionais\n"
            "Copa do Brasil, Super Campeão, mercado e Fair Play Financeiro"
        )
        info.setObjectName("mainMenuInfo")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(info)


def build_placeholder_screen(title: str) -> QWidget:
    """Cria uma tela temporária para destinos ainda não migrados."""

    frame = QFrame()
    frame.setObjectName("emptyCentralFrame")

    layout = QVBoxLayout(frame)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(32, 32, 32, 32)

    label = QLabel(title)
    label.setObjectName("emptyCentralLabel")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(label)
    return frame
