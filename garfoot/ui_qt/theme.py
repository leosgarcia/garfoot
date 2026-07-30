"""Tema visual da interface PySide6 do Garfoot."""

from __future__ import annotations


def classic_windows_qss() -> str:
    """Retorna um QSS simples inspirado em aplicativos Windows 95/98.

    O objetivo do primeiro bloco é validar a stack Qt com uma identidade
    clássica discreta. Ajustes finos de tela ficam para os blocos seguintes.
    """

    return """
    QMainWindow {
        background: #c0c0c0;
    }

    QWidget {
        background: #c0c0c0;
        color: #000000;
        font-family: "Arial", "Helvetica", sans-serif;
        font-size: 10pt;
    }

    QMenuBar, QMenu, QStatusBar, QToolBar {
        background: #c0c0c0;
        color: #000000;
    }

    QMenuBar::item:selected, QMenu::item:selected {
        background: #000080;
        color: #ffffff;
    }

    QFrame#emptyCentralFrame {
        background: #c0c0c0;
        border: 2px inset #ffffff;
    }

    QLabel#emptyCentralLabel {
        color: #000080;
        font-family: "Courier New", monospace;
        font-weight: bold;
    }


    QWidget#splashScreen {
        background: #c0c0c0;
    }

    QLabel#splashBanner {
        color: #000080;
        background: #c0c0c0;
    }

    QLabel#splashSubtitle, QLabel#splashPrompt, QLabel#panelTitle {
        color: #000080;
        font-weight: bold;
    }

    QFrame#classicPanel {
        background: #d4d0c8;
        border: 2px inset #ffffff;
    }

    QLabel#panelBody {
        background: #d4d0c8;
        color: #000000;
    }


    QWidget#mainMenuScreen {
        background: #c0c0c0;
    }

    QLabel#mainMenuTitle {
        color: #000080;
        font-family: "Arial", "Helvetica", sans-serif;
        font-size: 16pt;
        font-weight: bold;
    }

    QLabel#mainMenuSubtitle, QLabel#mainMenuInfo {
        color: #000000;
    }

    QFrame#mainMenuPanel {
        background: #d4d0c8;
        border: 2px outset #ffffff;
        min-width: 360px;
        max-width: 480px;
    }

    QPushButton#mainMenuButton {
        background: #d4d0c8;
        border: 2px outset #ffffff;
        color: #000000;
        font-weight: bold;
        padding: 6px 18px;
        text-align: left;
    }

    QPushButton#mainMenuButton:hover, QPushButton#mainMenuButton:focus {
        background: #000080;
        color: #ffffff;
    }

    QPushButton#mainMenuButton:pressed {
        border: 2px inset #ffffff;
    }
    """
