"""Testes unitários para as premiações financeiras de fim de temporada."""

import pytest

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.prizes import (
    CompetitionType,
    PrizeCategory,
    PrizeStructure,
    SeasonAward,
    SeasonAwardsResult,
    apply_season_awards,
    build_season_awards,
)
from garfoot.domain.statistics import SeasonStatisticsManager
from garfoot.domain.team import Team


def test_prize_structure_defaults_and_customization():
    prizes = PrizeStructure.default_brazil_2026()

    assert prizes.prize_for(CompetitionType.SERIE_A, PrizeCategory.CHAMPION) == 12_000_000
    assert prizes.prize_for(CompetitionType.SERIE_A, PrizeCategory.RUNNER_UP) == 6_000_000
    assert prizes.prize_for(CompetitionType.SERIE_D, PrizeCategory.CHAMPION) == 800_000
    assert prizes.prize_for(CompetitionType.SERIE_D, PrizeCategory.RUNNER_UP) == 400_000
    assert prizes.prize_for(CompetitionType.BRAZIL_CUP, PrizeCategory.CHAMPION) == 10_000_000


def test_build_season_awards_champions_runners_and_golden_boot():
    stats_mgr = SeasonStatisticsManager()
    stats_mgr.record_goal("Pedro", "Santa Cruz", "Série D", age=26, overall=75)
    stats_mgr.record_goal("Pedro", "Santa Cruz", "Série D", age=26, overall=75)

    standings = {
        CompetitionType.SERIE_D: [("Santa Cruz", 1), ("Treze", 2)],
        CompetitionType.SERIE_A: [("Flamengo", 1), ("Palmeiras", 2)],
    }

    awards_res = build_season_awards(
        season_year=2026,
        championship_standings=standings,
        copa_brasil_result=("Grêmio", "Bahia"),
        stats_manager=stats_mgr,
    )

    assert awards_res.applied is False
    assert len(awards_res.awards) >= 6

    # Campeão e Vice Série D
    sd_champ = next(a for a in awards_res.awards if a.competition == "SERIE_D" and a.category == "campeao")
    assert sd_champ.team_name == "Santa Cruz"
    assert sd_champ.amount == 800_000

    # Chuteira de Ouro
    golden_boot = next(a for a in awards_res.awards if a.category == "chuteira_de_ouro")
    assert golden_boot.team_name == "Santa Cruz"
    assert golden_boot.player_name == "Pedro"
    assert golden_boot.amount == 1_000_000


def test_apply_season_awards_financial_impact_and_idempotency():
    team_santa = Team(name="Santa Cruz", city="Recife", budget=500_000)
    team_treze = Team(name="Treze", city="Campina Grande", budget=200_000)

    awards = [
        SeasonAward(competition="SERIE_D", category="campeao", team_name="Santa Cruz", amount=800_000),
        SeasonAward(competition="SERIE_D", category="vice", team_name="Treze", amount=400_000),
        SeasonAward(competition="TEMPORADA", category="chuteira_de_ouro", team_name="Santa Cruz", amount=1_000_000, player_name="Pedro"),
    ]
    awards_res = SeasonAwardsResult(season_year=2026, awards=awards, applied=False)

    # 1ª Aplicação: Santa Cruz ganha 800k + 1M = +1.8M (total: 2.3M); Treze ganha 400k (total: 600k)
    updated_teams, applied_res = apply_season_awards([team_santa, team_treze], awards_res)

    assert applied_res.applied is True
    santa_updated = next(t for t in updated_teams if t.name == "Santa Cruz")
    treze_updated = next(t for t in updated_teams if t.name == "Treze")

    assert santa_updated.budget == 2_300_000
    assert treze_updated.budget == 600_000

    # 2ª Aplicação (Idempotente): não altera os orçamentos novamente
    again_teams, again_res = apply_season_awards(updated_teams, applied_res)
    santa_again = next(t for t in again_teams if t.name == "Santa Cruz")

    assert santa_again.budget == 2_300_000


def test_season_awards_serialization_and_backwards_compatibility():
    awards = [SeasonAward(competition="SERIE_A", category="campeao", team_name="Flamengo", amount=12_000_000)]
    result = SeasonAwardsResult(season_year=2026, awards=awards, applied=True)

    serialized = result.to_dict()
    assert serialized["season_year"] == 2026
    assert serialized["applied"] is True

    restored = SeasonAwardsResult.from_dict(serialized)
    assert restored is not None
    assert restored.applied is True
    assert restored.awards[0].team_name == "Flamengo"

    # Save antigo sem premiações
    assert SeasonAwardsResult.from_dict(None) is None
