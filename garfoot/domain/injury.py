"""Modelo e regras puras de lesões de jogadores."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from random import Random
from typing import Any

from garfoot.domain.enums import PlayerPosition

MIN_ATTRIBUTE = 1
MAX_ATTRIBUTE = 100


class InjurySeverity(StrEnum):
    """Severidade da lesão do jogador."""

    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass(frozen=True, slots=True)
class Injury:
    """Representa a lesão ativa de um jogador com afastamento e penalidades."""

    severity: InjurySeverity
    rounds_remaining: int
    description: str = ""
    fitness_penalty: int = 0
    attack_penalty: int = 0
    defense_penalty: int = 0

    def __post_init__(self) -> None:
        if self.rounds_remaining < 0:
            raise ValueError("O tempo restante de lesão não pode ser negativo.")

    @property
    def is_active(self) -> bool:
        return self.rounds_remaining > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "rounds_remaining": self.rounds_remaining,
            "description": self.description,
            "fitness_penalty": self.fitness_penalty,
            "attack_penalty": self.attack_penalty,
            "defense_penalty": self.defense_penalty,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Injury | None:
        if not data or not isinstance(data, dict):
            return None

        try:
            severity = InjurySeverity(data["severity"])
        except (KeyError, ValueError):
            return None

        return cls(
            severity=severity,
            rounds_remaining=int(data.get("rounds_remaining", 0)),
            description=str(data.get("description", "")),
            fitness_penalty=int(data.get("fitness_penalty", 0)),
            attack_penalty=int(data.get("attack_penalty", 0)),
            defense_penalty=int(data.get("defense_penalty", 0)),
        )


def create_injury(
    severity: InjurySeverity,
    rng: Random | None = None,
) -> Injury:
    """Cria uma lesão pura com base na severidade e gerador determinístico."""

    random_gen = rng if rng is not None else Random(42)

    if severity == InjurySeverity.MINOR:
        rounds = random_gen.randint(1, 2)
        fit_loss = random_gen.randint(10, 20)
        desc = "Estiramento muscular leve"
        att_loss = 0
        def_loss = 0
    elif severity == InjurySeverity.MODERATE:
        rounds = random_gen.randint(3, 6)
        fit_loss = random_gen.randint(20, 35)
        desc = "Entorse articular moderada"
        att_loss = random_gen.randint(0, 1)
        def_loss = random_gen.randint(0, 1)
    else:  # SEVERE
        rounds = random_gen.randint(7, 15)
        fit_loss = random_gen.randint(35, 55)
        desc = "Ruptura ligamentar grave"
        att_loss = random_gen.randint(1, 3)
        def_loss = random_gen.randint(1, 3)

    return Injury(
        severity=severity,
        rounds_remaining=rounds,
        description=desc,
        fitness_penalty=fit_loss,
        attack_penalty=att_loss,
        defense_penalty=def_loss,
    )


def apply_injury_to_player(player: Player, injury: Injury) -> Player:
    """Aplica uma nova lesão a um jogador, reduzindo forma física e atributos conforme a gravidade."""

    from dataclasses import replace

    new_fitness = max(MIN_ATTRIBUTE, min(MAX_ATTRIBUTE, player.fitness - injury.fitness_penalty))
    new_attack = max(MIN_ATTRIBUTE, min(MAX_ATTRIBUTE, player.attack - injury.attack_penalty))
    new_defense = max(MIN_ATTRIBUTE, min(MAX_ATTRIBUTE, player.defense - injury.defense_penalty))

    return replace(
        player,
        fitness=new_fitness,
        attack=new_attack,
        defense=new_defense,
        injury=injury,
    )


def advance_player_injury(player: Player) -> Player:
    """Avança 1 rodada no tempo de recuperação da lesão de um jogador.

    Quando o tempo restante chega a zero, a lesão é curada e o jogador volta a ficar disponível.
    """

    from dataclasses import replace

    if not player.is_injured or player.injury is None:
        return player

    new_rounds = player.injury.rounds_remaining - 1
    if new_rounds <= 0:
        # Recuperado! Volta a ser disponível
        return replace(player, injury=None)

    updated_injury = Injury(
        severity=player.injury.severity,
        rounds_remaining=new_rounds,
        description=player.injury.description,
        fitness_penalty=player.injury.fitness_penalty,
        attack_penalty=player.injury.attack_penalty,
        defense_penalty=player.injury.defense_penalty,
    )
    return replace(player, injury=updated_injury)


def advance_team_injuries(team: Team) -> Team:
    """Avança o tempo de recuperação de todos os jogadores lesionados do elenco do time."""

    from dataclasses import replace

    updated_players = [advance_player_injury(p) for p in team.players]
    return replace(team, players=updated_players)
