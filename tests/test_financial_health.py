"""Testes unitários do sistema de saúde financeira, crise e fair play financeiro."""

from __future__ import annotations

import pytest

from garfoot.domain.financial_health import (
    CRISIS_TRANSFER_CAP,
    ClubFinancialState,
    FinancialHealthReport,
    FinancialHealthStatus,
    FinancialPenaltyType,
    apply_financial_morale_penalty,
    calculate_financial_health_report,
    can_register_transfer_under_financial_rules,
    can_start_stadium_upgrade_under_financial_rules,
    can_take_loan_under_financial_rules,
    classify_financial_health,
    determine_financial_penalties,
    should_cpu_avoid_purchases_under_financial_pressure,
    should_cpu_sell_under_financial_pressure,
    update_club_financial_state,
)
from garfoot.domain.player import Player
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.contract import Contract
from garfoot.domain.squad_rules import WageHealth
from garfoot.domain.team import Team


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_team(budget: int = 1_000_000, n_players: int = 0) -> Team:
    team = Team(name="Teste FC", city="Cidade", budget=budget)
    return team


def _make_player(salary: int = 10_000, morale: int = 70) -> Player:
    return Player(
        name="Jogador Teste",
        age=25,
        attack=70,
        defense=60,
        fitness=80,
        position=PlayerPosition.MIDFIELDER,
        salary=salary,
        morale=morale,
        value=100_000,
        contract=Contract(years_remaining=3, is_protected=False),
    )


def _make_report(
    status: FinancialHealthStatus,
    score: int,
    budget: int = 1_000_000,
    active_penalties: tuple[FinancialPenaltyType, ...] = (),
) -> FinancialHealthReport:
    return FinancialHealthReport(
        team_name="Clube Teste",
        status=status,
        score=score,
        budget=budget,
        wage_commitment=0.5,
        operating_burn_rate=0,
        projected_rounds_until_cashout=None,
        warnings=(),
        recommended_actions=(),
        active_penalties=active_penalties,
    )


# ---------------------------------------------------------------------------
# 1. Classificação por score
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score,expected", [
    (100, FinancialHealthStatus.HEALTHY),
    (80, FinancialHealthStatus.HEALTHY),
    (70, FinancialHealthStatus.ATTENTION),
    (60, FinancialHealthStatus.ATTENTION),
    (50, FinancialHealthStatus.PRESSURED),
    (40, FinancialHealthStatus.PRESSURED),
    (30, FinancialHealthStatus.CRISIS),
    (20, FinancialHealthStatus.CRISIS),
    (19, FinancialHealthStatus.INSOLVENT),
    (10, FinancialHealthStatus.INSOLVENT),
    (0, FinancialHealthStatus.INSOLVENT),
])
def test_classify_financial_health_all_scores(score: int, expected: FinancialHealthStatus) -> None:
    assert classify_financial_health(score) == expected


# ---------------------------------------------------------------------------
# 2. Relatório de saúde financeira
# ---------------------------------------------------------------------------

def test_healthy_team_generates_healthy_report() -> None:
    team = _make_team(budget=5_000_000)
    report = calculate_financial_health_report(
        team=team,
        wage_commitment=0.30,       # 30% da receita → HEALTHY
        operating_burn_rate=50_000,
        recurring_income_per_round=200_000,
    )
    assert report.status == FinancialHealthStatus.HEALTHY
    assert report.score >= 80
    assert report.budget == 5_000_000


def test_negative_budget_generates_warning() -> None:
    team = _make_team(budget=-200_000)
    report = calculate_financial_health_report(
        team=team,
        wage_commitment=0.30,
        operating_burn_rate=50_000,
    )
    assert report.budget < 0
    assert any("negativo" in w.lower() or "Caixa" in w for w in report.warnings)
    assert report.score < 100


def test_critical_wages_reduce_score() -> None:
    team = _make_team(budget=1_000_000)
    report_critical = calculate_financial_health_report(
        team=team,
        wage_commitment=0.95,       # CRITICAL
        operating_burn_rate=0,
    )
    report_healthy = calculate_financial_health_report(
        team=team,
        wage_commitment=0.30,       # HEALTHY
        operating_burn_rate=0,
    )
    assert report_critical.score < report_healthy.score


