"""Eventos gerados durante a simulacao de uma partida."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias


class MatchEventType(StrEnum):
    """Tipos de eventos narraveis pelo motor de partida."""

    GOAL = "gol"
    SHOT = "chute"
    CARD = "cartao"
    INJURY = "lesao"
    MISSED_CHANCE = "chance_perdida"
    SUBSTITUTION = "substituicao"


class CardType(StrEnum):
    """Tipos de cartao aceitos na primeira versao."""

    YELLOW = "amarelo"
    RED = "vermelho"


class SubstitutionReason(StrEnum):
    """Motivo da substituição realizada."""

    TACTICAL = "tatica"
    FITNESS = "cansaco"
    INJURY = "lesao"
    HALF_TIME = "intervalo"
    CPU_AUTO = "cpu_auto"


@dataclass(frozen=True, slots=True)
class GoalEvent:
    """Gol marcado por um jogador."""

    minute: int
    team_name: str
    player_name: str
    assisted_by: str | None = None
    event_type: MatchEventType = MatchEventType.GOAL


@dataclass(frozen=True, slots=True)
class ShotEvent:
    """Chute que nao necessariamente vira gol."""

    minute: int
    team_name: str
    player_name: str
    on_target: bool
    event_type: MatchEventType = MatchEventType.SHOT


@dataclass(frozen=True, slots=True)
class CardEvent:
    """Cartao recebido por um jogador."""

    minute: int
    team_name: str
    player_name: str
    card_type: CardType
    event_type: MatchEventType = MatchEventType.CARD


@dataclass(frozen=True, slots=True)
class InjuryEvent:
    """Lesao sofrida por um jogador durante a partida."""

    minute: int
    team_name: str
    player_name: str
    severity: str = "leve"
    event_type: MatchEventType = MatchEventType.INJURY


@dataclass(frozen=True, slots=True)
class MissedChanceEvent:
    """Chance clara desperdicada por um jogador."""

    minute: int
    team_name: str
    player_name: str
    on_target: bool = False
    event_type: MatchEventType = MatchEventType.MISSED_CHANCE


@dataclass(frozen=True, slots=True)
class SubstitutionEvent:
    """Substituição de jogador realizada durante a partida."""

    minute: int
    team_name: str
    player_out_name: str
    player_in_name: str
    reason: SubstitutionReason = SubstitutionReason.TACTICAL
    event_type: MatchEventType = MatchEventType.SUBSTITUTION


MatchEvent: TypeAlias = (
    GoalEvent | ShotEvent | CardEvent | InjuryEvent | MissedChanceEvent | SubstitutionEvent
)
