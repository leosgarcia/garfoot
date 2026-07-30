"""Orquestracao da simulacao minuto a minuto de uma partida."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.engine.events import (
    CardEvent,
    CardType,
    GoalEvent,
    InjuryEvent,
    MatchEvent,
    MissedChanceEvent,
    ShotEvent,
)
from garfoot.engine.probability import (
    TeamMatchProfile,
    build_team_profile,
    calculate_goal_chance,
    calculate_possession,
)


MATCH_MINUTES = 90
EVENT_CHANCE_PER_MINUTE = 0.22
SHOT_OR_CHANCE_RATE = 0.75
CARD_RATE = 0.18
INJURY_RATE = 0.07
REGULAR_SHOT_RATE = 0.70
REGULAR_SHOT_QUALITY = 0.75
CLEAR_CHANCE_QUALITY = 1.35
YELLOW_CARD_RATE = 0.90
ASSIST_RATE = 0.45
SHOT_ON_TARGET_RATE = 0.42


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Resultado completo e serializavel de uma simulacao."""

    home_team_name: str
    away_team_name: str
    home_score: int
    away_score: int
    events: tuple[MatchEvent, ...]
    shots_home: int
    shots_away: int
    possession_home: float
    possession_away: float
    cards_home: int
    cards_away: int
    starters_home: tuple[str, ...] = ()
    starters_away: tuple[str, ...] = ()


def simulate_match(home: Team, away: Team, seed: int | None = None) -> MatchResult:
    """Simula uma partida completa.

    A simulacao roda 90 minutos, com chance fixa de lance relevante por minuto.
    Dentro de lances ofensivos, 70% sao chutes comuns e 30% chances claras.
    Cartoes sao 90% amarelos e 10% vermelhos. Em gols, ha 45% de chance de
    registrar assistencia de outro titular do mesmo time.
    """

    random = Random(seed)
    home_profile = build_team_profile(home, is_home=True)
    away_profile = build_team_profile(away, is_home=False)
    possession_home, possession_away = calculate_possession(home_profile, away_profile)

    events: list[MatchEvent] = []
    shots_home = 0
    shots_away = 0
    cards_home = 0
    cards_away = 0

    for minute in range(1, MATCH_MINUTES + 1):
        if random.random() > EVENT_CHANCE_PER_MINUTE:
            continue

        acting_profile, opposing_profile = _choose_acting_team(
            random,
            home_profile,
            away_profile,
            possession_home,
        )
        event_roll = random.random()

        if event_roll < SHOT_OR_CHANCE_RATE:
            event = _simulate_shot_event(
                random,
                minute,
                acting_profile,
                opposing_profile,
            )
            events.append(event)
            if acting_profile.team_name == home.name:
                shots_home += 1
            else:
                shots_away += 1
        elif event_roll < SHOT_OR_CHANCE_RATE + CARD_RATE:
            event = _simulate_card_event(random, minute, acting_profile)
            events.append(event)
            if acting_profile.team_name == home.name:
                cards_home += 1
            else:
                cards_away += 1
        else:
            events.append(_simulate_injury_event(random, minute, acting_profile))

    home_score = sum(
        isinstance(event, GoalEvent) and event.team_name == home.name
        for event in events
    )
    away_score = sum(
        isinstance(event, GoalEvent) and event.team_name == away.name
        for event in events
    )

    starters_home_names = tuple(p.name for p in home_profile.starters)
    starters_away_names = tuple(p.name for p in away_profile.starters)

    return MatchResult(
        home_team_name=home.name,
        away_team_name=away.name,
        home_score=home_score,
        away_score=away_score,
        events=tuple(events),
        shots_home=shots_home,
        shots_away=shots_away,
        possession_home=possession_home,
        possession_away=possession_away,
        cards_home=cards_home,
        cards_away=cards_away,
        starters_home=starters_home_names,
        starters_away=starters_away_names,
    )


def _choose_acting_team(
    random: Random,
    home_profile: TeamMatchProfile,
    away_profile: TeamMatchProfile,
    possession_home: float,
) -> tuple[TeamMatchProfile, TeamMatchProfile]:
    if random.random() < possession_home:
        return home_profile, away_profile
    return away_profile, home_profile


def _simulate_shot_event(
    random: Random,
    minute: int,
    attacking: TeamMatchProfile,
    defending: TeamMatchProfile,
) -> MatchEvent:
    player = _choose_player(random, attacking.starters)
    is_regular_shot = random.random() < REGULAR_SHOT_RATE
    shot_quality = REGULAR_SHOT_QUALITY if is_regular_shot else CLEAR_CHANCE_QUALITY
    goal_chance = calculate_goal_chance(attacking, defending, shot_quality)

    if random.random() < goal_chance:
        return GoalEvent(
            minute=minute,
            team_name=attacking.team_name,
            player_name=player.name,
            assisted_by=_choose_assistant(random, attacking.starters, player),
        )

    if is_regular_shot:
        return ShotEvent(
            minute=minute,
            team_name=attacking.team_name,
            player_name=player.name,
            on_target=random.random() < SHOT_ON_TARGET_RATE,
        )

    return MissedChanceEvent(
        minute=minute,
        team_name=attacking.team_name,
        player_name=player.name,
        on_target=random.random() < SHOT_ON_TARGET_RATE,
    )


def _simulate_card_event(
    random: Random,
    minute: int,
    profile: TeamMatchProfile,
) -> CardEvent:
    card_type = (
        CardType.YELLOW
        if random.random() < YELLOW_CARD_RATE
        else CardType.RED
    )
    return CardEvent(
        minute=minute,
        team_name=profile.team_name,
        player_name=_choose_player(random, profile.starters).name,
        card_type=card_type,
    )


def _simulate_injury_event(
    random: Random,
    minute: int,
    profile: TeamMatchProfile,
) -> InjuryEvent:
    return InjuryEvent(
        minute=minute,
        team_name=profile.team_name,
        player_name=_choose_player(random, profile.starters).name,
    )


def _choose_player(random: Random, players: tuple[Player, ...]) -> Player:
    if players:
        return random.choice(players)
    return Player(
        name="Jogador desconhecido",
        age=25,
        position=PlayerPosition.MIDFIELDER,
        attack=1,
        defense=1,
        fitness=1,
        morale=1,
        value=0,
    )


def _choose_assistant(
    random: Random,
    players: tuple[Player, ...],
    scorer: Player,
) -> str | None:
    if random.random() >= ASSIST_RATE:
        return None

    candidates = [player for player in players if player.name != scorer.name]
    if not candidates:
        return None
    return random.choice(candidates).name
