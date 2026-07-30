"""Dados fictícios para telas demonstrativas da UI."""

from __future__ import annotations

from garfoot.domain import Player, PlayerPosition, Team


POSITIONS = (
    [PlayerPosition.GOALKEEPER]
    + [PlayerPosition.DEFENDER] * 4
    + [PlayerPosition.MIDFIELDER] * 4
    + [PlayerPosition.FORWARD] * 2
)


def make_demo_team(name: str, rating: int) -> Team:
    """Cria um time completo para demonstrar a simulação de partida."""

    players = [
        Player(
            name=f"{name[:3].upper()} {index + 1}",
            age=24 + index % 8,
            position=position,
            attack=rating,
            defense=rating,
            fitness=rating,
            morale=rating,
            value=rating * 100,
        )
        for index, position in enumerate(POSITIONS)
    ]
    return Team(name=name, city="Demo", budget=1_000_000, players=players)
