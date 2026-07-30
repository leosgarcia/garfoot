"""Módulo puro de estatísticas de jogadores e treinadores para rankings e premiações."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from garfoot.domain.team import Team
from garfoot.engine.events import GoalEvent
from garfoot.engine.match_engine import MatchResult


@dataclass(slots=True)
class PlayerSeasonStats:
    """Estatísticas acumuladas de um jogador na temporada/competição."""

    player_name: str
    team_name: str
    competition: str
    goals: int = 0
    appearances: int = 0
    age: int = 25
    overall: int = 60

    @property
    def goals_per_game(self) -> float:
        return round(self.goals / self.appearances, 2) if self.appearances > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PlayerSeasonStats:
        return cls(
            player_name=str(data["player_name"]),
            team_name=str(data["team_name"]),
            competition=str(data["competition"]),
            goals=int(data.get("goals", 0)),
            appearances=int(data.get("appearances", 0)),
            age=int(data.get("age", 25)),
            overall=int(data.get("overall", 60)),
        )


@dataclass(slots=True)
class CoachSeasonStats:
    """Estatísticas acumuladas de um treinador na temporada/competição."""

    coach_name: str
    team_name: str | None
    competition: str | None
    matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    titles: int = 0
    sackings: int = 0
    reputation: int = 50

    @property
    def points(self) -> int:
        return self.wins * 3 + self.draws

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def win_percentage(self) -> float:
        return round((self.points / (self.matches * 3)) * 100.0, 1) if self.matches > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoachSeasonStats:
        return cls(
            coach_name=str(data["coach_name"]),
            team_name=data.get("team_name"),
            competition=data.get("competition"),
            matches=int(data.get("matches", 0)),
            wins=int(data.get("wins", 0)),
            draws=int(data.get("draws", 0)),
            losses=int(data.get("losses", 0)),
            goals_for=int(data.get("goals_for", 0)),
            goals_against=int(data.get("goals_against", 0)),
            titles=int(data.get("titles", 0)),
            sackings=int(data.get("sackings", 0)),
            reputation=int(data.get("reputation", 50)),
        )


@dataclass(slots=True)
class SeasonStatisticsManager:
    """Gerenciador de estatísticas acumuladas de toda a temporada."""

    player_stats: dict[str, PlayerSeasonStats] = field(default_factory=dict)
    coach_stats: dict[str, CoachSeasonStats] = field(default_factory=dict)

    def record_goal(
        self,
        player_name: str,
        team_name: str,
        competition: str,
        age: int = 25,
        overall: int = 60,
    ) -> None:
        """Registra um gol marcado por um jogador em uma competição."""

        key = f"{player_name}::{competition}"
        if key not in self.player_stats:
            self.player_stats[key] = PlayerSeasonStats(
                player_name=player_name,
                team_name=team_name,
                competition=competition,
                goals=0,
                appearances=1,
                age=age,
                overall=overall,
            )

        self.player_stats[key].goals += 1

    def record_match_player_appearances(
        self,
        starters: tuple[str, ...],
        team: Team,
        competition: str,
    ) -> None:
        """Registra a presença dos titulares de uma partida."""

        for name in starters:
            p = team.find_player(name)
            age = p.age if p else 25
            ovr = p.overall if p else 60
            key = f"{name}::{competition}"
            if key not in self.player_stats:
                self.player_stats[key] = PlayerSeasonStats(
                    player_name=name,
                    team_name=team.name,
                    competition=competition,
                    goals=0,
                    appearances=1,
                    age=age,
                    overall=ovr,
                )
            else:
                self.player_stats[key].appearances += 1

    def record_match_coach_result(
        self,
        coach_name: str,
        team_name: str,
        competition: str,
        goals_for: int,
        goals_against: int,
        reputation: int = 50,
    ) -> None:
        """Registra o resultado de uma partida para o treinador."""

        key = f"{coach_name}::{competition}"
        if key not in self.coach_stats:
            self.coach_stats[key] = CoachSeasonStats(
                coach_name=coach_name,
                team_name=team_name,
                competition=competition,
                reputation=reputation,
            )

        st = self.coach_stats[key]
        st.matches += 1
        st.goals_for += goals_for
        st.goals_against += goals_against

        if goals_for > goals_against:
            st.wins += 1
        elif goals_against > goals_for:
            st.losses += 1
        else:
            st.draws += 1

    def build_top_scorers_ranking(
        self,
        competition: str | None = None,
        limit: int = 20,
    ) -> list[PlayerSeasonStats]:
        """Gera o ranking de artilheiros agrupado ou filtrado por competição.

        Ordenação: Gols DESC, Partidas ASC, Média Gols DESC, Overall DESC, Nome ASC.
        """

        if competition:
            candidates = [st for st in self.player_stats.values() if st.competition == competition and st.goals > 0]
        else:
            # Agrupa estatísticas gerais por jogador de todas as competições
            grouped: dict[str, PlayerSeasonStats] = {}
            for st in self.player_stats.values():
                if st.goals <= 0:
                    continue
                if st.player_name not in grouped:
                    grouped[st.player_name] = PlayerSeasonStats(
                        player_name=st.player_name,
                        team_name=st.team_name,
                        competition="GERAL",
                        goals=st.goals,
                        appearances=st.appearances,
                        age=st.age,
                        overall=st.overall,
                    )
                else:
                    g = grouped[st.player_name]
                    g.goals += st.goals
                    g.appearances += st.appearances

            candidates = list(grouped.values())

        sorted_list = sorted(
            candidates,
            key=lambda x: (
                x.goals,
                -x.appearances,
                x.goals_per_game,
                x.overall,
                x.player_name,
            ),
            reverse=True,
        )
        return sorted_list[:limit]

    def build_coach_ranking(
        self,
        competition: str | None = None,
        limit: int = 20,
    ) -> list[CoachSeasonStats]:
        """Gera o ranking de treinadores por desempenho e aproveitamento.

        Ordenação: Aproveitamento DESC, Vitórias DESC, Saldo DESC, Derrotas ASC, Reputação DESC, Nome ASC.
        """

        if competition:
            candidates = [st for st in self.coach_stats.values() if st.competition == competition and st.matches > 0]
        else:
            grouped: dict[str, CoachSeasonStats] = {}
            for st in self.coach_stats.values():
                if st.matches <= 0:
                    continue
                if st.coach_name not in grouped:
                    grouped[st.coach_name] = CoachSeasonStats(
                        coach_name=st.coach_name,
                        team_name=st.team_name,
                        competition="GERAL",
                        matches=st.matches,
                        wins=st.wins,
                        draws=st.draws,
                        losses=st.losses,
                        goals_for=st.goals_for,
                        goals_against=st.goals_against,
                        titles=st.titles,
                        sackings=st.sackings,
                        reputation=st.reputation,
                    )
                else:
                    g = grouped[st.coach_name]
                    g.matches += st.matches
                    g.wins += st.wins
                    g.draws += st.draws
                    g.losses += st.losses
                    g.goals_for += st.goals_for
                    g.goals_against += st.goals_against

            candidates = list(grouped.values())

        sorted_list = sorted(
            candidates,
            key=lambda x: (
                x.win_percentage,
                x.wins,
                x.goal_difference,
                -x.losses,
                x.reputation,
                x.coach_name,
            ),
            reverse=True,
        )
        return sorted_list[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_stats": {k: v.to_dict() for k, v in self.player_stats.items()},
            "coach_stats": {k: v.to_dict() for k, v in self.coach_stats.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SeasonStatisticsManager:
        if not data or not isinstance(data, dict):
            return cls()

        p_stats = {
            k: PlayerSeasonStats.from_dict(v)
            for k, v in data.get("player_stats", {}).items()
            if isinstance(v, dict)
        }
        c_stats = {
            k: CoachSeasonStats.from_dict(v)
            for k, v in data.get("coach_stats", {}).items()
            if isinstance(v, dict)
        }

        return cls(player_stats=p_stats, coach_stats=c_stats)


def record_match_result_statistics(
    mgr: SeasonStatisticsManager,
    result: MatchResult,
    competition_name: str,
    home_team: Team,
    away_team: Team,
) -> None:
    """Função auxiliar pura para registrar gols, presenças e estatísticas de técnicos após uma partida."""

    # 1. Registra presenças dos titulares
    mgr.record_match_player_appearances(result.starters_home, home_team, competition_name)
    mgr.record_match_player_appearances(result.starters_away, away_team, competition_name)

    # 2. Registra gols de cada jogador
    for event in result.events:
        if isinstance(event, GoalEvent):
            team_obj = home_team if event.team_name == home_team.name else away_team
            p_obj = team_obj.find_player(event.player_name)
            age = p_obj.age if p_obj else 25
            ovr = p_obj.overall if p_obj else 60
            mgr.record_goal(
                player_name=event.player_name,
                team_name=event.team_name,
                competition=competition_name,
                age=age,
                overall=ovr,
            )

    # 3. Registra estatísticas dos treinadores se existirem
    if home_team.coach:
        mgr.record_match_coach_result(
            coach_name=home_team.coach.name,
            team_name=home_team.name,
            competition=competition_name,
            goals_for=result.home_score,
            goals_against=result.away_score,
            reputation=home_team.coach.reputation,
        )

    if away_team.coach:
        mgr.record_match_coach_result(
            coach_name=away_team.coach.name,
            team_name=away_team.name,
            competition=competition_name,
            goals_for=result.away_score,
            goals_against=result.home_score,
            reputation=away_team.coach.reputation,
        )
