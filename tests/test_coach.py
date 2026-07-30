"""Testes automatizados para o sistema de treinadores, demissões, contratações e chicotada psicológica."""

from random import Random
import pytest

from garfoot.domain.coach import (
    Coach,
    CoachBounceEffect,
    CoachStatus,
    CoachStyle,
    calculate_coach_pressure,
    create_coach_bounce_effect,
    select_best_coach_for_team,
    should_sack_coach,
)
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.engine.match_engine import simulate_match


def test_coach_model_attributes_and_serialization():
    coach = Coach(
        name="Dorival Júnior",
        reputation=85,
        tactical_skill=80,
        morale_management=90,
        pressure_resistance=75,
        style=CoachStyle.BALANCED,
    )

    assert coach.status == CoachStatus.FREE_AGENT

    serialized = coach.to_dict()
    assert serialized["name"] == "Dorival Júnior"
    assert serialized["status"] == "free_agent"

    restored = Coach.from_dict(serialized)
    assert restored is not None
    assert restored.name == "Dorival Júnior"
    assert restored.style == CoachStyle.BALANCED


def test_calculate_coach_pressure_rules():
    # 1. Time em boa posição sem derrotas -> Pressão baixa
    p_low = calculate_coach_pressure(
        team_squad_strength=70,
        standing_position=2,
        total_teams=20,
        recent_results=["W", "W", "D"],
        coach_pressure_resistance=80,
    )
    assert p_low < 40

    # 2. Time em rebaixamento com derrotas seguidas -> Pressão alta/crítica
    p_high = calculate_coach_pressure(
        team_squad_strength=75,
        standing_position=19,  # Penúltimo
        total_teams=20,
        recent_results=["L", "L", "L"],
        coach_pressure_resistance=30,
    )
    assert p_high >= 70


def test_should_sack_coach_thresholds():
    # Risco < 60 nunca demite
    assert should_sack_coach(pressure=50) is False

    # Risco crítico (90) com RNG determinístico
    rng = Random(42)
    assert should_sack_coach(pressure=90, rng=rng) is True


def test_select_best_coach_for_team_hiring():
    c1 = Coach(name="Técnico A", reputation=60, tactical_skill=60, morale_management=60, pressure_resistance=60)
    c2 = Coach(name="Técnico B", reputation=90, tactical_skill=85, morale_management=85, pressure_resistance=80)

    coaches_pool = [c1, c2]

    best = select_best_coach_for_team("Flamengo", coaches_pool, "SERIE_A")
    assert best is not None
    assert best.name == "Técnico B"


def test_coach_bounce_effect_creation_and_morale():
    coach = Coach(name="Renato Gaúcho", reputation=80, tactical_skill=80, morale_management=90, pressure_resistance=70)
    effect = create_coach_bounce_effect(coach, rng=Random(100))

    assert 3 <= effect.rounds_remaining <= 5
    assert effect.morale_bonus > 0
    assert effect.rating_bonus > 0

    # Testa aplicação da moral média no Team
    players = [Player(name=f"Player {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=70) for i in range(11)]
    team = Team(name="Grêmio", city="Porto Alegre", budget=100, players=players, bounce_effect=effect)

    # Moral base dos jogadores = 70.0; com o efeito deve aumentar sem alterar permanentemente os jogadores
    assert team.average_morale() > 70.0
    assert team.players[0].morale == 70  # Jogador não foi alterado permanentemente


def test_team_serialization_with_coach_and_backwards_compatibility():
    coach = Coach(name="Abel Ferreira", reputation=90, tactical_skill=90, morale_management=85, pressure_resistance=90)
    effect = CoachBounceEffect(rounds_remaining=3, morale_bonus=5.0, rating_bonus=0.03, source_coach_name="Abel Ferreira")

    team = Team(name="Palmeiras", city="SP", budget=1000, coach=coach, bounce_effect=effect)
    serialized = team.to_dict()

    assert serialized["coach"]["name"] == "Abel Ferreira"
    assert serialized["bounce_effect"]["rounds_remaining"] == 3

    restored = Team.from_dict(serialized)
    assert restored.coach is not None
    assert restored.coach.name == "Abel Ferreira"
    assert restored.bounce_effect is not None
    assert restored.bounce_effect.rounds_remaining == 3

    # Saves antigos sem a chave coach carregam normalmente como None
    del serialized["coach"]
    del serialized["bounce_effect"]
    old_restored = Team.from_dict(serialized)
    assert old_restored.coach is None
    assert old_restored.bounce_effect is None


def test_engine_determinism_unaffected_by_coach_system():
    p1 = [Player(name=f"Home {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p2 = [Player(name=f"Away {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    c1 = Coach(name="Técnico Home", reputation=70, tactical_skill=70, morale_management=70, pressure_resistance=70)
    c2 = Coach(name="Técnico Away", reputation=70, tactical_skill=70, morale_management=70, pressure_resistance=70)

    home = Team(name="Time A", city="Rio", budget=100, players=p1, coach=c1)
    away = Team(name="Time B", city="SP", budget=100, players=p2, coach=c2)

    res1 = simulate_match(home, away, seed=888)
    res2 = simulate_match(home, away, seed=888)

    assert res1.home_score == res2.home_score
    assert res1.away_score == res2.away_score
