"""Testes unitários para o módulo financeiro (upgrade de estádio e empréstimo bancário)."""

import pytest

from garfoot.domain.finance import (
    BankLoan,
    StadiumUpgradeProject,
    calculate_max_loan_amount,
    calculate_upgrade_cost,
    can_upgrade_stadium,
    process_round_finances,
    start_stadium_upgrade,
    take_bank_loan,
)
from garfoot.domain.player import Player
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team


def _make_test_team(budget: int = 1_000_000, capacity: int = 10_000) -> Team:
    stadium = Stadium(name="Estádio Teste", city="Cidade Teste", capacity=capacity)
    players = [
        Player(name=f"Jogador {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=50, defense=50, fitness=80, morale=80)
        for i in range(11)
    ]
    return Team(name="Time Teste", city="Cidade Teste", budget=budget, stadium=stadium, players=players)


def test_stadium_upgrade_cost_calculation():
    # Custo de 2.500 assentos para estádio de 10.000 lugares
    c1 = calculate_upgrade_cost(current_capacity=10_000, additional_seats=2_500)
    # Custo de 2.500 assentos para estádio de 50.000 lugares (deve ser mais caro)
    c2 = calculate_upgrade_cost(current_capacity=50_000, additional_seats=2_500)

    assert c1 == 825_000
    assert c2 == 1_125_000
    assert c2 > c1


def test_stadium_upgrade_eligibility_and_grandfathering():
    # Estádio de 10k na Série D (abaixo do teto de 25k) -> pode evoluir
    ok, _ = can_upgrade_stadium(10_000, "D")
    assert ok is True

    # Estádio de 25k na Série D (atingiu teto de 25k) -> não pode evoluir
    ok_max, _ = can_upgrade_stadium(25_000, "D")
    assert ok_max is False

    # Direitos Adquiridos: Estádio de 35k na Série D (original do dataset) -> preserva capacidade, mas bloqueia obra adicional
    ok_grandfathered, _ = can_upgrade_stadium(35_000, "D")
    assert ok_grandfathered is False


def test_start_stadium_upgrade_success_and_budget_deduction():
    team = _make_test_team(budget=2_000_000, capacity=10_000)
    updated_team, project = start_stadium_upgrade(team, series="D", additional_seats=2_500)

    assert project.rounds_remaining == 6
    assert project.additional_seats == 2_500
    assert updated_team.budget == 2_000_000 - 825_000


def test_bank_loan_limit_and_creation():
    team = _make_test_team(budget=500_000, capacity=10_000)
    max_loan = calculate_max_loan_amount(team, series="D")
    assert max_loan > 500_000

    updated_team, loan = take_bank_loan(team, series="D", amount_requested=500_000)
    assert updated_team.budget == 1_000_000
    assert loan.original_amount == 500_000
    assert loan.total_amount_with_interest == 575_000
    assert loan.installment_amount == 57_500
    assert loan.remaining_installments == 10


def test_process_round_finances_completion_and_payment():
    team = _make_test_team(budget=1_000_000, capacity=10_000)
    project = StadiumUpgradeProject(additional_seats=2_500, cost=825_000, rounds_remaining=1)
    loan = BankLoan(
        original_amount=500_000,
        total_amount_with_interest=575_000,
        installment_amount=57_500,
        total_installments=10,
        remaining_installments=10,
    )

    updated_team, completed_proj, updated_loan, msgs = process_round_finances(team, project, loan)

    # Obra finalizada -> capacidade subiu para 12.500
    assert updated_team.stadium.capacity == 12_500
    assert completed_proj.is_completed is True

    # Parcela de 57.500 paga -> budget debitado
    assert updated_team.budget == 1_000_000 - 57_500
    assert updated_loan.remaining_installments == 9
    assert len(msgs) == 2
