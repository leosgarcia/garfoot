"""Testes do motor de simulacao de partidas."""

from __future__ import annotations

import pytest

from garfoot.engine.events import GoalEvent
from garfoot.engine.match_engine import MatchResult, simulate_match


@pytest.mark.parametrize("seed", [1, 42, 12345])
def test_same_seed_produces_identical_match_result(strong_team, weak_team, seed):
    first = simulate_match(strong_team, weak_team, seed=seed)
    second = simulate_match(strong_team, weak_team, seed=seed)

    assert first == second


def test_different_seeds_are_not_all_identical(strong_team, weak_team):
    results = [simulate_match(strong_team, weak_team, seed=seed) for seed in range(5)]
    signatures = {
        (
            result.home_score,
            result.away_score,
            result.events,
            result.shots_home,
            result.shots_away,
            result.cards_home,
            result.cards_away,
        )
        for result in results
    }

    assert len(signatures) > 1


@pytest.mark.slow
def test_strong_home_team_wins_at_least_55_percent_against_weak_team(
    strong_team,
    weak_team,
):
    # Validacao estatistica: usa seeds fixas para ficar reprodutivel.
    wins = 0
    simulations = 500

    for seed in range(simulations):
        result = simulate_match(strong_team, weak_team, seed=seed)
        if result.home_score > result.away_score:
            wins += 1

    assert wins / simulations >= 0.55


@pytest.mark.slow
def test_strong_away_team_still_outperforms_weak_home_team(strong_team, weak_team):
    # O mando ajuda, mas nao deve apagar uma diferenca grande de qualidade.
    strong_wins = 0
    weak_wins = 0
    simulations = 500

    for seed in range(simulations):
        result = simulate_match(weak_team, strong_team, seed=seed)
        if result.away_score > result.home_score:
            strong_wins += 1
        elif result.home_score > result.away_score:
            weak_wins += 1

    assert strong_wins > weak_wins


def test_equal_teams_with_same_seed_produce_valid_results(
    equal_home_team,
    equal_away_team,
):
    for seed in [1, 2, 3, 42, 99]:
        result = simulate_match(equal_home_team, equal_away_team, seed=seed)

        assert isinstance(result, MatchResult)
        assert result.home_score >= 0
        assert result.away_score >= 0
        assert result.shots_home >= 0
        assert result.shots_away >= 0
        assert result.cards_home >= 0
        assert result.cards_away >= 0
        assert result.events == tuple(sorted(result.events, key=lambda event: event.minute))


def test_short_rosters_do_not_raise(short_roster_home, short_roster_away):
    result = simulate_match(short_roster_home, short_roster_away, seed=7)

    assert isinstance(result, MatchResult)
    assert result.home_team_name == short_roster_home.name
    assert result.away_team_name == short_roster_away.name


def test_score_matches_goal_events(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team, seed=123)

    home_goals = sum(
        isinstance(event, GoalEvent) and event.team_name == result.home_team_name
        for event in result.events
    )
    away_goals = sum(
        isinstance(event, GoalEvent) and event.team_name == result.away_team_name
        for event in result.events
    )

    assert result.home_score == home_goals
    assert result.away_score == away_goals
