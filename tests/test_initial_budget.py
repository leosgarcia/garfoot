"""Testes unitários para as regras de orçamento inicial e perfil financeiro dos clubes."""

import pytest

from garfoot.domain.club_finance import (
    ClubFinancialProfile,
    calculate_initial_budget,
    infer_financial_profile,
    initialize_team_budget,
)
from garfoot.domain.player import Player
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team
from garfoot.ui.data import load_teams


def test_initial_budget_base_values_by_tier():
    assert calculate_initial_budget(series="A", profile=ClubFinancialProfile.MEDIUM) == 12_000_000
    assert calculate_initial_budget(series="B", profile=ClubFinancialProfile.MEDIUM) == 5_000_000
    assert calculate_initial_budget(series="C", profile=ClubFinancialProfile.MEDIUM) == 2_000_000
    assert calculate_initial_budget(series="D", profile=ClubFinancialProfile.MEDIUM) == 800_000


def test_initial_budget_profile_multipliers():
    base = 12_000_000  # Série A

    assert calculate_initial_budget(series="A", profile=ClubFinancialProfile.LARGE) == round(base * 1.50)
    assert calculate_initial_budget(series="A", profile=ClubFinancialProfile.SMALL) == round(base * 0.70)
    assert calculate_initial_budget(series="A", profile=ClubFinancialProfile.DEBT_PRESSURED) == round(base * 0.45)
    assert calculate_initial_budget(series="A", profile=ClubFinancialProfile.DEVELOPING) == round(base * 0.85)


test_economic_index_impact = lambda: (
    assert_budget(calculate_initial_budget(series="A", profile=ClubFinancialProfile.MEDIUM, economic_index=1.10), round(12_000_000 * 1.10))
)


def assert_budget(actual: int, expected: int):
    assert actual == expected


def test_initial_budget_stadium_factor_capped():
    # Estádio de 50k lugares traz bônus de 50,000 / 100,000 = +50% -> limitado a +25%
    budget_50k = calculate_initial_budget(series="D", profile=ClubFinancialProfile.MEDIUM, stadium_capacity=50_000)
    assert budget_50k == round(800_000 * 1.25)

    # Estádio de 200k lugares (gigante) deve continuar travado no teto máximo de +25%
    budget_200k = calculate_initial_budget(series="D", profile=ClubFinancialProfile.MEDIUM, stadium_capacity=200_000)
    assert budget_200k == round(800_000 * 1.25)


def test_infer_financial_profile_explicit_dataset_field_and_fallbacks():
    # 1. Campo explícito no dataset
    dict_explicit = {"financial_profile": "debt_pressed"}
    assert infer_financial_profile(dict_explicit, series="A") == ClubFinancialProfile.DEBT_PRESSURED

    # 2. Regra por Série e estádio
    dict_serie_a = {"stadium": {"capacity": 60_000}}
    assert infer_financial_profile(dict_serie_a, series="A") == ClubFinancialProfile.LARGE

    dict_serie_d = {"stadium": {"capacity": 10_000}}
    assert infer_financial_profile(dict_serie_d, series="D") == ClubFinancialProfile.DEVELOPING


def test_initialize_team_budget_preserves_existing_saved_budget():
    # Time já salvo com orçamento de 15.000.000 (não deve ser sobrescrito)
    saved_team = Team(name="Salvo", city="Cidade", budget=15_000_000)

    updated = initialize_team_budget(saved_team, series="D", force_recalculate=False)
    assert updated.budget == 15_000_000  # Mantido intacto


def test_team_financial_profile_serialization():
    team = Team(name="Flamengo", city="Rio", budget=18_000_000, financial_profile=ClubFinancialProfile.LARGE)

    data = team.to_dict()
    assert data["financial_profile"] == "large"

    restored = Team.from_dict(data)
    assert restored.financial_profile == ClubFinancialProfile.LARGE

    # Save antigo sem financial_profile
    del data["financial_profile"]
    restored_legacy = Team.from_dict(data)
    assert restored_legacy.financial_profile is None


def test_data_load_teams_initial_budgets():
    teams = load_teams()
    assert len(teams) >= 60

    for t in teams:
        assert t.budget > 0

    flamengo = next(t for t in teams if "Flamengo" in t.name)
    santa_cruz = next(t for t in teams if "Santa Cruz" in t.name or "Barra" in t.name)

    # Série A (Flamengo) deve ter orçamento maior que o time da Série D
    assert flamengo.budget > santa_cruz.budget