def test_high_burn_rate_reduces_score() -> None:
    team = _make_team(budget=500_000)
    report = calculate_financial_health_report(
        team=team,
        wage_commitment=0.30,
        operating_burn_rate=800_000,
        recurring_income_per_round=200_000,
    )
    assert report.score <= 80


def test_consecutive_negative_rounds_reduce_score() -> None:
    team = _make_team(budget=-100_000)

    state_3 = ClubFinancialState(consecutive_negative_rounds=3)
    state_10 = ClubFinancialState(consecutive_negative_rounds=10)

    report_3 = calculate_financial_health_report(
        team=team, wage_commitment=0.40, operating_burn_rate=0, financial_state=state_3
    )
    report_10 = calculate_financial_health_report(
        team=team, wage_commitment=0.40, operating_burn_rate=0, financial_state=state_10
    )
    assert report_10.score < report_3.score


# ---------------------------------------------------------------------------
# 3. Estado financeiro (ClubFinancialState) e atualização
# ---------------------------------------------------------------------------

def test_negative_budget_increments_consecutive_negative_rounds() -> None:
    state = ClubFinancialState(consecutive_negative_rounds=2)
    report = _make_report(FinancialHealthStatus.ATTENTION, score=65, budget=-1)
    new_state = update_club_financial_state(state, report)
    assert new_state.consecutive_negative_rounds == 3


def test_positive_budget_resets_negative_rounds() -> None:
    state = ClubFinancialState(consecutive_negative_rounds=5)
    report = _make_report(FinancialHealthStatus.HEALTHY, score=85, budget=500_000)
    new_state = update_club_financial_state(state, report)
    assert new_state.consecutive_negative_rounds == 0


def test_crisis_increments_crisis_rounds() -> None:
    state = ClubFinancialState(consecutive_crisis_rounds=1)
    report = _make_report(FinancialHealthStatus.CRISIS, score=25, budget=-500_000)
    new_state = update_club_financial_state(state, report)
    assert new_state.consecutive_crisis_rounds == 2


def test_healthy_reduces_crisis_rounds() -> None:
    state = ClubFinancialState(consecutive_crisis_rounds=4)
    report = _make_report(FinancialHealthStatus.HEALTHY, score=90, budget=1_000_000)
    new_state = update_club_financial_state(state, report)
    assert new_state.consecutive_crisis_rounds < 4


def test_transfer_restriction_rounds_decremented_each_update() -> None:
    state = ClubFinancialState(transfer_restriction_rounds=4)
    report = _make_report(FinancialHealthStatus.HEALTHY, score=85, budget=500_000)
    new_state = update_club_financial_state(state, report)
    assert new_state.transfer_restriction_rounds == 3


# ---------------------------------------------------------------------------
# 4. Penalidades
# ---------------------------------------------------------------------------

def test_few_crisis_rounds_only_generates_warning() -> None:
    state = ClubFinancialState(consecutive_crisis_rounds=1)
    report = _make_report(FinancialHealthStatus.CRISIS, score=25)
    penalties = determine_financial_penalties(report, state)
    assert FinancialPenaltyType.WARNING not in penalties  # WARNING só p/ ATTENTION/PRESSURED
    # Menos de 3 rodadas: sem penalidade de moral
    assert FinancialPenaltyType.MORALE_PENALTY not in penalties


def test_persistent_crisis_generates_morale_penalty() -> None:
    state = ClubFinancialState(consecutive_crisis_rounds=5)
    report = _make_report(FinancialHealthStatus.CRISIS, score=25)
    penalties = determine_financial_penalties(report, state)
    assert FinancialPenaltyType.MORALE_PENALTY in penalties


def test_persistent_insolvency_generates_transfer_restriction() -> None:
    state = ClubFinancialState(consecutive_crisis_rounds=4)
    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5)
    penalties = determine_financial_penalties(report, state)
    assert FinancialPenaltyType.TRANSFER_RESTRICTION in penalties


