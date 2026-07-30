"""Testes unitários para a orquestração de temporada e Super Campeão."""

import pytest

from garfoot.domain.cup import CupMatch, KnockoutCup
from garfoot.domain.league import Championship, MatchFixture
from garfoot.domain.season import LeagueTier
from garfoot.domain.season_orchestrator import (
    SeasonOrchestrator,
    SuperChampionMatchup,
    determine_super_champion_matchup,
)
from garfoot.domain.team import Team


def _make_team(name: str) -> Team:
    return Team(name=name, city="Cidade", budget=100_000)


def test_determine_super_champion_matchup_standard():
    # Caso Padrão: Campeão da Série A != Campeão da Copa do Brasil
    matchup = determine_super_champion_matchup(
        serie_a_champion="Flamengo",
        serie_a_runner_up="Palmeiras",
        copa_brasil_champion="Corinthians",
    )

    assert matchup == SuperChampionMatchup(
        home_team="Flamengo",
        away_team="Corinthians",
        is_double_winner_rule_applied=False,
    )


def test_determine_super_champion_matchup_double_winner():
    # Caso Dobradinha: Campeão da Série A == Campeão da Copa do Brasil
    matchup = determine_super_champion_matchup(
        serie_a_champion="Flamengo",
        serie_a_runner_up="Palmeiras",
        copa_brasil_champion="Flamengo",
    )

    assert matchup == SuperChampionMatchup(
        home_team="Flamengo",
        away_team="Palmeiras",
        is_double_winner_rule_applied=True,
    )


def test_season_orchestrator_integration():
    teams_a = [_make_team("Flamengo"), _make_team("Palmeiras"), _make_team("Sao Paulo"), _make_team("Santos")]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams_a)
    champ_a.generate_round_robin_fixtures(double_round=False)

    # Simula todos os jogos da Série A
    for fix in champ_a.fixtures:
        if fix.home_team == "Flamengo":
            fix.record_result(3, 0)
        elif fix.away_team == "Flamengo":
            fix.record_result(0, 3)
        else:
            fix.record_result(1, 0)

    # Cria Copa do Brasil com final já jogada (Dobradinha de Flamengo)
    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams_a)
    final_fixture = MatchFixture(round_number=1, home_team="Flamengo", away_team="Palmeiras")
    final_match = CupMatch(fixture=final_fixture)
    final_match.record_result(2, 0)
    copa.rounds = [[final_match]]

    orchestrator = SeasonOrchestrator(
        season_year=2026,
        championships={LeagueTier.SERIE_A: champ_a},
        copa_do_brasil=copa,
    )

    super_match = orchestrator.build_super_champion_match()

    assert super_match.fixture.home_team == "Flamengo"
    assert super_match.fixture.away_team == "Palmeiras"
    assert orchestrator.super_champion_match is not None


def test_season_orchestrator_start_new_season():
    teams = [_make_team(f"Time {i:02d}") for i in range(1, 21)]
    champ_a = Championship(name="Série A 2026", season_year=2026, teams=teams)
    copa = KnockoutCup(name="Copa 2026", season_year=2026, teams=teams)

    orchestrator = SeasonOrchestrator(
        season_year=2026,
        championships={LeagueTier.SERIE_A: champ_a},
        copa_do_brasil=copa,
    )

    cbf_ranking = {t.name: i for i, t in enumerate(teams, start=1)}
    orchestrator.start_new_season(cbf_ranking=cbf_ranking, seed=42)

    # Série A com 380 jogos gerados
    assert len(champ_a.fixtures) == 380

    # Copa do Brasil com chaveamento inicial e byes gerados para 20 times (32 - 20 = 12 byes, 8 times jogando = 4 jogos)
    assert len(copa.rounds) == 1
    assert len(copa.rounds[0]) == 4


def test_season_orchestrator_start_new_season_all_four_tiers_80_teams():
    """Testa a inicialização completa da temporada com 4 séries (80 times no total)."""
    teams_a = [_make_team(f"TimeA_{i:02d}") for i in range(1, 21)]
    teams_b = [_make_team(f"TimeB_{i:02d}") for i in range(1, 21)]
    teams_c = [_make_team(f"TimeC_{i:02d}") for i in range(1, 21)]
    teams_d = [_make_team(f"TimeD_{i:02d}") for i in range(1, 21)]

    all_teams = teams_a + teams_b + teams_c + teams_d
    cbf_ranking = {t.name: i for i, t in enumerate(all_teams, start=1)}

    championships = {
        LeagueTier.SERIE_A: Championship(name="Série A 2026", season_year=2026, teams=teams_a),
        LeagueTier.SERIE_B: Championship(name="Série B 2026", season_year=2026, teams=teams_b),
        LeagueTier.SERIE_C: Championship(name="Série C 2026", season_year=2026, teams=teams_c),
        LeagueTier.SERIE_D: Championship(name="Série D 2026", season_year=2026, teams=teams_d),
    }

    copa = KnockoutCup(name="Copa do Brasil 2026", season_year=2026, teams=all_teams)

    orchestrator = SeasonOrchestrator(
        season_year=2026,
        championships=championships,
        copa_do_brasil=copa,
    )

    orchestrator.start_new_season(cbf_ranking=cbf_ranking, seed=42)

    # Cada uma das 4 séries deve ter exatamente 380 jogos gerados (38 rodadas)
    for tier, champ in championships.items():
        assert len(champ.fixtures) == 380, f"{tier.value} não gerou 380 partidas."

    # Copa do Brasil com 80 times ativa a fase preliminar (32 piores -> 16 jogos)
    assert len(copa.preliminary_round) == 16
    assert len(copa.rounds) == 0  # Fase principal aguarda a conclusão da preliminar

