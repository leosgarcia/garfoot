"""Testes unitários para rivalidade, apelo do adversário e impacto na lotação do estádio."""

import pytest

from garfoot.domain.match_appeal import (
    MatchAppealContext,
    MatchImportance,
    OpponentAppeal,
    RivalryLevel,
    calculate_match_appeal_factor,
    calculate_opponent_appeal_bonus,
    calculate_rivalry_bonus,
    infer_match_importance,
    infer_opponent_appeal,
    infer_rivalry_level,
)
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team


def test_rivalry_and_opponent_appeal_bonuses():
    assert calculate_rivalry_bonus(RivalryLevel.NONE) == 0.00
    assert calculate_rivalry_bonus(RivalryLevel.STATE_CLASSIC) == 0.07
    assert calculate_rivalry_bonus(RivalryLevel.CITY_CLASSIC) == 0.10
    assert calculate_rivalry_bonus(RivalryLevel.HISTORIC) == 0.12

    assert calculate_opponent_appeal_bonus(OpponentAppeal.LOW) == -0.03
    assert calculate_opponent_appeal_bonus(OpponentAppeal.MEDIUM) == 0.00
    assert calculate_opponent_appeal_bonus(OpponentAppeal.NATIONAL) == 0.08


def test_combined_match_appeal_factor():
    ctx_high = MatchAppealContext(
        rivalry_level=RivalryLevel.CITY_CLASSIC,  # +0.10
        match_importance=MatchImportance.FINAL,   # +0.12
        opponent_appeal=OpponentAppeal.NATIONAL,   # +0.08
    )
    factor = calculate_match_appeal_factor(ctx_high)
    assert round(factor, 2) == 0.30

    ctx_low = MatchAppealContext(
        rivalry_level=RivalryLevel.NONE,
        match_importance=MatchImportance.NORMAL,
        opponent_appeal=OpponentAppeal.LOW,       # -0.03
    )
    assert round(calculate_match_appeal_factor(ctx_low), 2) == -0.03


def test_stadium_attendance_rate_clamping_with_appeal():
    stadium = Stadium(name="Maracanã", city="Rio de Janeiro", capacity=80_000, average_ticket_price=50)

    # 1. Jogo normal com moral média 50
    rate_normal = stadium.estimate_attendance_rate(morale=50, performance=0.5)
    assert rate_normal == 0.45

    # 2. Grande Final Clássica contra adversário Nacional (deve aumentar muito, mas travar no máximo 95%)
    ctx_final = MatchAppealContext(
        rivalry_level=RivalryLevel.HISTORIC,      # +0.12
        match_importance=MatchImportance.FINAL,   # +0.12
        opponent_appeal=OpponentAppeal.NATIONAL,   # +0.08
    )
    rate_appeal = stadium.estimate_attendance_rate_with_appeal(morale=90, performance=0.9, appeal_context=ctx_final)
    assert rate_appeal == 0.95  # Travado no teto máximo de 95%

    # 3. Jogo de baixíssimo apelo com moral péssima (trava no piso de 20%)
    ctx_low = MatchAppealContext(opponent_appeal=OpponentAppeal.LOW)
    rate_low = stadium.estimate_attendance_rate_with_appeal(morale=10, performance=0.1, appeal_context=ctx_low)
    assert rate_low == 0.20


def test_stadium_and_team_match_income_with_appeal():
    stadium = Stadium(name="Arena", city="Curitiba", capacity=40_000, average_ticket_price=40)
    team = Team(name="Athletico", city="Curitiba", budget=5_000_000, stadium=stadium)

    income_normal = team.estimate_match_income(performance=0.5)

    ctx = MatchAppealContext(
        rivalry_level=RivalryLevel.CITY_CLASSIC,
        match_importance=MatchImportance.FINAL,
        opponent_appeal=OpponentAppeal.HIGH,
    )
    income_high_appeal = team.estimate_match_income(performance=0.5, appeal_context=ctx)

    assert income_high_appeal > income_normal


def test_infer_rivalry_level():
    team_fla = type("T", (), {"name": "Flamengo", "city": "Rio de Janeiro", "state": "RJ"})()
    team_flu = type("T", (), {"name": "Fluminense", "city": "Rio de Janeiro", "state": "RJ"})()
    team_vasco_sp = type("T", (), {"name": "Vasco", "city": "Niterói", "state": "RJ"})()
    team_gremio = type("T", (), {"name": "Grêmio", "city": "Porto Alegre", "state": "RS"})()

    # Mesma cidade -> CITY_CLASSIC
    assert infer_rivalry_level(team_fla, team_flu) == RivalryLevel.CITY_CLASSIC

    # Mesmo estado -> STATE_CLASSIC
    assert infer_rivalry_level(team_fla, team_vasco_sp) == RivalryLevel.STATE_CLASSIC

    # Estados diferentes sem rivalidade no mapa -> NONE
    assert infer_rivalry_level(team_fla, team_gremio) == RivalryLevel.NONE

    # Mapa explícito prevalece
    rival_map = {("Flamengo", "Grêmio"): RivalryLevel.HISTORIC}
    assert infer_rivalry_level(team_fla, team_gremio, rivalry_map=rival_map) == RivalryLevel.HISTORIC


def test_infer_opponent_appeal_and_importance():
    team = type("T", (), {"name": "Time A"})()

    assert infer_opponent_appeal(team, series="A") == OpponentAppeal.NATIONAL
    assert infer_opponent_appeal(team, series="D") == OpponentAppeal.LOW

    assert infer_match_importance(is_final=True) == MatchImportance.FINAL
    assert infer_match_importance(is_semifinal=True) == MatchImportance.SEMIFINAL
    assert infer_match_importance(is_knockout=True) == MatchImportance.KNOCKOUT
    assert infer_match_importance(round_number=37, total_rounds=38) == MatchImportance.TITLE_DECIDER
