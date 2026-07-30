"""Regras puras de progressão, oscilação e envelhecimento de jogadores."""

from __future__ import annotations

from dataclasses import replace
from enum import Enum, auto
from random import Random

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.stable_random import stable_composite_seed


class MatchOutcome(Enum):
    """Resultado da partida para o time do jogador."""

    WIN = auto()
    DRAW = auto()
    LOSS = auto()


DEFAULT_STARTER_MINUTES = 90
DEFAULT_FITNESS_LOSS_PER_MATCH = 10
DEFAULT_FITNESS_RECOVERY_PER_REST = 12

DEFAULT_WIN_MORALE_BOOST = 4
DEFAULT_LOSS_MORALE_PENALTY = -4
DEFAULT_GOAL_MORALE_BONUS = 2

DEFAULT_RETIREMENT_AGE = 38
DEFAULT_RETIREMENT_MAX_OVERALL = 50


def apply_post_match_fatigue(
    player: Player,
    minutes_played: int = 0,
    fitness_loss_starter: int = DEFAULT_FITNESS_LOSS_PER_MATCH,
    fitness_recovery_rest: int = DEFAULT_FITNESS_RECOVERY_PER_REST,
) -> Player:
    """Aplica perda de forma física se o jogador atuou ou recuperação se descansou."""

    if minutes_played > 0:
        loss = round(fitness_loss_starter * (minutes_played / 90.0))
        new_fitness = max(1, min(100, player.fitness - loss))
    else:
        new_fitness = max(1, min(100, player.fitness + fitness_recovery_rest))

    return replace(player, fitness=new_fitness)


def apply_post_match_morale(
    player: Player,
    outcome: MatchOutcome,
    scored_goals: int = 0,
    win_boost: int = DEFAULT_WIN_MORALE_BOOST,
    loss_penalty: int = DEFAULT_LOSS_MORALE_PENALTY,
    goal_bonus: int = DEFAULT_GOAL_MORALE_BONUS,
) -> Player:
    """Aplica variação de moral com base no resultado e gols individuais."""

    delta = 0
    if outcome == MatchOutcome.WIN:
        delta += win_boost
    elif outcome == MatchOutcome.LOSS:
        delta += loss_penalty

    delta += scored_goals * goal_bonus
    new_morale = max(1, min(100, player.morale + delta))

    return replace(player, morale=new_morale)


def apply_season_aging(
    player: Player,
    rng: Random | None = None,
    retirement_age: int = DEFAULT_RETIREMENT_AGE,
    max_retirement_ovr: int = DEFAULT_RETIREMENT_MAX_OVERALL,
) -> Player | None:
    """Aplica o envelhecimento anual (+1 ano) e ajusta attack/defense.

    Retorna None se o jogador se aposentar.
    """

    new_age = player.age + 1

    if new_age > retirement_age and player.overall < max_retirement_ovr:
        return None

    random_gen = rng if rng is not None else Random(stable_composite_seed((player.name, new_age), namespace="player-progression"))

    new_att = player.attack
    new_def = player.defense

    if new_age < 23:
        boost = random_gen.randint(1, 3)
        if player.position == PlayerPosition.FORWARD:
            new_att = min(100, new_att + boost)
        elif player.position in (PlayerPosition.DEFENDER, PlayerPosition.GOALKEEPER):
            new_def = min(100, new_def + boost)
        else:
            new_att = min(100, new_att + random_gen.randint(0, 2))
            new_def = min(100, new_def + random_gen.randint(0, 2))
    elif new_age > 31:
        drop = random_gen.randint(1, 3)
        new_att = max(1, new_att - drop)
        new_def = max(1, new_def - drop)

    return replace(player, age=new_age, attack=new_att, defense=new_def)
