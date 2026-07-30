"""Testes de sanidade para telas e rotas da TUI Textual."""

from garfoot.ui.app import GarfootApp
from garfoot.ui.screens.contracts import ContractsScreen
from garfoot.ui.screens.news import NewsScreen
from garfoot.ui.screens.rankings import RankingsScreen


def test_contracts_screen_instantiates_with_default_tab():
    screen = ContractsScreen()

    assert screen.active_tab == "squad"


def test_functional_auxiliary_screens_are_registered():
    assert GarfootApp.SCREENS["contracts"] is ContractsScreen
    assert GarfootApp.SCREENS["news"] is NewsScreen
    assert GarfootApp.SCREENS["rankings"] is RankingsScreen


def test_parameterized_screens_are_not_registered_as_plain_routes():
    # Estas telas exigem dados no construtor e devem ser abertas como instância,
    # não por rota simples em GarfootApp.SCREENS.
    assert "season_awards" not in GarfootApp.SCREENS
    assert "round_results" not in GarfootApp.SCREENS
