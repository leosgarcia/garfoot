"""Janela principal da interface PySide6 do Garfoot."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget, QWidget

from garfoot.ui_qt.screens.main_menu import MainMenuScreen, PLACEHOLDER_TITLES, build_placeholder_screen
from garfoot.ui_qt.screens.splash import SPLASH_CREDITS_CONTENT, SplashScreen


class GarfootMainWindow(QMainWindow):
    """Janela principal única da UI Qt."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Garfoot 2026")
        self.resize(1024, 720)

        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)
        self.screens: dict[str, QWidget] = {}

        self._build_menu_bar()
        self._build_status_bar()
        self._install_initial_pages()

    def _build_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&Arquivo")
        self.exit_action = file_menu.addAction("Sair")
        self.exit_action.triggered.connect(self.close)

        help_menu = menu_bar.addMenu("A&juda")
        self.about_action = help_menu.addAction("Sobre")
        self.about_action.triggered.connect(self.show_about_dialog)

    def _build_status_bar(self) -> None:
        self.statusBar().showMessage("Garfoot Qt: Bloco 2 concluído")

    def _install_initial_pages(self) -> None:
        splash = SplashScreen(on_continue=lambda: self.show_screen("main_menu"))
        menu = MainMenuScreen(on_select=self.show_screen, on_quit=self.close)

        self.add_screen("splash", splash)
        self.add_screen("main_menu", menu)

        for name, title in PLACEHOLDER_TITLES.items():
            self.add_screen(name, build_placeholder_screen(title))

        self.show_screen("splash")

    def add_screen(self, name: str, widget: QWidget) -> None:
        """Registra uma tela no stack central."""

        self.screens[name] = widget
        self.stack.addWidget(widget)

    def show_screen(self, name: str) -> None:
        """Mostra uma tela registrada pelo nome."""

        self.stack.setCurrentWidget(self.screens[name])

    def show_about_dialog(self) -> None:
        """Mostra os créditos em uma caixa de diálogo clássica."""

        QMessageBox.about(
            self,
            "Sobre o Garfoot",
            f"GARFOOT 2026\n\n{SPLASH_CREDITS_CONTENT}",
        )
