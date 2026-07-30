"""Orquestração completa da temporada (Séries A/B/C + Copa do Brasil + Super Campeão)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from garfoot.domain.cup import CupMatch, KnockoutCup
from garfoot.domain.league import Championship, MatchFixture
from garfoot.domain.season import LeagueTier
from garfoot.domain.stable_random import combine_seed


@dataclass(frozen=True, slots=True)
class SuperChampionMatchup:
    """Confronto final da partida de Super Campeão."""

    home_team: str
    away_team: str
    is_double_winner_rule_applied: bool


def determine_super_champion_matchup(
    serie_a_champion: str,
    serie_a_runner_up: str,
    copa_brasil_champion: str,
) -> SuperChampionMatchup:
    """Determina puramente os dois participantes do jogo do Super Campeão.

    Regra:
    - Se o campeão da Série A for o mesmo campeão da Copa do Brasil (dobradinha),
      a segunda vaga fica com o vice-campeão da Série A.
    - Caso contrário, enfrentam-se o campeão da Série A x campeão da Copa do Brasil.
    """

    if serie_a_champion == copa_brasil_champion:
        return SuperChampionMatchup(
            home_team=serie_a_champion,
            away_team=serie_a_runner_up,
            is_double_winner_rule_applied=True,
        )

    return SuperChampionMatchup(
        home_team=serie_a_champion,
        away_team=copa_brasil_champion,
        is_double_winner_rule_applied=False,
    )


@dataclass(slots=True)
class SeasonOrchestrator:
    """Orquestra as competições da temporada brasileira (Séries A/B/C, Copa e Super Campeão)."""

    season_year: int
    championships: dict[LeagueTier, Championship]
    copa_do_brasil: KnockoutCup
    super_champion_match: CupMatch | None = None

    def start_new_season(
        self,
        cbf_ranking: dict[str, int],
        seed: int | None = None,
    ) -> None:
        """Inicializa e gera os calendários de todas as ligas (A/B/C) e o chaveamento da Copa do Brasil."""

        for tier, champ in self.championships.items():
            champ_seed = combine_seed(seed, tier.value, namespace="league-schedule") if seed is not None else None
            champ.generate_round_robin_fixtures(double_round=True, seed=champ_seed)

        self.copa_do_brasil.generate_initial_bracket(cbf_ranking=cbf_ranking, seed=seed)

    def build_super_champion_match(self) -> CupMatch:
        """Monta o confronto do Super Campeão após a conclusão da Série A e da Copa do Brasil.

        Lança ValueError caso as competições ainda não estejam concluídas.
        """

        serie_a = self.championships.get(LeagueTier.SERIE_A)
        if serie_a is None:
            raise ValueError("Série A não está presente na temporada.")

        standings = serie_a.standings()
        if len(standings) < 2:
            raise ValueError("Série A precisa ter pelo menos dois times finalizados.")

        # Verifica se todas as partidas da Série A já foram jogadas
        if serie_a.next_fixture() is not None:
            raise ValueError("Série A ainda possui partidas pendentes.")

        serie_a_champ = standings[0].team_name
        serie_a_runner_up = standings[1].team_name

        copa_champ = self.copa_do_brasil.champion
        if copa_champ is None:
            raise ValueError("Copa do Brasil ainda não foi concluída.")

        matchup = determine_super_champion_matchup(
            serie_a_champion=serie_a_champ,
            serie_a_runner_up=serie_a_runner_up,
            copa_brasil_champion=copa_champ,
        )

        fixture = MatchFixture(
            round_number=99,
            home_team=matchup.home_team,
            away_team=matchup.away_team,
        )

        super_match = CupMatch(fixture=fixture)
        self.super_champion_match = super_match
        return super_match

    def to_dict(self) -> dict[str, Any]:
        return {
            "season_year": self.season_year,
            "championships": {
                tier.value: champ.to_dict()
                for tier, champ in self.championships.items()
            },
            "copa_do_brasil": self.copa_do_brasil.to_dict(),
            "super_champion_match": (
                self.super_champion_match.to_dict()
                if self.super_champion_match
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SeasonOrchestrator:
        championships = {
            LeagueTier(tier_str): Championship.from_dict(champ_data)
            for tier_str, champ_data in data.get("championships", {}).items()
        }
        copa = KnockoutCup.from_dict(data["copa_do_brasil"])
        super_match_data = data.get("super_champion_match")
        super_match = CupMatch.from_dict(super_match_data) if super_match_data else None

        return cls(
            season_year=data["season_year"],
            championships=championships,
            copa_do_brasil=copa,
            super_champion_match=super_match,
        )
