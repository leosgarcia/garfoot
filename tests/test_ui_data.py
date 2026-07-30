"""Testes para a camada de dados usada pelas interfaces."""

from garfoot.ui.data import clubs_by_series, load_clubs, load_teams_by_series


def test_load_teams_by_series_filters_dataset_series():
    clubs = load_clubs()

    for series in ("A", "B", "C", "D"):
        expected_clubs = clubs_by_series(clubs, series)
        teams = load_teams_by_series(series)

        assert len(teams) == 20
        assert len(teams) == len(expected_clubs)
        assert {team.name for team in teams} == {club["name"] for club in expected_clubs}


def test_load_teams_by_series_accepts_lowercase_series():
    teams = load_teams_by_series("d")
    serie_d_names = {club["name"] for club in clubs_by_series(load_clubs(), "D")}

    assert len(teams) == 20
    assert {team.name for team in teams} == serie_d_names
