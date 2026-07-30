"""Smoke tests do esqueleto PySide6 em modo sem display."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel

from garfoot.ui_qt.app import build_app
from garfoot.ui_qt.main_window import GarfootMainWindow
from garfoot.ui_qt.screens.main_menu import MainMenuScreen, PLACEHOLDER_TITLES
from garfoot.ui_qt.screens.splash import SplashScreen


def test_qt_app_builds_main_window_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])

    assert app.applicationName() == "Garfoot"
    assert isinstance(window, GarfootMainWindow)
    assert window.stack.count() == 2 + len(PLACEHOLDER_TITLES)
    assert window.windowTitle() == "Garfoot 2026"
    assert set(window.screens) == {"splash", "main_menu", *PLACEHOLDER_TITLES}
    assert isinstance(window.screens["splash"], SplashScreen)
    assert isinstance(window.screens["main_menu"], MainMenuScreen)
    assert window.stack.currentWidget() is window.screens["splash"]

    window.close()


def test_xcb_dependency_check_explains_missing_cursor_library(monkeypatch):
    from garfoot.ui_qt import app as qt_app

    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setattr(qt_app.ctypes.util, "find_library", lambda name: None)

    try:
        qt_app._validate_linux_xcb_dependencies(["garfoot"])
    except RuntimeError as err:
        assert "sudo apt install libxcb-cursor0" in str(err)
    else:
        raise AssertionError("RuntimeError esperado quando libxcb-cursor esta ausente")


def test_xcb_dependency_check_skips_offscreen(monkeypatch):
    from garfoot.ui_qt import app as qt_app

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("DISPLAY", ":99")
    monkeypatch.setattr(qt_app.ctypes.util, "find_library", lambda name: None)

    qt_app._validate_linux_xcb_dependencies(["garfoot"])


def test_splash_key_press_switches_to_main_menu_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    window.show()

    splash = window.screens["splash"]
    assert window.stack.currentWidget() is splash

    splash.setFocus()
    QTest.keyClick(splash, Qt.Key.Key_Return)
    app.processEvents()

    assert window.stack.currentWidget() is window.screens["main_menu"]
    window.close()


def test_splash_click_switches_to_main_menu_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    window.show()

    splash = window.screens["splash"]
    window.show_screen("splash")
    assert window.stack.currentWidget() is splash

    QTest.mouseClick(splash, Qt.MouseButton.LeftButton)
    app.processEvents()

    assert window.stack.currentWidget() is window.screens["main_menu"]
    window.close()


def _placeholder_text(window, screen_name: str) -> str:
    labels = window.screens[screen_name].findChildren(QLabel)
    return "\n".join(label.text() for label in labels)


def test_main_menu_buttons_switch_to_distinct_placeholders_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    window.show()
    window.show_screen("main_menu")

    menu = window.screens["main_menu"]
    assert isinstance(menu, MainMenuScreen)

    for screen_name, expected_title in PLACEHOLDER_TITLES.items():
        window.show_screen("main_menu")
        QTest.mouseClick(menu.buttons[screen_name], Qt.MouseButton.LeftButton)
        app.processEvents()

        assert window.stack.currentWidget() is window.screens[screen_name]
        assert expected_title in _placeholder_text(window, screen_name)

    window.close()


def test_main_menu_quit_button_closes_window_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    window.show()
    window.show_screen("main_menu")

    menu = window.screens["main_menu"]
    assert window.isVisible()

    QTest.mouseClick(menu.buttons["quit"], Qt.MouseButton.LeftButton)
    app.processEvents()

    assert not window.isVisible()


def test_file_exit_action_closes_window_offscreen():
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    window.show()

    window.exit_action.trigger()
    app.processEvents()

    assert not window.isVisible()


def test_help_about_action_opens_message_box(monkeypatch):
    app, window = build_app(["garfoot-test", "-platform", "offscreen"])
    calls = []

    def fake_about(parent, title, text):
        calls.append((parent, title, text))

    from garfoot.ui_qt import main_window as main_window_module

    monkeypatch.setattr(main_window_module.QMessageBox, "about", fake_about)
    window.about_action.trigger()
    app.processEvents()

    assert calls
    assert calls[0][0] is window
    assert calls[0][1] == "Sobre o Garfoot"
    assert "LEONARDO GARCIA" in calls[0][2]
    window.close()
