"""Testes unitários para despesas operacionais e custos recorrentes dos clubes."""

import pytest

from garfoot.domain.club_finance import ClubFinancialProfile
from garfoot.domain.economic_context import EconomicContext
from garfoot.domain.operating_expenses import (
    ClubOperatingExpenseProfile,
    OperatingExpense,
    OperatingExpenseType,
    calculate_financial_burn_rate,
    calculate_operating_expense_amount,
    generate_default_operating_expenses_for_team,
    process_round_operating_expenses,
)
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team


def test_operating_expense_model_and_profile_serialization():
    exp1 = OperatingExpense(
        expense_type=OperatingExpenseType.STADIUM_MAINTENANCE,
        description="Manutenção de Gramado",
        amount_per_round=50_000,
        is_active=True,
    )
    profile = ClubOperatingExpenseProfile(expenses=[exp1])

    assert profile.total_per_round == 50_000
    assert profile.annual_estimate == 50_000 * 38

    data = profile.to_dict()
    restored = ClubOperatingExpenseProfile.from_dict(data)

    assert len(restored.expenses) == 1
    assert restored.expenses[0].expense_type == OperatingExpenseType.STADIUM_MAINTENANCE
    assert restored.expenses[0].amount_per_round == 50_000


def test_calculate_operating_expense_amounts_by_series_and_profile():
    # 1. Série A x Série D
    amt_a = calculate_operating_expense_amount(OperatingExpenseType.STADIUM_MAINTENANCE, series="A", profile=ClubFinancialProfile.MEDIUM)
    amt_d = calculate_operating_expense_amount(OperatingExpenseType.STADIUM_MAINTENANCE, series="D", profile=ClubFinancialProfile.MEDIUM)
    assert amt_a == 120_000
    assert amt_d == 12_000

    # 2. Perfil LARGE (1.35x) vs SMALL (0.75x)
    amt_large = calculate_operating_expense_amount(OperatingExpenseType.ADMINISTRATIVE, series="A", profile=ClubFinancialProfile.LARGE)
    amt_small = calculate_operating_expense_amount(OperatingExpenseType.ADMINISTRATIVE, series="A", profile=ClubFinancialProfile.SMALL)
    assert amt_large == round(100_000 * 1.35)
    assert amt_small == round(100_000 * 0.75)


def test_stadium_capacity_impact_capped_at_40_percent():
    # Estádio de 50.000 (50,000 / 100,000 = +50% -> limitado a +40%)
    amt_50k = calculate_operating_expense_amount(
        OperatingExpenseType.STADIUM_MAINTENANCE,
        series="D",
        profile=ClubFinancialProfile.MEDIUM,
        stadium_capacity=50_000,
    )
    assert amt_50k == round(12_000 * 1.40)

    # Estádio gigante de 200.000 deve continuar travado em no máximo +40%
    amt_200k = calculate_operating_expense_amount(
        OperatingExpenseType.STADIUM_MAINTENANCE,
        series="D",
        profile=ClubFinancialProfile.MEDIUM,
        stadium_capacity=200_000,
    )
    assert amt_200k == round(12_000 * 1.40)


def test_economic_index_applies_to_operating_expenses():
    econ = EconomicContext(economic_index=1.10)
    amt = calculate_operating_expense_amount(OperatingExpenseType.TRAVEL_LOGISTICS, series="A", economic_context=econ)
    assert amt == round(70_000 * 1.10)


def test_generate_default_operating_expenses_for_team():
    stadium = Stadium(name="Arena", city="SP", capacity=40_000)
    team = Team(name="São Paulo", city="SP", budget=10_000_000, stadium=stadium)

    profile = generate_default_operating_expenses_for_team(team, series="A")
    assert len(profile.expenses) == 6
    assert profile.total_per_round > 0


def test_process_round_operating_expenses_and_negative_budget_safety():
    team = Team(name="Time Dev", city="Cidade", budget=50_000)
    exp = OperatingExpense(expense_type=OperatingExpenseType.ADMINISTRATIVE, description="Admin", amount_per_round=60_000)
    profile = ClubOperatingExpenseProfile(expenses=[exp])

    updated_team, cost = process_round_operating_expenses(team, profile)
    assert cost == 60_000
    # Saldo pode ficar negativo de forma segura sem crash
    assert updated_team.budget == -10_000


def test_calculate_financial_burn_rate():
    team = Team(name="Clube Burn", city="Cidade", budget=1_000_000)
    exp = OperatingExpense(expense_type=OperatingExpenseType.TRAVEL_LOGISTICS, description="Log", amount_per_round=40_000)
    profile = ClubOperatingExpenseProfile(expenses=[exp])

    burn = calculate_financial_burn_rate(team, profile, total_rounds=38)
    assert burn["operating_per_round"] == 40_000
    assert burn["total_burn_per_round"] >= 40_000


def test_team_serialization_with_operating_expenses():
    team = Team(name="Vasco", city="Rio", budget=5_000_000)
    team.operating_expenses = generate_default_operating_expenses_for_team(team, series="A")

    data = team.to_dict()
    assert "operating_expenses" in data
    assert len(data["operating_expenses"]["expenses"]) == 6

    restored = Team.from_dict(data)
    assert len(restored.operating_expenses.expenses) == 6
    assert restored.operating_expenses.total_per_round > 0

    # Save antigo sem a chave operating_expenses
    del data["operating_expenses"]
    restored_legacy = Team.from_dict(data)
    assert restored_legacy.operating_expenses is not None
    assert len(restored_legacy.operating_expenses.expenses) == 0
