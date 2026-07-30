"""Testes automatizados para a velocidade de partida e configurações do jogo (GameSettings)."""

import pytest

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_settings import GameSettings, MatchSpeed
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.engine.match_engine import simulate_match
from garfoot.persistence.save_manager import SaveManager


def test_match_speed_delays_mapping():
    assert MatchSpeed.SLOW.delay_seconds == 0.45
    assert MatchSpeed.NORMAL.delay_seconds == 0.25
    assert MatchSpeed.FAST.delay_seconds == 0.08
    assert MatchSpeed.INSTANT.delay_seconds == 0.0


def test_game_settings_serialization_and_fallback():
    # 1. Defaults
    settings = GameSettings()
    assert settings.match_speed == MatchSpeed.NORMAL

    # 2. to_dict & from_dict
    settings_fast = GameSettings(match_speed=MatchSpeed.FAST)
    serialized = settings_fast.to_dict()
    assert serialized["match_speed"] == "rapida"

    deserialized = GameSettings.from_dict(serialized)
    assert deserialized.match_speed == MatchSpeed.FAST

    # 3. Fallback seguro para dicts inválidos ou nulos
    assert GameSettings.from_dict(None).match_speed == MatchSpeed.NORMAL
    assert GameSettings.from_dict({}).match_speed == MatchSpeed.NORMAL
    assert GameSettings.from_dict({"match_speed": "invalido"}).match_speed == MatchSpeed.NORMAL


def test_game_state_settings_backwards_compatibility(tmp_path):
    from garfoot.domain.cup import KnockoutCup
    from garfoot.domain.league import Championship
    from garfoot.domain.season import LeagueTier
    from garfoot.domain.team import Team

    teams = [Team(name="Flamengo", city="Rio", budget=100_000), Team(name="Vasco", city="Rio", budget=100_000)]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams)
    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams)
    orchestrator = SeasonOrchestrator(season_year=2026, championships={LeagueTier.SERIE_A: champ_a}, copa_do_brasil=copa)

    state = GameState(
        save_name="Save Antigo",
        player_team_name="Flamengo",
        current_season=2026,
        current_round=1,
        season_orchestrator=orchestrator,
    )

    data = state.to_dict()
    # Simula um save antigo removendo a chave 'settings'
    del data["settings"]

    loaded_state = GameState.from_dict(data)
    assert loaded_state.settings.match_speed == MatchSpeed.NORMAL


def test_save_manager_persists_match_speed(tmp_path):
    from garfoot.domain.cup import KnockoutCup
    from garfoot.domain.league import Championship
    from garfoot.domain.season import LeagueTier
    from garfoot.domain.team import Team

    teams = [Team(name="Flamengo", city="Rio", budget=100_000), Team(name="Vasco", city="Rio", budget=100_000)]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams)
    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams)
    orchestrator = SeasonOrchestrator(season_year=2026, championships={LeagueTier.SERIE_A: champ_a}, copa_do_brasil=copa)

    manager = SaveManager(save_dir=tmp_path)
    state = GameState(
        save_name="Save Velocidade",
        player_team_name="Flamengo",
        current_season=2026,
        current_round=1,
        season_orchestrator=orchestrator,
        settings=GameSettings(match_speed=MatchSpeed.SLOW),
    )

    filepath = manager.save_game(state)
    loaded_state = manager.load_game(filepath)

    assert loaded_state.settings.match_speed == MatchSpeed.SLOW


def test_match_engine_determinism_unaffected_by_speed_settings():
    """Garante que a engine de partida permaneça pura e determinística.

    A mesma seed produz exatamente o mesmo resultado independente de qualquer
    configuração de UI / velocidade.
    """
    p1 = [Player(name=f"Home {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p2 = [Player(name=f"Away {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    from garfoot.domain.team import Team
    home = Team(name="Time Casa", city="Cidade A", budget=100, players=p1)
    away = Team(name="Time Fora", city="Cidade B", budget=100, players=p2)

    res1 = simulate_match(home, away, seed=12345)
    res2 = simulate_match(home, away, seed=12345)

    assert res1.home_score == res2.home_score
    assert res1.away_score == res2.away_score
    assert [e.minute for e in res1.events] == [e.minute for e in res2.events]
