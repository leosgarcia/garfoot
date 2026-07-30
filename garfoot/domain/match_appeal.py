"""Regras puras de rivalidade, apelo do adversário e impacto na lotação do estádio."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RivalryLevel(StrEnum):
    """Níveis de rivalidade entre dois clubes."""

    NONE = "none"
    REGIONAL = "regional"
    STATE_CLASSIC = "state_classic"
    CITY_CLASSIC = "city_classic"
    HISTORIC = "historic"


class MatchImportance(StrEnum):
    """Níveis de importância da partida no campeonato/temporada."""

    NORMAL = "normal"
    DIRECT_TABLE_RIVAL = "direct_table_rival"
    RELEGATION_BATTLE = "relegation_battle"
    PROMOTION_BATTLE = "promotion_battle"
    TITLE_DECIDER = "title_decider"
    KNOCKOUT = "knockout"
    SEMIFINAL = "semifinal"
    FINAL = "final"


class OpponentAppeal(StrEnum):
    """Apelo e poder de atração do clube visitante."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    NATIONAL = "national"


RIVALRY_BONUS: dict[RivalryLevel, float] = {
    RivalryLevel.NONE: 0.00,
    RivalryLevel.REGIONAL: 0.03,
    RivalryLevel.STATE_CLASSIC: 0.07,
    RivalryLevel.CITY_CLASSIC: 0.10,
    RivalryLevel.HISTORIC: 0.12,
}

OPPONENT_APPEAL_BONUS: dict[OpponentAppeal, float] = {
    OpponentAppeal.LOW: -0.03,
    OpponentAppeal.MEDIUM: 0.00,
    OpponentAppeal.HIGH: 0.04,
    OpponentAppeal.NATIONAL: 0.08,
}

MATCH_IMPORTANCE_BONUS: dict[MatchImportance, float] = {
    MatchImportance.NORMAL: 0.00,
    MatchImportance.DIRECT_TABLE_RIVAL: 0.03,
    MatchImportance.RELEGATION_BATTLE: 0.04,
    MatchImportance.PROMOTION_BATTLE: 0.06,
    MatchImportance.TITLE_DECIDER: 0.08,
    MatchImportance.KNOCKOUT: 0.05,
    MatchImportance.SEMIFINAL: 0.08,
    MatchImportance.FINAL: 0.12,
}


@dataclass(frozen=True, slots=True)
class MatchAppealContext:
    """Contexto de atratividade e apelo de uma partida de futebol."""

    rivalry_level: RivalryLevel = RivalryLevel.NONE
    match_importance: MatchImportance = MatchImportance.NORMAL
    opponent_appeal: OpponentAppeal = OpponentAppeal.MEDIUM
    same_state: bool = False
    same_city: bool = False
    is_knockout: bool = False
    is_final: bool = False


def calculate_rivalry_bonus(rivalry_level: RivalryLevel) -> float:
    """Retorna o bônus de taxa de ocupação para o nível de rivalidade."""

    return RIVALRY_BONUS.get(rivalry_level, 0.00)


def calculate_opponent_appeal_bonus(appeal: OpponentAppeal) -> float:
    """Retorna a variação da taxa de ocupação com base no apelo do adversário."""

    return OPPONENT_APPEAL_BONUS.get(appeal, 0.00)


def calculate_match_importance_bonus(importance: MatchImportance) -> float:
    """Retorna o bônus de ocupação pela importância decisiva da partida."""

    return MATCH_IMPORTANCE_BONUS.get(importance, 0.00)


def calculate_match_appeal_factor(context: MatchAppealContext) -> float:
    """Calcula o bônus acumulado de atratividade do jogo sobre a taxa de ocupação do estádio."""

    r_bonus = calculate_rivalry_bonus(context.rivalry_level)
    a_bonus = calculate_opponent_appeal_bonus(context.opponent_appeal)
    i_bonus = calculate_match_importance_bonus(context.match_importance)

    return r_bonus + a_bonus + i_bonus


def infer_rivalry_level(
    home_team: Any,
    away_team: Any,
    rivalry_map: dict[tuple[str, str], RivalryLevel] | None = None,
) -> RivalryLevel:
    """Infere puramente o nível de rivalidade entre dois clubes."""

    home_name = getattr(home_team, "name", str(home_team))
    away_name = getattr(away_team, "name", str(away_team))

    # 1. Mapa explícito no dataset
    if rivalry_map:
        if (home_name, away_name) in rivalry_map:
            return rivalry_map[(home_name, away_name)]
        if (away_name, home_name) in rivalry_map:
            return rivalry_map[(away_name, home_name)]

    home_city = getattr(home_team, "city", "").strip()
    away_city = getattr(away_team, "city", "").strip()

    home_state = getattr(home_team, "state", "").strip()
    away_state = getattr(away_team, "state", "").strip()

    # 2. Clássico municipal
    if home_city and away_city and home_city.lower() == away_city.lower():
        return RivalryLevel.CITY_CLASSIC

    # 3. Clássico estadual
    if home_state and away_state and home_state.lower() == away_state.lower():
        return RivalryLevel.STATE_CLASSIC

    return RivalryLevel.NONE


def infer_opponent_appeal(away_team: Any, series: str = "D") -> OpponentAppeal:
    """Infere o nível de apelo do adversário visitante."""

    if hasattr(away_team, "opponent_appeal") and getattr(away_team, "opponent_appeal") is not None:
        raw = getattr(away_team, "opponent_appeal")
        for app in OpponentAppeal:
            if app.value == str(raw).lower():
                return app

    series_upper = series.upper()
    if series_upper == "A":
        return OpponentAppeal.NATIONAL
    elif series_upper == "B":
        return OpponentAppeal.HIGH
    elif series_upper == "C":
        return OpponentAppeal.MEDIUM
    else:
        return OpponentAppeal.LOW


def infer_match_importance(
    competition_type: str = "league",
    is_final: bool = False,
    is_semifinal: bool = False,
    is_knockout: bool = False,
    round_number: int | None = None,
    total_rounds: int | None = None,
) -> MatchImportance:
    """Infere a importância da partida na competição."""

    if is_final:
        return MatchImportance.FINAL
    if is_semifinal:
        return MatchImportance.SEMIFINAL
    if is_knockout:
        return MatchImportance.KNOCKOUT

    if round_number and total_rounds and round_number >= total_rounds - 2:
        return MatchImportance.TITLE_DECIDER

    return MatchImportance.NORMAL
