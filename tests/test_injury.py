"""Testes automatizados para o sistema de lesões de jogadores."""

from random import Random
import pytest

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.injury import (
    Injury,
    InjurySeverity,
    advance_player_injury,
    apply_injury_to_player,
    create_injury,
)
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.engine.events import InjuryEvent
from garfoot.engine.match_engine import MatchResult, simulate_match
from garfoot.engine.match_progression import apply_post_match_progression


def test_create_injury_severities():
    rng = Random(42)

    minor = create_injury(InjurySeverity.MINOR, rng=rng)
    assert 1 <= minor.rounds_remaining <= 2
    assert 10 <= minor.fitness_penalty <= 20
    assert minor.attack_penalty == 0
    assert minor.defense_penalty == 0

    moderate = create_injury(InjurySeverity.MODERATE, rng=rng)
    assert 3 <= moderate.rounds_remaining <= 6
    assert 20 <= moderate.fitness_penalty <= 35

    severe = create_injury(InjurySeverity.SEVERE, rng=rng)
    assert 7 <= severe.rounds_remaining <= 15
    assert 35 <= severe.fitness_penalty <= 55


def test_apply_injury_to_player_limits_and_availability():
    player = Player(
        name="Gabriel",
        age=25,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=50,
        fitness=90,
        morale=80,
    )
    assert player.is_available is True
    assert player.is_injured is False

    injury = Injury(
        severity=InjurySeverity.MODERATE,
        rounds_remaining=4,
        description="Entorse",
        fitness_penalty=30,
        attack_penalty=2,
        defense_penalty=1,
    )

    injured_player = apply_injury_to_player(player, injury)
    assert injured_player.is_injured is True
    assert injured_player.is_available is False
    assert injured_player.fitness == 60  # 90 - 30
    assert injured_player.attack == 78   # 80 - 2
    assert injured_player.defense == 49  # 50 - 1
    assert injured_player.overall < player.overall


def test_advance_player_injury_recovery():
    player = Player(
        name="Bruno Henrique",
        age=30,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=50,
        fitness=50,
        morale=80,
        injury=Injury(severity=InjurySeverity.MINOR, rounds_remaining=2, fitness_penalty=15),
    )

    # 1ª Rodada: de 2 passa para 1 rodada restante
    r1 = advance_player_injury(player)
    assert r1.is_injured is True
    assert r1.injury.rounds_remaining == 1

    # 2ª Rodada: de 1 passa para 0 -> recuperado!
    r2 = advance_player_injury(r1)
    assert r2.is_injured is False
    assert r2.is_available is True
    assert r2.injury is None
    assert r2.fitness == 50  # Mantém a fitness sem restauração mágica para 100


def test_auto_select_starters_skips_injured_players():
    from garfoot.ui.screens.match_prep import MatchPrepScreen

    healthy_players = [
        Player(name=f"Saudavel {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80)
        for i in range(11)
    ]
    injured_star = Player(
        name="Craque Lesionado",
        age=25,
        position=PlayerPosition.FORWARD,
        attack=95,
        defense=95,
        fitness=30,
        morale=80,
        injury=Injury(severity=InjurySeverity.SEVERE, rounds_remaining=5),
    )

    team = Team(name="Time Teste", city="Rio", budget=100, players=healthy_players + [injured_star])
    prep = MatchPrepScreen()
    prep._auto_select_starters(team)

    # Craque lesionado NÃO deve ter sido escalado como titular
    assert "Craque Lesionado" not in prep.selected_starters
    assert len(prep.selected_starters) == 11


def test_injury_serialization_and_backwards_compatibility():
    # 1. to_dict & from_dict com lesão
    p = Player(
        name="Pedro",
        age=26,
        position=PlayerPosition.FORWARD,
        attack=85,
        defense=40,
        fitness=70,
        morale=80,
        injury=Injury(severity=InjurySeverity.MODERATE, rounds_remaining=3, description="Entorse joelho"),
    )
    serialized = p.to_dict()
    assert serialized["injury"]["severity"] == "moderate"
    assert serialized["injury"]["rounds_remaining"] == 3

    p_restored = Player.from_dict(serialized)
    assert p_restored.is_injured is True
    assert p_restored.injury.description == "Entorse joelho"

    # 2. Save antigo sem campo de lesão
    del serialized["injury"]
    p_old = Player.from_dict(serialized)
    assert p_old.injury is None
    assert p_old.is_available is True


def test_post_match_progression_applies_injury_event():
    p_home = [Player(name=f"Home {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p_away = [Player(name=f"Away {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    home = Team(name="Home Team", city="Rio", budget=100, players=p_home)
    away = Team(name="Away Team", city="SP", budget=100, players=p_away)

    inj_event = InjuryEvent(minute=25, team_name="Home Team", player_name="Home 0")
    result = MatchResult(
        home_team_name="Home Team",
        away_team_name="Away Team",
        home_score=1,
        away_score=0,
        events=(inj_event,),
        shots_home=5,
        shots_away=3,
        possession_home=50,
        possession_away=50,
        cards_home=0,
        cards_away=0,
        starters_home=tuple(p.name for p in p_home),
        starters_away=tuple(p.name for p in p_away),
    )

    new_home, new_away = apply_post_match_progression(home, away, result)
    injured_p = new_home.find_player("Home 0")

    assert injured_p is not None
    assert injured_p.is_injured is True
    assert injured_p.injury.rounds_remaining > 0


def test_engine_determinism_unaffected_by_injury_system():
    p1 = [Player(name=f"Home {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p2 = [Player(name=f"Away {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    home = Team(name="Time A", city="Rio", budget=100, players=p1)
    away = Team(name="Time B", city="SP", budget=100, players=p2)

    res1 = simulate_match(home, away, seed=777)
    res2 = simulate_match(home, away, seed=777)

    assert res1.home_score == res2.home_score
    assert res1.away_score == res2.away_score
    assert [e.minute for e in res1.events] == [e.minute for e in res2.events]
