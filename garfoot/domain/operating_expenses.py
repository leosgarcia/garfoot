"""Modelo e regras puras de despesas operacionais recorrentes dos clubes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from garfoot.domain.club_finance import (
    ClubFinancialProfile,
    infer_financial_profile,
)


class OperatingExpenseType(StrEnum):
    """Categorias de despesas operacionais recorrentes do clube."""

    STADIUM_MAINTENANCE = "stadium_maintenance"
    MATCHDAY_OPERATIONS = "matchday_operations"
    TRAVEL_LOGISTICS = "travel_logistics"
    COACHING_STAFF = "coaching_staff"
    ADMINISTRATIVE = "administrative"
    YOUTH_DEVELOPMENT = "youth_development"


OPERATING_BASE_VALUES: dict[str, dict[OperatingExpenseType, int]] = {
    "A": {
        OperatingExpenseType.STADIUM_MAINTENANCE: 120_000,
        OperatingExpenseType.MATCHDAY_OPERATIONS: 80_000,
        OperatingExpenseType.TRAVEL_LOGISTICS: 70_000,
        OperatingExpenseType.COACHING_STAFF: 150_000,
        OperatingExpenseType.ADMINISTRATIVE: 100_000,
        OperatingExpenseType.YOUTH_DEVELOPMENT: 80_000,
    },
    "B": {
        OperatingExpenseType.STADIUM_MAINTENANCE: 55_000,
        OperatingExpenseType.MATCHDAY_OPERATIONS: 35_000,
        OperatingExpenseType.TRAVEL_LOGISTICS: 35_000,
        OperatingExpenseType.COACHING_STAFF: 70_000,
        OperatingExpenseType.ADMINISTRATIVE: 45_000,
        OperatingExpenseType.YOUTH_DEVELOPMENT: 35_000,
    },
    "C": {
        OperatingExpenseType.STADIUM_MAINTENANCE: 25_000,
        OperatingExpenseType.MATCHDAY_OPERATIONS: 18_000,
        OperatingExpenseType.TRAVEL_LOGISTICS: 20_000,
        OperatingExpenseType.COACHING_STAFF: 35_000,
        OperatingExpenseType.ADMINISTRATIVE: 22_000,
        OperatingExpenseType.YOUTH_DEVELOPMENT: 18_000,
    },
    "D": {
        OperatingExpenseType.STADIUM_MAINTENANCE: 12_000,
        OperatingExpenseType.MATCHDAY_OPERATIONS: 8_000,
        OperatingExpenseType.TRAVEL_LOGISTICS: 10_000,
        OperatingExpenseType.COACHING_STAFF: 15_000,
        OperatingExpenseType.ADMINISTRATIVE: 10_000,
        OperatingExpenseType.YOUTH_DEVELOPMENT: 7_000,
    },
}

OPERATING_PROFILE_MULTIPLIER: dict[ClubFinancialProfile, float] = {
    ClubFinancialProfile.LARGE: 1.35,
    ClubFinancialProfile.MEDIUM: 1.00,
    ClubFinancialProfile.SMALL: 0.75,
    ClubFinancialProfile.DEBT_PRESSURED: 0.65,
    ClubFinancialProfile.DEVELOPING: 0.55,
}

EXPENSE_DESCRIPTIONS: dict[OperatingExpenseType, str] = {
    OperatingExpenseType.STADIUM_MAINTENANCE: "Manutenção do Estádio e Gramado",
    OperatingExpenseType.MATCHDAY_OPERATIONS: "Operação e Segurança de Dia de Jogo",
    OperatingExpenseType.TRAVEL_LOGISTICS: "Logística de Viagens e Concentrações",
    OperatingExpenseType.COACHING_STAFF: "Comissão Técnica e Departamento Médico",
    OperatingExpenseType.ADMINISTRATIVE: "Despesas Administrativas e Operacionais",
    OperatingExpenseType.YOUTH_DEVELOPMENT: "Estrutura e Categorias de Base",
}


@dataclass(frozen=True, slots=True)
class OperatingExpense:
    """Representa um custo operacional recorrente debitado a cada rodada."""

    expense_type: OperatingExpenseType
    description: str
    amount_per_round: int
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serialização para JSON."""

        data = asdict(self)
        data["expense_type"] = self.expense_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OperatingExpense:
        """Desserialização a partir de dados salvos."""

        payload = dict(data)
        payload["expense_type"] = OperatingExpenseType(str(payload["expense_type"]))
        return cls(**payload)