def test_points_deduction_only_once_per_season() -> None:
    state_first = ClubFinancialState(consecutive_crisis_rounds=7, points_deducted_this_season=0)
    state_already = ClubFinancialState(consecutive_crisis_rounds=7, points_deducted_this_season=3)

    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5)

    penalties_first = determine_financial_penalties(report, state_first)
    penalties_already = determine_financial_penalties(report, state_already)

    assert FinancialPenaltyType.POINTS_DEDUCTION in penalties_first
    assert FinancialPenaltyType.POINTS_DEDUCTION not in penalties_already


# ---------------------------------------------------------------------------
# 5. Penalidade de moral
# ---------------------------------------------------------------------------

def test_morale_penalty_reduces_player_morale() -> None:
    team = _make_team()
    player = _make_player(morale=70)
    team.players.append(player)

    apply_financial_morale_penalty(team, penalty_points=4)
    assert team.players[0].morale == 66


def test_morale_penalty_does_not_go_below_zero() -> None:
    team = _make_team()
    player = _make_player(morale=2)
    team.players.append(player)

    apply_financial_morale_penalty(team, penalty_points=10)
    assert team.players[0].morale >= 0


# ---------------------------------------------------------------------------
# 6. Restrições de mercado
# ---------------------------------------------------------------------------

def test_healthy_club_can_register_transfer() -> None:
    team = _make_team(budget=5_000_000)
    report = _make_report(FinancialHealthStatus.HEALTHY, score=90)
    ok, _ = can_register_transfer_under_financial_rules(team, 1_000_000, 50_000, report, series="A")
    assert ok


def test_insolvent_club_blocks_paid_transfer() -> None:
    team = _make_team(budget=-3_000_000)
    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5)
    ok, reason = can_register_transfer_under_financial_rules(team, 500_000, 20_000, report, series="D")
    assert not ok
    assert "insolvente" in reason.lower()


def test_crisis_club_blocks_transfer_above_cap() -> None:
    team = _make_team(budget=500_000)
    report = _make_report(FinancialHealthStatus.CRISIS, score=30)
    cap = CRISIS_TRANSFER_CAP["D"]
    ok, reason = can_register_transfer_under_financial_rules(team, cap + 1, 5_000, report, series="D")
    assert not ok
    assert "crise" in reason.lower()


def test_crisis_club_allows_transfer_within_cap() -> None:
    team = _make_team(budget=500_000)
    report = _make_report(FinancialHealthStatus.CRISIS, score=30)
    cap = CRISIS_TRANSFER_CAP["D"]
    ok, _ = can_register_transfer_under_financial_rules(team, cap - 1, 5_000, report, series="D")
    assert ok


def test_transfer_restriction_active_blocks_all_purchases() -> None:
    team = _make_team(budget=2_000_000)
    report = _make_report(
        FinancialHealthStatus.CRISIS,
        score=30,
        active_penalties=(FinancialPenaltyType.TRANSFER_RESTRICTION,),
    )
    ok, reason = can_register_transfer_under_financial_rules(team, 10_000, 5_000, report, series="D")
    assert not ok
    assert "restrição" in reason.lower()


# ---------------------------------------------------------------------------
# 7. Restrições de upgrade de estádio
# ---------------------------------------------------------------------------

def test_healthy_club_can_upgrade_stadium() -> None:
    team = _make_team(budget=5_000_000)
    report = _make_report(FinancialHealthStatus.HEALTHY, score=90)
    ok, _ = can_start_stadium_upgrade_under_financial_rules(team, 1_000_000, report)
    assert ok


def test_insolvent_club_cannot_upgrade_stadium() -> None:
    team = _make_team(budget=-1_000_000)
    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5, budget=-1_000_000)
    ok, reason = can_start_stadium_upgrade_under_financial_rules(team, 500_000, report)
    assert not ok
    assert "insolvente" in reason.lower()


