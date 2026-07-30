"""Testes das funcoes puras de probabilidade."""

from __future__ import annotations

from garfoot.engine.probability import (
    build_team_profile,
    calculate_goal_chance,
    calculate_possession,
)


def test_stronger_team_profile_has_higher_attack_and_defense(strong_team, weak_team):
    strong = build_team_profile(strong_team, is_home=True)
    weak = build_team_profile(weak_team, is_home=False)

    assert strong.attack_rating > weak.attack_rating
    assert strong.defense_rating > weak.defense_rating
    assert strong.midfield_rating > weak.midfield_rating


def test_possession_is_clamped_and_sums_to_one(strong_team, weak_team):
    strong = build_team_profile(strong_team, is_home=True)
    weak = build_team_profile(weak_team, is_home=False)

    home_possession, away_possession = calculate_possession(strong, weak)

    assert 0.35 <= home_possession <= 0.65
    assert 0.35 <= away_possession <= 0.65
    assert home_possession + away_possession == 1.0


def test_goal_chance_is_clamped_for_extreme_profiles(strong_team, weak_team):
    strong = build_team_profile(strong_team, is_home=True)
    weak = build_team_profile(weak_team, is_home=False)

    high_chance = calculate_goal_chance(strong, weak, shot_quality=10.0)
    low_chance = calculate_goal_chance(weak, strong, shot_quality=0.01)

    assert high_chance == 0.35
    assert low_chance == 0.03