@dataclass(slots=True)
class ClubOperatingExpenseProfile:
    """Perfil de custos e despesas operacionais recorrentes do clube."""

    expenses: list[OperatingExpense] = field(default_factory=list)

    @property
    def total_per_round(self) -> int:
        """Soma total das despesas operacionais ativas por rodada."""

        return sum(e.amount_per_round for e in self.expenses if e.is_active)

    @property
    def annual_estimate(self) -> int:
        """Estimativa de custo operacional total em uma temporada de 38 rodadas."""

        return self.total_per_round * 38

    def active_expenses(self) -> list[OperatingExpense]:
        """Retorna apenas as despesas atualmente ativas."""

        return [e for e in self.expenses if e.is_active]

    def to_dict(self) -> dict[str, Any]:
        """Serialização do perfil de despesas para JSON."""

        return {"expenses": [e.to_dict() for e in self.expenses]}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ClubOperatingExpenseProfile:
        """Desserialização retrocompatível de perfil salvos."""

        if not data or not isinstance(data, dict):
            return cls()
        expenses = [
            OperatingExpense.from_dict(e)
            for e in data.get("expenses", [])
            if isinstance(e, dict)
        ]
        return cls(expenses=expenses)


def calculate_operating_expense_amount(
    expense_type: OperatingExpenseType,
    series: str = "D",
    profile: ClubFinancialProfile = ClubFinancialProfile.MEDIUM,
    stadium_capacity: int = 0,
    economic_context: Any | None = None,
) -> int:
    """Calcula o valor unitário por rodada de uma despesa operacional."""

    series_upper = series.upper()
    base = OPERATING_BASE_VALUES.get(series_upper, OPERATING_BASE_VALUES["D"]).get(expense_type, 10_000)
    prof_mult = OPERATING_PROFILE_MULTIPLIER.get(profile, 1.00)

    # Aplica fator de estádio em manutenção e dia de jogo
    stadium_factor = 1.0
    if expense_type in (OperatingExpenseType.STADIUM_MAINTENANCE, OperatingExpenseType.MATCHDAY_OPERATIONS):
        if stadium_capacity > 0:
            stadium_factor = 1.0 + min(stadium_capacity / 100_000.0, 0.40)

    econ_index = (
        economic_context.economic_index
        if economic_context and hasattr(economic_context, "economic_index")
        else 1.0
    )

    final_val = round(base * prof_mult * stadium_factor * econ_index)
    return max(1_000, final_val)


def generate_default_operating_expenses_for_team(
    team: Any,
    series: str = "D",
    profile: ClubFinancialProfile | None = None,
    economic_context: Any | None = None,
) -> ClubOperatingExpenseProfile:
    """Gera puramente a lista padrão de despesas operacionais do clube."""

    prof = profile or infer_financial_profile(team, series=series)
    stadium_cap = team.stadium.capacity if hasattr(team, "stadium") and team.stadium is not None else 0

    expenses: list[OperatingExpense] = []
    for exp_type in OperatingExpenseType:
        amt = calculate_operating_expense_amount(
            expense_type=exp_type,
            series=series,
            profile=prof,
            stadium_capacity=stadium_cap,
            economic_context=economic_context,
        )
        expenses.append(
            OperatingExpense(
                expense_type=exp_type,
                description=EXPENSE_DESCRIPTIONS.get(exp_type, exp_type.value),
                amount_per_round=amt,
                is_active=True,
            )
        )

    return ClubOperatingExpenseProfile(expenses=expenses)


def process_round_operating_expenses(
    team: Any,
    expense_profile: ClubOperatingExpenseProfile,
) -> tuple[Any, int]:
    """Deduz as despesas operacionais da rodada do orçamento do clube."""

    total_cost = expense_profile.total_per_round
    if hasattr(team, "budget"):
        team.budget -= total_cost

    if hasattr(team, "operating_expenses"):
        team.operating_expenses = expense_profile

    return team, total_cost


def process_round_operating_expenses_idempotent(
    team: Any,
    expense_profile: ClubOperatingExpenseProfile,
    season_year: int,
    round_number: int,
    ledger: Any,
) -> tuple[Any, int]:
    """Deduz as despesas operacionais da rodada de forma estritamente idempotente via ledger."""

    team_name = getattr(team, "name", "Club")
    key = f"operating-expenses:{season_year}:{round_number}:{team_name}"
    if ledger is not None and hasattr(ledger, "check_and_mark"):
        if not ledger.check_and_mark(key):
            return team, 0

    return process_round_operating_expenses(team=team, expense_profile=expense_profile)


def calculate_financial_burn_rate(
    team: Any,
    expense_profile: ClubOperatingExpenseProfile,
    total_rounds: int = 38,
) -> dict[str, int]:
    """Calcula a taxa de saída financeira do clube (burn rate) por rodada."""

    op_per_round = expense_profile.total_per_round

    from garfoot.domain.squad_rules import calculate_wage_bill
    annual_wages = calculate_wage_bill(team) if hasattr(team, "players") else 0
    wage_per_round = round(annual_wages / total_rounds) if total_rounds > 0 else 0

    return {
        "operating_per_round": op_per_round,
        "wage_per_round": wage_per_round,
        "total_burn_per_round": op_per_round + wage_per_round,
    }