def test_crisis_club_cannot_do_expensive_stadium_upgrade() -> None:
    team = _make_team(budget=200_000)
    report = _make_report(FinancialHealthStatus.CRISIS, score=25, budget=200_000)
    # Custo > 50% do caixa → bloqueado
    ok, reason = can_start_stadium_upgrade_under_financial_rules(team, 150_000, report)
    assert not ok
    assert "crise" in reason.lower()


# ---------------------------------------------------------------------------
# 8. CPU — comportamento sob pressão
# ---------------------------------------------------------------------------

def test_cpu_should_sell_in_crisis() -> None:
    report = _make_report(FinancialHealthStatus.CRISIS, score=25)
    assert should_cpu_sell_under_financial_pressure(report) is True


def test_cpu_should_sell_in_insolvent() -> None:
    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5)
    assert should_cpu_sell_under_financial_pressure(report) is True


def test_cpu_should_not_sell_when_healthy() -> None:
    report = _make_report(FinancialHealthStatus.HEALTHY, score=90)
    assert should_cpu_sell_under_financial_pressure(report) is False


def test_cpu_avoids_purchases_when_pressured_or_worse() -> None:
    for status in (FinancialHealthStatus.PRESSURED, FinancialHealthStatus.CRISIS, FinancialHealthStatus.INSOLVENT):
        report = _make_report(status, score=50)
        assert should_cpu_avoid_purchases_under_financial_pressure(report) is True


def test_cpu_allows_purchases_when_healthy_or_attention() -> None:
    for status in (FinancialHealthStatus.HEALTHY, FinancialHealthStatus.ATTENTION):
        report = _make_report(status, score=80)
        assert should_cpu_avoid_purchases_under_financial_pressure(report) is False


# ---------------------------------------------------------------------------
# 9. Empréstimos
# ---------------------------------------------------------------------------

def test_healthy_club_can_take_loan() -> None:
    team = _make_team()
    report = _make_report(FinancialHealthStatus.HEALTHY, score=85)
    ok, _ = can_take_loan_under_financial_rules(team, report)
    assert ok


def test_insolvent_club_cannot_take_loan() -> None:
    team = _make_team()
    report = _make_report(FinancialHealthStatus.INSOLVENT, score=5)
    ok, reason = can_take_loan_under_financial_rules(team, report)
    assert not ok
    assert "insolvente" in reason.lower()


# ---------------------------------------------------------------------------
# 10. Save / load de Team com financial_state
# ---------------------------------------------------------------------------

def test_team_serializes_and_restores_financial_state() -> None:
    team = _make_team()
    team.financial_state.consecutive_crisis_rounds = 4
    team.financial_state.consecutive_negative_rounds = 7

    data = team.to_dict()
    assert "financial_state" in data
    assert data["financial_state"]["consecutive_crisis_rounds"] == 4

    restored = Team.from_dict(data)
    assert restored.financial_state.consecutive_crisis_rounds == 4
    assert restored.financial_state.consecutive_negative_rounds == 7


def test_legacy_save_without_financial_state_loads_healthy() -> None:
    team = _make_team()
    data = team.to_dict()
    del data["financial_state"]

    restored = Team.from_dict(data)
    assert restored.financial_state is not None
    assert restored.financial_state.last_health_status == FinancialHealthStatus.HEALTHY
    assert restored.financial_state.consecutive_crisis_rounds == 0


# ---------------------------------------------------------------------------
# 11. Engine permanece pura
# ---------------------------------------------------------------------------

def test_engine_does_not_import_financial_health() -> None:
    import importlib
    import sys

    # Garante que a engine não contém referência ao módulo de saúde financeira
    engine_modules = [k for k in sys.modules if k.startswith("garfoot.engine")]
    for mod_name in engine_modules:
        mod = sys.modules[mod_name]
        source_file = getattr(mod, "__file__", "") or ""
        if source_file.endswith(".py"):
            with open(source_file) as f:
                content = f.read()
            assert "financial_health" not in content, (
                f"Engine module {mod_name} importa financial_health — violação de pureza!"
            )
