"""Modelos de campeonato por pontos corridos."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from garfoot.domain.enums import MatchStatus
from garfoot.domain.team import Team


@dataclass(slots=True)
class MatchFixture:
    """Partida do calendario de uma liga."""

    round_number: int
    home_team: str
    away_team: str
    status: MatchStatus = MatchStatus.SCHEDULED
    home_goals: int | None = None
    away_goals: int | None = None

    def record_result(self, home_goals: int, away_goals: int) -> None:
        if home_goals < 0 or away_goals < 0:
            raise ValueError("Gols nao podem ser negativos.")
        self.home_goals = home_goals
        self.away_goals = away_goals
        self.status = MatchStatus.PLAYED

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "MatchFixture":
        payload = dict(data)
        payload["status"] = MatchStatus(str(payload["status"]))
        return cls(**payload)  # type: ignore[arg-type]


@dataclass(slots=True)
class LeagueStanding:
    """Linha da tabela de classificacao."""

    team_name: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def apply_match(self, goals_for: int, goals_against: int) -> None:
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against

        if goals_for > goals_against:
            self.wins += 1
            self.points += 3
        elif goals_for == goals_against:
            self.draws += 1
            self.points += 1
        else:
            self.losses += 1


@dataclass(slots=True)
class Championship:
    """Liga de pontos corridos com calendario e tabela derivada."""

    name: str
    season_year: int
    teams: list[Team]
    fixtures: list[MatchFixture] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("O campeonato precisa ter nome.")
        if len(self.teams) < 2:
            raise ValueError("O campeonato precisa de pelo menos dois times.")
        if len({team.name for team in self.teams}) != len(self.teams):
            raise ValueError("Nao pode haver times repetidos no campeonato.")
        if self.season_year < 1900:
            raise ValueError("Ano da temporada invalido.")

    def generate_round_robin_fixtures(self, double_round: bool = True, seed: int | None = None) -> None:
        """Gera a tabela completa de todos contra todos com rodadas ordenadas (Circle Method)."""

        from garfoot.domain.round_robin import generate_round_robin_schedule

        team_names = [team.name for team in self.teams]
        self.fixtures = generate_round_robin_schedule(team_names, double_round=double_round, seed=seed)

    def standings(self) -> list[LeagueStanding]:
        table = {team.name: LeagueStanding(team.name) for team in self.teams}

        for fixture in self.fixtures:
            if fixture.status != MatchStatus.PLAYED:
                continue
            if fixture.home_goals is None or fixture.away_goals is None:
                continue

            table[fixture.home_team].apply_match(fixture.home_goals, fixture.away_goals)
            table[fixture.away_team].apply_match(fixture.away_goals, fixture.home_goals)

        return sorted(
            table.values(),
            key=lambda standing: (
                standing.points,
                standing.wins,
                standing.goal_difference,
                standing.goals_for,
                standing.team_name,
            ),
            reverse=True,
        )

    def next_fixture(self) -> MatchFixture | None:
        return next(
            (fixture for fixture in self.fixtures if fixture.status == MatchStatus.SCHEDULED),
            None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "season_year": self.season_year,
            "teams": [team.to_dict() for team in self.teams],
            "fixtures": [fixture.to_dict() for fixture in self.fixtures],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Championship":
        payload = dict(data)
        payload["teams"] = [
            Team.from_dict(team_data)
            for team_data in payload.get("teams", [])
        ]
        payload["fixtures"] = [
            MatchFixture.from_dict(fixture_data)
            for fixture_data in payload.get("fixtures", [])
        ]
        return cls(**payload)  # type: ignore[arg-type]
