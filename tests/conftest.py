"""Fixtures compartilhadas para testes do Garfoot."""

from __future__ import annotations

import pytest

from garfoot.domain import Player, PlayerPosition, Team


POSITIONS = (
    [PlayerPosition.GOALKEEPER]
    + [PlayerPosition.DEFENDER] * 4
    + [PlayerPosition.MIDFIELDER] * 4
    + [PlayerPosition.FORWARD] * 2
)


def make_player(name: str, position: PlayerPosition, base_rating: int) -> Player:
    """Cria jogador com overall previsivel perto de ``base_rating``."""

    return Player(
        name=name,
        age=25,
        position=position,
        attack=base_rating,
        defense=base_rating,
        fitness=base_rating,
        morale=base_rating,
        value=base_rating * 100,
    )


def make_squad(prefix: str, base_rating: int, size: int = 11) -> list[Player]:
    players: list[Player] = []
    for index in range(size):
        position = POSITIONS[index % len(POSITIONS)]
        players.append(make_player(f"{prefix} {index + 1}", position, base_rating))
    return players


def make_team(name: str, base_rating: int, size: int = 11) -> Team:
    return Team(
        name=name,
        city="Cidade Teste",
        budget=1_000_000,
        players=make_squad(name, base_rating, size),
    )


@pytest.fixture
def strong_team() -> Team:
    return make_team("Forte FC", 80)


@pytest.fixture
def weak_team() -> Team:
    return make_team("Fraco FC", 45)


@pytest.fixture
def equal_home_team() -> Team:
    return make_team("Casa Igual", 65)


@pytest.fixture
def equal_away_team() -> Team:
    return make_team("Fora Igual", 65)


@pytest.fixture
def short_roster_home() -> Team:
    return make_team("Curto Casa", 65, size=5)


@pytest.fixture
def short_roster_away() -> Team:
    return make_team("Curto Fora", 60, size=4)
