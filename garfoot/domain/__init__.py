"""Modelos de dominio do Garfoot."""

from garfoot.domain.enums import MatchStatus, PlayerPosition
from garfoot.domain.league import Championship, LeagueStanding, MatchFixture
from garfoot.domain.player import Player
from garfoot.domain.prizes import (
    CompetitionPrize,
    CompetitionType,
    PrizeCategory,
    PrizeStructure,
)
from garfoot.domain.season import (
    LeagueTier,
    NextSeasonComposition,
    apply_promotion_relegation,
)
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Formation, Team

from garfoot.domain.stable_random import (
    combine_seed,
    stable_composite_seed,
    stable_int_seed,
)

__all__ = [
    "Championship",
    "CompetitionPrize",
    "CompetitionType",
    "Formation",
    "LeagueStanding",
    "LeagueTier",
    "MatchFixture",
    "MatchStatus",
    "NextSeasonComposition",
    "Player",
    "PlayerPosition",
    "PrizeCategory",
    "PrizeStructure",
    "Stadium",
    "Team",
    "apply_promotion_relegation",
    "combine_seed",
    "stable_composite_seed",
    "stable_int_seed",
]
