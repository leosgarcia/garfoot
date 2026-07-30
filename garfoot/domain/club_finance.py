"""Regras puras de orçamento inicial e perfil financeiro dos clubes."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

INITIAL_BUDGET_BY_TIER: dict[str, int] = {
    "A": 12_000_000,
    "B": 5_000_000,
    "C": 2_000_000,
    "D": 800_000,
}


class ClubFinancialProfile(StrEnum):
    """Perfis financeiros de porte e saúde de clubes no Garfoot."""

    LARGE = "large"
    MEDIUM = "medium"
    SMALL = "small"
    DEBT_PRESSURED = "debt_pressed"
    DEVELOPING = "developing"


FINANCIAL_PROFILE_MULTIPLIER: dict[ClubFinancialProfile, float] = {
    ClubFinancialProfile.LARGE: 1.50,
    ClubFinancialProfile.MEDIUM: 1.00,
    ClubFinancialProfile.SMALL: 0.70,
    ClubFinancialProfile.DEBT_PRESSURED: 0.45,
    ClubFinancialProfile.DEVELOPING: 0.85,
}


def infer_financial_profile(
    club_data_or_team: dict[str, Any] | Any,
    series: str = "D",
) -> ClubFinancialProfile:
    """Infere puramente o perfil financeiro do clube a partir do seu dataset ou modelo."""

    series_upper = series.upper()

    # 1. Se contiver perfil explícito no dataset
    if isinstance(club_data_or_team, dict) and "financial_profile" in club_data_or_team:
        raw = str(club_data_or_team["financial_profile"]).lower()
        for p in ClubFinancialProfile:
            if p.value == raw:
                return p

    if hasattr(club_data_or_team, "financial_profile") and getattr(club_data_or_team, "financial_profile") is not None:
        return getattr(club_data_or_team, "financial_profile")

    # 2. Regras por Série e facilidades de estádio / ranking
    stadium_cap = 0
    if isinstance(club_data_or_team, dict):
        stadium_dict = club_data_or_team.get("stadium")
        if isinstance(stadium_dict, dict):
            stadium_cap = int(stadium_dict.get("capacity", 0))
    elif hasattr(club_data_or_team, "stadium") and getattr(club_data_or_team, "stadium") is not None:
        stadium_cap = getattr(club_data_or_team, "stadium").capacity

    if series_upper == "A":
        return ClubFinancialProfile.LARGE if stadium_cap >= 50_000 else ClubFinancialProfile.MEDIUM
    elif series_upper == "B":
        return ClubFinancialProfile.MEDIUM if stadium_cap >= 35_000 else ClubFinancialProfile.SMALL
    elif series_upper == "C":
        return ClubFinancialProfile.SMALL if stadium_cap >= 20_000 else ClubFinancialProfile.DEVELOPING
    else:  # Série D
        return ClubFinancialProfile.SMALL if stadium_cap >= 15_000 else ClubFinancialProfile.DEVELOPING


def calculate_initial_budget(
    series: str,
    profile: ClubFinancialProfile = ClubFinancialProfile.MEDIUM,
    economic_index: float = 1.0,
    stadium_capacity: int = 0,
) -> int:
    """Calcula o orçamento inicial padronizado para um clube."""

    base = INITIAL_BUDGET_BY_TIER.get(series.upper(), 800_000)
    mult = FINANCIAL_PROFILE_MULTIPLIER.get(profile, 1.00)

    # Fator de estádio limitado a no máximo +25%
    stadium_factor = 1.0 + min(stadium_capacity / 100_000.0, 0.25) if stadium_capacity > 0 else 1.0

    final_budget = round(base * mult * stadium_factor * economic_index)
    return max(200_000, final_budget)


def initialize_team_budget(
    team: Any,
    series: str = "D",
    profile: ClubFinancialProfile | None = None,
    economic_index: float = 1.0,
    force_recalculate: bool = False,
) -> Any:
    """Inicializa o orçamento do clube de forma idetempotente. Preserva orçamentos salvos."""

    if getattr(team, "budget", 0) > 0 and not force_recalculate:
        return team

    prof = profile or infer_financial_profile(team, series=series)
    stadium_cap = team.stadium.capacity if getattr(team, "stadium", None) is not None else 0

    new_budget = calculate_initial_budget(
        series=series,
        profile=prof,
        economic_index=economic_index,
        stadium_capacity=stadium_cap,
    )

    team.budget = new_budget
    if hasattr(team, "financial_profile"):
        team.financial_profile = prof

    return team
