"""Aplicação de regras de progressão pós-partida nos elencos."""

from __future__ import annotations

from dataclasses import replace
from random import Random
from typing import Counter

from garfoot.domain.injury import InjurySeverity, advance_player_injury, apply_injury_to_player, create_injury
from garfoot.engine.events import GoalEvent, InjuryEvent
from garfoot.engine.match_engine import MatchResult
from garfoot.domain.player import Player
from garfoot.domain.stable_random import stable_composite_seed
from garfoot.domain.player_progression import (
    MatchOutcome,
    apply_post_match_fatigue,
    apply_post_match_morale,
)
from garfoot.domain.team import Team


def apply_post_match_progression(
    home: Team,
    away: Team,
    result: MatchResult,
) -> tuple[Team, Team]:
    """Aplica fadiga, lesões, descanso e alterações de moral aos jogadores após a partida."""

    # Determina o resultado para cada time
    if result.home_score > result.away_score:
        outcome_home = MatchOutcome.WIN
        outcome_away = MatchOutcome.LOSS
    elif result.away_score > result.home_score:
        outcome_home = MatchOutcome.LOSS
        outcome_away = MatchOutcome.WIN
    else:
        outcome_home = MatchOutcome.DRAW
        outcome_away = MatchOutcome.DRAW

    # Contagem de gols e lesões ocorridos nos eventos da partida
    goals_counter: Counter[str] = Counter(
        event.player_name for event in result.events if isinstance(event, GoalEvent)
    )

    injured_players_map: dict[str, InjuryEvent] = {
        event.player_name: event for event in result.events if isinstance(event, InjuryEvent)
    }

    home_starters_set = set(result.starters_home)
    away_starters_set = set(result.starters_away)

    updated_home_players = _process_team_players(
        home.players, home_starters_set, outcome_home, goals_counter, injured_players_map
    )
    updated_away_players = _process_team_players(
        away.players, away_starters_set, outcome_away, goals_counter, injured_players_map
    )

    new_home = replace(home, players=updated_home_players)
    new_away = replace(away, players=updated_away_players)

    return new_home, new_away


def _process_team_players(
    players: list[Player],
    starters_set: set[str],
    outcome: MatchOutcome,
    goals_counter: Counter[str],
    injured_players_map: dict[str, InjuryEvent],
) -> list[Player]:
    updated: list[Player] = []
    for p in players:
        # 0. Avança lesão existente anterior
        p_current = advance_player_injury(p)

        played = p_current.name in starters_set
        minutes = 90 if played else 0
        goals = goals_counter.get(p_current.name, 0)

        # 1. Aplica fadiga ou descanso
        p_fatigued = apply_post_match_fatigue(p_current, minutes_played=minutes)
        # 2. Aplica moral
        p_final = apply_post_match_morale(p_fatigued, outcome=outcome, scored_goals=goals)

        # 3. Se sofreu nova lesão nesta partida, aplica as consequências
        if p_final.name in injured_players_map:
            inj_event = injured_players_map[p_final.name]
            seed_val = stable_composite_seed((p_final.name, inj_event.minute), namespace="match-injury-severity")
            rng = Random(seed_val)
            # Sorteia a severidade (70% MINOR, 20% MODERATE, 10% SEVERE)
            roll = rng.random()
            if roll < 0.70:
                severity = InjurySeverity.MINOR
            elif roll < 0.90:
                severity = InjurySeverity.MODERATE
            else:
                severity = InjurySeverity.SEVERE

            injury = create_injury(severity, rng=rng)
            p_final = apply_injury_to_player(p_final, injury)

        updated.append(p_final)
    return updated
