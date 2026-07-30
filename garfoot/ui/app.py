"""Aplicação Textual do Garfoot."""

from __future__ import annotations

from textual.app import App

from garfoot.ui.screens.board_inbox import BoardInboxScreen
from garfoot.ui.screens.clubs import ClubsScreen
from garfoot.ui.screens.contracts import ContractsScreen
from garfoot.ui.screens.live_match import LiveMatchScreen
from garfoot.ui.screens.load_game import LoadGameScreen
from garfoot.ui.screens.main_menu import MainMenuScreen
from garfoot.ui.screens.news import NewsScreen
from garfoot.ui.screens.market import TransferMarketScreen
from garfoot.ui.screens.match import MatchScreen
from garfoot.ui.screens.match_prep import MatchPrepScreen
from garfoot.ui.screens.new_game import NewGameScreen
from garfoot.ui.screens.options import OptionsScreen
from garfoot.ui.screens.rankings import RankingsScreen
from garfoot.ui.screens.season_hub import SeasonHubScreen
from garfoot.ui.screens.splash import SplashOpeningScreen
from garfoot.ui.screens.standings import StandingsScreen


class GarfootApp(App[None]):
    """TUI retrô, navegável por teclado."""

    CSS = """
    $accent: #00ff66;
    $surface: #050505;
    $panel: #0aa6a6;
    $blue: #0700a8;
    $green: #00a800;
    $red: #9c0000;
    $amber: #ffbf00;

    Screen {
        background: black;
        color: white;
        layout: vertical;
        padding: 0 1;
    }

    #title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        border: solid $accent;
        margin-bottom: 1;
    }

    #main-grid, #clubs-grid, #match-grid {
        height: 1fr;
    }

    #left-column, #right-column, #club-side {
        width: 1fr;
    }

    #main-menu-panel {
        height: 1fr;
        background: $panel;
        color: white;
        padding: 1 2;
    }

    #season-panel {
        height: 1fr;
        background: $blue;
        color: white;
        padding: 1 2;
    }

    #footer-menu, #commands-panel {
        height: 4;
        background: $blue;
        color: white;
        border: solid white;
        padding: 0 1;
    }

    #club-list {
        width: 2fr;
        border: solid $accent;
        background: black;
        color: white;
    }

    ListItem {
        height: 1;
    }

    ListItem.--highlight {
        background: $blue;
        color: white;
    }

    #club-side {
        width: 3fr;
    }

    #filter-panel {
        height: 8;
        background: $green;
        color: black;
    }

    #club-detail {
        height: 1fr;
        background: $panel;
        color: white;
    }

    #standings-panel {
        height: 1fr;
        background: black;
        color: white;
    }

    #commentary-panel {
        width: 2fr;
        background: black;
        color: $amber;
    }

    #score-panel {
        width: 1fr;
        background: $panel;
        color: white;
    }

    #hub-grid {
        height: 1fr;
    }

    #hub-left {
        width: 2fr;
    }

    #hub-middle {
        width: 2fr;
    }

    #hub-right {
        width: 3fr;
    }

    #status-panel {
        height: 8;
        background: $blue;
        color: white;
    }

    #club-summary-panel {
        height: 1fr;
        background: $green;
        color: black;
    }

    #next-match-panel {
        height: 1fr;
        background: $panel;
        color: white;
    }

    #hub-standings-panel {
        height: 1fr;
        background: black;
        color: white;
    }

    #squad-list {
        width: 3fr;
        border: solid $accent;
        background: black;
        color: white;
    }

    #club-info-panel {
        height: 7;
        background: $panel;
        color: white;
    }

    #tactics-list-panel {
        height: 1fr;
        background: $green;
        color: black;
    }

    #prep-bottom-grid {
        height: 7;
    }

    #fixture-info-panel {
        width: 1fr;
        background: $blue;
        color: white;
    }

    #finance-info-panel {
        width: 1fr;
        background: $panel;
        color: white;
    }

    #live-timer-header {
        height: 3;
        content-align: center middle;
        background: $green;
        color: black;
        text-style: bold;
        margin-bottom: 1;
    }

    #live-grid {
        height: 1fr;
    }

    #live-left-column {
        width: 1fr;
    }

    #live-right-column {
        width: 1fr;
    }

    #live-panel-left {
        height: 1fr;
        background: black;
        color: white;
    }

    #live-panel-right {
        height: 1fr;
        background: black;
        color: white;
    }

    #splash-container {
        height: 1fr;
        content-align: center middle;
        align: center middle;
        background: black;
        padding: 1 2;
    }

    #splash-banner {
        width: 100%;
        content-align: center middle;
        color: $accent;
        text-style: bold;
    }

    #splash-subtitle {
        width: 100%;
        content-align: center middle;
        color: $amber;
        text-style: bold;
        margin-bottom: 1;
    }

    #splash-credits-panel {
        width: 100%;
        border: solid $panel;
        background: $surface;
        color: white;
        padding: 0 2;
        margin-bottom: 1;
    }

    #splash-features-panel {
        width: 100%;
        border: solid $green;
        background: $surface;
        color: white;
        padding: 1 2;
        margin-bottom: 1;
    }

    #splash-prompt {
        width: 100%;
        content-align: center middle;
        margin-top: 1;
    }

    #board-msg-list {
        width: 1fr;
        height: 1fr;
        background: $surface;
        border: solid $accent;
    }

    #board-msg-detail {
        height: 12;
        background: $blue;
        color: white;
    }

    #board-options-panel {
        height: 1fr;
        background: $panel;
        color: white;
    }

    DosPanel {
        margin: 0 1 1 0;
    }
    """

    SCREENS = {
        "splash": SplashOpeningScreen,
        "main": MainMenuScreen,
        "new_game": NewGameScreen,
        "load_game": LoadGameScreen,
        "clubs": ClubsScreen,
        "standings": StandingsScreen,
        "match": MatchScreen,
        "match_prep": MatchPrepScreen,
        "season_hub": SeasonHubScreen,
        "live_match": LiveMatchScreen,
        "market": TransferMarketScreen,
        "contracts": ContractsScreen,
        "options": OptionsScreen,
        "news": NewsScreen,
        "rankings": RankingsScreen,
        "board_inbox": BoardInboxScreen,
    }

    BINDINGS = [("q", "quit", "Sair")]

    def on_mount(self) -> None:
        self.push_screen("splash")


def main() -> None:
    GarfootApp().run()


if __name__ == "__main__":
    main()
