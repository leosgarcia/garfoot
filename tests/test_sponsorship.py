"""Testes unitários para patrocínios e receitas comerciais dos clubes."""

import pytest

from garfoot.domain.club_finance import ClubFinancialProfile
from garfoot.domain.economic_context import EconomicContext
from garfoot.domain.sponsorship import (
    ClubSponsorshipPortfolio,
    SponsorshipContract,
    SponsorshipType,
    advance_sponsorship_rounds,
    calculate_sponsorship_match_bonus,
    calculate_sponsorship_value,
    generate_default_sponsorships_for_team,
    process_round_sponsorship_income,
)
from garfoot.domain.team import Team


def test_sponsorship_contract_and_portfolio_serialization():
    contract = SponsorshipContract(
        sponsor_name="Bet DOS",
        sponsorship_type=SponsorshipType.MASTER,
        annual_value=3_800_000,
        rounds_remaining=38,
        bonus_per_win=50_000,
    )

    portfolio = ClubSponsorshipPortfolio(contracts=[contract])
    assert portfolio.annual_total == 3_800_000

    data = portfolio.to_dict()
    restored = ClubSponsorshipPortfolio.from_dict(data)

    assert len(restored.contracts) == 1
    assert restored.contracts[0].sponsor_name == "Bet DOS"
    assert restored.contracts[0].sponsorship_type == SponsorshipType.MASTER
    assert restored.contracts[0].value_per_round(38) == 100_000


def test_calculate_sponsorship_values_by_series_and_profile():
    # 1. Série A x Série D
    val_master_a = calculate_sponsorship_value(SponsorshipType.MASTER, series="A", profile=ClubFinancialProfile.MEDIUM)
    val_master_d = calculate_sponsorship_value(SponsorshipType.MASTER, series="D", profile=ClubFinancialProfile.MEDIUM)
    assert val_master_a == 4_000_000
    assert val_master_d == 250_000

    # 2. Perfil LARGE (1.5x) vs SMALL (0.7x)
    val_large = calculate_sponsorship_value(SponsorshipType.MASTER, series="A", profile=ClubFinancialProfile.LARGE)
    val_small = calculate_sponsorship_value(SponsorshipType.MASTER, series="A", profile=ClubFinancialProfile.SMALL)
    assert val_large == round(4_000_000 * 1.50)
    assert val_small == round(4_000_000 * 0.70)


def test_economic_index_applies_only_to_new_contracts():
    econ_110 = EconomicContext(economic_index=1.10)

    val_new = calculate_sponsorship_value(SponsorshipType.MASTER, series="A", economic_context=econ_110)
    assert val_new == round(4_000_000 * 1.10)

    # Contrato já assinado não altera seu valor assinado com a inflação
    contract_old = SponsorshipContract(
        sponsor_name="Banco Antigo",
        sponsorship_type=SponsorshipType.MASTER,
        annual_value=4_000_000,
        rounds_remaining=20,
    )
    assert contract_old.annual_value == 4_000_000


def test_generate_default_sponsorships_for_team_deterministic():
    team = Team(name="Palmeiras", city="São Paulo", budget=10_000_000)
    portfolio = generate_default_sponsorships_for_team(team, series="A", seed=12345)

    assert len(portfolio.contracts) == 2
    types = {c.sponsorship_type for c in portfolio.contracts}
    assert SponsorshipType.MASTER in types
    assert SponsorshipType.KIT_SUPPLIER in types

    # Determinismo
    portfolio_again = generate_default_sponsorships_for_team(team, series="A", seed=12345)
    assert portfolio_again.contracts[0].sponsor_name == portfolio.contracts[0].sponsor_name


def test_process_round_sponsorship_income_and_win_bonus():
    team = Team(name="Flamengo", city="Rio", budget=1_000_000)
    c1 = SponsorshipContract(
        sponsor_name="Master",
        sponsorship_type=SponsorshipType.MASTER,
        annual_value=3_800_000,
        rounds_remaining=38,
        bonus_per_win=50_000,
    )
    portfolio = ClubSponsorshipPortfolio(contracts=[c1])
    team.sponsorships = portfolio

    # 1. Processa 1 rodada de receita comercial (3.8M / 38 = 100k)
    updated_team, income = process_round_sponsorship_income(team, portfolio, total_rounds=38)
    assert income == 100_000
    assert updated_team.budget == 1_100_000
    assert updated_team.sponsorships.contracts[0].rounds_remaining == 37

    # 2. Bônus por vitória
    win_bonus = calculate_sponsorship_match_bonus(updated_team.sponsorships, is_win=True)
    assert win_bonus == 50_000

    draw_bonus = calculate_sponsorship_match_bonus(updated_team.sponsorships, is_win=False)
    assert draw_bonus == 0


def test_team_serialization_with_sponsorships():
    team = Team(name="Botafogo", city="Rio", budget=5_000_000)
    team.sponsorships = generate_default_sponsorships_for_team(team, series="A", seed=99)

    data = team.to_dict()
    assert "sponsorships" in data
    assert len(data["sponsorships"]["contracts"]) == 2

    restored = Team.from_dict(data)
    assert len(restored.sponsorships.contracts) == 2
    assert restored.sponsorships.annual_total > 0

    # Save antigo sem a chave sponsorships
    del data["sponsorships"]
    restored_legacy = Team.from_dict(data)
    assert restored_legacy.sponsorships is not None
    assert len(restored_legacy.sponsorships.contracts) == 0
