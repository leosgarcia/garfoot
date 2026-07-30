"""Regressão de compatibilidade para saves antigos mínimos."""

from garfoot.domain.game_state import GameState


def _legacy_team(name: str) -> dict[str, object]:
    return {
        "name": name,
        "city": "Cidade",
        "budget": 100_000,
        "players": [],
        "formation": {"defenders": 4, "midfielders": 4, "forwards": 2},
        "starting_player_names": [],
        "stadium": None,
    }


def test_minimal_legacy_save_loads_with_safe_defaults() -> None:
    """Um save antigo sem campos recentes deve carregar sem erro."""

    legacy_save = {
        "save_name": "Save antigo",
        "player_team_name": "Time A",
        "current_season": 2026,
        "current_round": 1,
        "season_orchestrator": {
            "season_year": 2026,
            "championships": {},
            "copa_do_brasil": {
                "name": "Copa antiga",
                "season_year": 2026,
                "teams": [_legacy_team("Time A"), _legacy_team("Time B")],
                "rounds": [],
            },
            "super_champion_match": None,
        },
        "saved_at": "",
    }

    state = GameState.from_dict(legacy_save)

    assert state.settings is not None
    assert state.statistics is not None
    assert state.economic_context is not None
    assert state.free_agents == []
    assert state.news_center.items == []
