"""Ponto de entrada da interface PySide6 do Garfoot."""

from __future__ import annotations

import ctypes.util
import os
import sys

from PySide6.QtWidgets import QApplication

from garfoot.ui_qt.main_window import GarfootMainWindow
from garfoot.ui_qt.theme import classic_windows_qss


XCB_CURSOR_ERROR = """Não foi possível iniciar a UI Qt com o plugin xcb.

O PySide6 encontrou o plugin xcb, mas o Qt 6.5+ precisa da biblioteca de
sistema xcb-cursor para carregar esse plugin no Linux.

Em Debian/Ubuntu, instale com:

    sudo apt install libxcb-cursor0

Se você estiver em um servidor sem ambiente gráfico e quiser apenas validar o
smoke test, use:

    QT_QPA_PLATFORM=offscreen .venv/bin/pytest tests/test_ui_qt_app.py -q
"""


def _selected_qt_platform(argv: list[str]) -> str | None:
    """Descobre a plataforma Qt solicitada por env var ou argumento CLI."""

    if "QT_QPA_PLATFORM" in os.environ:
        return os.environ["QT_QPA_PLATFORM"]

    for index, arg in enumerate(argv):
        if arg == "-platform" and index + 1 < len(argv):
            return argv[index + 1]
        if arg.startswith("-platform="):
            return arg.split("=", 1)[1]
    return None


def _validate_linux_xcb_dependencies(argv: list[str]) -> None:
    """Evita abort/core dump quando falta libxcb-cursor no Linux."""

    if not sys.platform.startswith("linux"):
        return

    platform = _selected_qt_platform(argv)
    if platform and platform != "xcb":
        return

    # Sem DISPLAY/Wayland, o erro esperado é outro; deixamos o Qt ou o teste
    # offscreen cuidar disso. Esta checagem mira especificamente o plugin xcb.
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return

    if ctypes.util.find_library("xcb-cursor") is None:
        raise RuntimeError(XCB_CURSOR_ERROR)


def build_app(argv: list[str] | None = None) -> tuple[QApplication, GarfootMainWindow]:
    """Cria a aplicação Qt e a janela principal sem iniciar o loop de eventos.

    Separar construção e execução permite validar a janela em modo offscreen
    nos testes/CI, sem depender de um display gráfico real.
    """

    app_argv = argv if argv is not None else sys.argv
    _validate_linux_xcb_dependencies(app_argv)

    app = QApplication.instance()
    if app is None:
        app = QApplication(app_argv)

    app.setApplicationName("Garfoot")
    app.setStyleSheet(classic_windows_qss())

    window = GarfootMainWindow()
    return app, window


def main() -> int:
    try:
        app, window = build_app()
    except RuntimeError as err:
        print(err, file=sys.stderr)
        return 1

    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
