"""Testes unitários para as regras de progressão de jogadores."""

from random import Random

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.player_progression import (
    MatchOutcome,
    apply_post_match_fatigue,
    apply_post_match_morale,
    apply_season_aging,
)


def _make_player(
    name: str = "Gabigol",
    age: int = 25,
    position: PlayerPosition = PlayerPosition.FORWARD,
    attack: int = 80,
    defense: int = 40,
    fitness: int = 80,
    morale: int = 80,
) -> Player:
    return Player(
        name=name,
        age=age,
        position=position,
        attack=attack,
        defense=defense,
        fitness=fitness,
        morale=morale,
        value=100_000,
    )


def test_apply_post_match_fatigue_starter_and_rest():
    p = _make_player(fitness=90)

    # Titular jogando 90 minutos
    tired = apply_post_match_fatigue(p, minutes_played=90, fitness_loss_starter=10)
    assert tired.fitness == 80

    # Reserva descansando
    rested = apply_post_match_fatigue(tired, minutes_played=0, fitness_recovery_rest=12)
    assert rested.fitness == 92


def test_apply_post_match_morale_win_loss_goals():
    p = _make_player(morale=70)

    # Vitória com 1 gol
    won = apply_post_match_morale(
        p,
        outcome=MatchOutcome.WIN,
        scored_goals=1,
        win_boost=4,
        goal_bonus=2,
    )
    assert won.morale == 76  # 70 + 4 + 2

    # Derrota sem gols
    lost = apply_post_match_morale(p, outcome=MatchOutcome.LOSS, loss_penalty=-4)
    assert lost.morale == 66  # 70 - 4


def test_apply_season_aging_young_evolution():
    young = _make_player(age=20, position=PlayerPosition.FORWARD, attack=75, defense=30)
    rng = Random(42)

    aged = apply_season_aging(young, rng=rng)
    assert aged is not None
    assert aged.age == 21
    assert aged.attack > 75  # Evoluiu em ataque


def test_apply_season_aging_veteran_decline_and_retirement():
    # Declínio veterano
    old = _make_player(age=35, attack=80, defense=50)
    rng = Random(42)

    aged_old = apply_season_aging(old, rng=rng)
    assert aged_old is not None
    assert aged_old.age == 36
    assert aged_old.attack < 80

    # Aposentadoria (idade > 38 e overall fraco)
    ancient = _make_player(
        age=38,
        position=PlayerPosition.MIDFIELDER,
        attack=20,
        defense=20,
        fitness=30,
        morale=30,
    )
    retired = apply_season_aging(ancient, retirement_age=38, max_retirement_ovr=50)
    assert retired is None
