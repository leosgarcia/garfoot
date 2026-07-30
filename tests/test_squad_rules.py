"""Testes unitários para as regras de limite de elenco, massa salarial e saúde financeira."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.squad_rules import (
    SquadLimitConfig,
    WageHealth,
    can_add_player_to_squad,
    can_afford_new_salary,
    calculate_estimated_annual_revenue,
    calculate_wage_bill,
    calculate_wage_commitment,
    classify_wage_health,
    count_players_by_position,
    validate_squad_limits,
)
from garfoot.domain.team import Team
from garfoot.domain.transfer_market import TransferListing, execute_player_purchase


def _make_team_with_n_players(name: str, n: int, budget: int = 5_000_000, salary_per_player: int = 50_000) -> Team:
    players = [
        Player(
            name=f"{name} Jogador {i:02d}",
            age=22,
            position=PlayerPosition.GOALKEEPER if i < 2 else (PlayerPosition.DEFENDER if i < 7 else PlayerPosition.MIDFIELDER),
            attack=60,
            defense=60,
            fitness=80,
            morale=80,
            salary=salary_per_player,
        )
        for i in range(n)
    ]
    t = Team(name=name, city="Cidade", budget=budget, players=players)
    t.starting_player_names = [p.name for p in players[:11]]
    return t


def test_count_players_by_position_and_validation():
    team = _make_team_with_n_players("Meu Time", n=20)
    counts = count_players_by_position(team)

    assert counts[PlayerPosition.GOALKEEPER] == 2
    assert counts[PlayerPosition.DEFENDER] == 5
    assert counts[PlayerPosition.MIDFIELDER] == 13

    diag = validate_squad_limits(team)
    assert diag.total_players == 20
    assert diag.is_over_limit is False
    assert diag.is_below_minimum is False


def test_squad_limits_over_max_and_below_min():
    small_team = _make_team_with_n_players("Pequeno", n=15)
    diag_small = validate_squad_limits(small_team)
    assert diag_small.is_below_minimum is True
    assert any("abaixo do mínimo operacional" in w for w in diag_small.warnings)

    huge_team = _make_team_with_n_players("Gigante", n=31)
    diag_huge = validate_squad_limits(huge_team)
    assert diag_huge.is_over_limit is True
    assert any("excede o limite máximo" in w for w in diag_huge.warnings)


def test_can_add_player_to_squad():
    team_29 = _make_team_with_n_players("Com29", n=29)
    can_29, _ = can_add_player_to_squad(team_29)
    assert can_29 is True

    team_30 = _make_team_with_n_players("Com30", n=30)
    can_30, reason_30 = can_add_player_to_squad(team_30)
    assert can_30 is False
    assert "limite máximo de 30 jogadores" in reason_30


def test_calculate_wage_bill_and_commitment_classification():
    team = _make_team_with_n_players("Financeiro", n=20, salary_per_player=100_000)
    bill = calculate_wage_bill(team)
    assert bill == 20 * 100_000  # 2_000_000

    rev = 5_000_000
    commit = calculate_wage_commitment(team, estimated_annual_revenue=rev)
    assert commit == 2_000_000 / 5_000_000  # 0.40 (40%)

    assert classify_wage_health(0.40) == WageHealth.HEALTHY
    assert classify_wage_health(0.60) == WageHealth.ATTENTION
    assert classify_wage_health(0.80) == WageHealth.PRESSURED
    assert classify_wage_health(0.95) == WageHealth.CRITICAL


def test_market_purchase_blocked_when_squad_full_or_wage_critical():
    buyer_full = _make_team_with_n_players("Comprador Cheio", n=30, budget=10_000_000)
    seller = _make_team_with_n_players("Vendedor", n=20, budget=1_000_000)

    target_player = seller.players[15]
    listing = TransferListing(player=target_player, seller_team_name=seller.name, asking_price=500_000)

    # 1. Tentar comprar com elenco cheio (30) deve FALHAR
    with pytest.raises(ValueError, match="limite máximo de 30 jogadores"):
        execute_player_purchase(buyer_full, seller, listing)

    # 2. Tentar comprar com folha em estado CRITICAL deve FALHAR
    buyer_critical = _make_team_with_n_players("Comprador Crítico", n=20, budget=10_000_000, salary_per_player=500_000)
    # Folha de 20 * 500k = 10M em receita pequena
    with pytest.raises(ValueError, match="CRÍTICO"):
        execute_player_purchase(buyer_critical, seller, listing)
