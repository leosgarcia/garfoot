"""Regras puras de limite de elenco, massa salarial e saúde financeira do clube."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.team import Team

# Receitas anuais base por Série no modo Brasil para cálculo de folha
SERIES_BASE_REVENUE: dict[str, int] = {
    "A": 25_000_000,
    "B": 10_000_000,
    "C": 4_000_000,
    "D": 1_500_000,
}


class WageHealth(StrEnum):
    """Classificação da saúde da folha salarial em relação às receitas do clube."""

    HEALTHY = "healthy"
    ATTENTION = "attention"
    PRESSURED = "pressured"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SquadLimitConfig:
    """Configuração dos limites operacionais e ideais do elenco."""

    min_total: int = 18
    ideal_min_total: int = 22
    ideal_max_total: int = 26
    max_total: int = 30
    min_by_position: dict[PlayerPosition, int] = field(
        default_factory=lambda: {
            PlayerPosition.GOALKEEPER: 2,
            PlayerPosition.DEFENDER: 6,
            PlayerPosition.MIDFIELDER: 6,
            PlayerPosition.FORWARD: 4,
        }
    )


@dataclass(frozen=True, slots=True)
class SquadValidationResult:
    """Resultado da validação do elenco com diagnósticos e alertas."""

    total_players: int
    is_over_limit: bool
    is_below_minimum: bool
    missing_by_position: dict[PlayerPosition, int]
    excess_by_position: dict[PlayerPosition, int]
    warnings: tuple[str, ...]


def count_players_by_position(team: Team) -> dict[PlayerPosition, int]:
    """Conta a quantidade de jogadores em cada posição do elenco."""

    counts = {pos: 0 for pos in PlayerPosition}
    for p in team.players:
        counts[p.position] = counts.get(p.position, 0) + 1
    return counts


def validate_squad_limits(
    team: Team, config: SquadLimitConfig | None = None
) -> SquadValidationResult:
    """Realiza o diagnóstico puro das regras de tamanho e composição do elenco."""

    cfg = config or SquadLimitConfig()
    total = len(team.players)
    counts = count_players_by_position(team)

    missing: dict[PlayerPosition, int] = {}
    excess: dict[PlayerPosition, int] = {}
    warnings_list: list[str] = []

    is_over = total > cfg.max_total
    is_below = total < cfg.min_total

    if is_over:
        warnings_list.append(f"Elenco excede o limite máximo de {cfg.max_total} jogadores (atual: {total}).")
    elif is_below:
        warnings_list.append(f"Elenco abaixo do mínimo operacional de {cfg.min_total} jogadores (atual: {total}).")

    min_pos = cfg.min_by_position or {}
    for pos, req_min in min_pos.items():
        curr = counts.get(pos, 0)
        if curr < req_min:
            missing[pos] = req_min - curr
            warnings_list.append(f"Faltam {req_min - curr} jogadores na posição {pos.value.upper()} (mínimo: {req_min}).")

    return SquadValidationResult(
        total_players=total,
        is_over_limit=is_over,
        is_below_minimum=is_below,
        missing_by_position=missing,
        excess_by_position=excess,
        warnings=tuple(warnings_list),
    )


def can_add_player_to_squad(
    team: Team, config: SquadLimitConfig | None = None
) -> tuple[bool, str]:
    """Verifica se o elenco do time pode receber mais um jogador sem violar o teto máximo."""

    cfg = config or SquadLimitConfig()
    if len(team.players) >= cfg.max_total:
        return False, f"O elenco do {team.name} já atingiu o limite máximo de {cfg.max_total} jogadores."
    return True, "Elegível."


def calculate_wage_bill(team: Team) -> int:
    """Calcula a soma salarial anual total do elenco."""

    if not team.players:
        return 0
    return sum(max(0, getattr(p, "salary", 0)) for p in team.players)


def calculate_estimated_annual_revenue(team: Team, series: str = "D") -> int:
    """Calcula a receita anual estimada do clube (mando de jogos + quota base da Série)."""

    base_rev = SERIES_BASE_REVENUE.get(series.upper(), 1_500_000)
    home_match_rev = team.estimate_home_income() * 19
    return base_rev + home_match_rev + max(0, team.budget // 2)


def calculate_wage_commitment(
    team: Team, estimated_annual_revenue: int | None = None
) -> float:
    """Calcula a proporção da folha salarial sobre as receitas do clube."""

    bill = calculate_wage_bill(team)
    rev = estimated_annual_revenue if estimated_annual_revenue is not None else calculate_estimated_annual_revenue(team)

    if rev <= 0:
        return 1.0 if bill > 0 else 0.0

    return bill / float(rev)


def classify_wage_health(commitment: float) -> WageHealth:
    """Classifica o comprometimento financeiro da folha salarial."""

    if commitment <= 0.50:
        return WageHealth.HEALTHY
    elif commitment <= 0.70:
        return WageHealth.ATTENTION
    elif commitment <= 0.90:
        return WageHealth.PRESSURED
    else:
        return WageHealth.CRITICAL


def can_afford_new_salary(
    team: Team, new_salary: int, estimated_annual_revenue: int | None = None
) -> tuple[bool, str]:
    """Valida se o clube pode arcar com um novo salário de contratação."""

    current_bill = calculate_wage_bill(team)
    future_bill = current_bill + new_salary
    rev = estimated_annual_revenue if estimated_annual_revenue is not None else calculate_estimated_annual_revenue(team)

    current_health = classify_wage_health(calculate_wage_commitment(team, rev))
    if current_health == WageHealth.CRITICAL and new_salary > 50_000:
        return False, "O clube está em estado financeiro CRÍTICO e não pode assumir novos salários altos."

    future_commitment = (future_bill / float(rev)) if rev > 0 else 1.0
    if future_commitment > 0.95:
        return False, "A nova contratação deixaria o comprometimento salarial do clube em nível insustentável (> 95%)."

    return True, "Elegível."
