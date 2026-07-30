"""Estrutura e cálculo de premiações das competições e encerramento de temporada."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from garfoot.domain.statistics import SeasonStatisticsManager
from garfoot.domain.team import Team


class CompetitionType(StrEnum):
    """Competições com premiação modelada."""

    SERIE_A = "serie_a"
    SERIE_B = "serie_b"
    SERIE_C = "serie_c"
    SERIE_D = "serie_d"
    BRAZIL_CUP = "copa_do_brasil"
    SUPER_CHAMPION = "super_campeao"


class PrizeCategory(StrEnum):
    """Categorias de premiação por competição."""

    CHAMPION = "campeao"
    RUNNER_UP = "vice"
    TOP_SCORER = "artilheiro"
    GOLDEN_BOOT = "chuteira_de_ouro"


@dataclass(frozen=True, slots=True)
class CompetitionPrize:
    """Prêmios configurados para uma competição."""

    competition: CompetitionType
    prizes: dict[PrizeCategory, int]


@dataclass(slots=True)
class PrizeStructure:
    """Tabela de prêmios por competição e categoria."""

    competitions: dict[CompetitionType, CompetitionPrize]

    def prize_for(
        self,
        competition: CompetitionType,
        category: PrizeCategory,
    ) -> int:
        """Retorna o prêmio configurado, ou 0 se não existir."""

        competition_prize = self.competitions.get(competition)
        if competition_prize is None:
            return 0
        return competition_prize.prizes.get(category, 0)

    def set_prize(
        self,
        competition: CompetitionType,
        category: PrizeCategory,
        amount: int,
    ) -> None:
        """Define um prêmio, criando a competição se necessário."""

        if amount < 0:
            raise ValueError("O valor da premiação não pode ser negativo.")

        competition_prize = self.competitions.get(competition)
        if competition_prize is None:
            competition_prize = CompetitionPrize(competition, {})
            self.competitions[competition] = competition_prize

        competition_prize.prizes[category] = amount

    @classmethod
    def default_brazil_2026(cls) -> PrizeStructure:
        """Cria prêmios padrão para a temporada brasileira."""

        structure = cls(competitions={})
        defaults = {
            CompetitionType.SERIE_A: {
                PrizeCategory.CHAMPION: 12_000_000,
                PrizeCategory.RUNNER_UP: 6_000_000,
                PrizeCategory.TOP_SCORER: 1_000_000,
            },
            CompetitionType.SERIE_B: {
                PrizeCategory.CHAMPION: 5_000_000,
                PrizeCategory.RUNNER_UP: 2_500_000,
                PrizeCategory.TOP_SCORER: 500_000,
            },
            CompetitionType.SERIE_C: {
                PrizeCategory.CHAMPION: 2_000_000,
                PrizeCategory.RUNNER_UP: 1_000_000,
                PrizeCategory.TOP_SCORER: 250_000,
            },
            CompetitionType.SERIE_D: {
                PrizeCategory.CHAMPION: 800_000,
                PrizeCategory.RUNNER_UP: 400_000,
                PrizeCategory.TOP_SCORER: 150_000,
            },
            CompetitionType.BRAZIL_CUP: {
                PrizeCategory.CHAMPION: 10_000_000,
                PrizeCategory.RUNNER_UP: 5_000_000,
                PrizeCategory.TOP_SCORER: 800_000,
            },
            CompetitionType.SUPER_CHAMPION: {
                PrizeCategory.CHAMPION: 15_000_000,
                PrizeCategory.RUNNER_UP: 7_500_000,
                PrizeCategory.TOP_SCORER: 1_200_000,
            },
        }

        for competition, prizes in defaults.items():
            for category, amount in prizes.items():
                structure.set_prize(competition, category, amount)

        return structure


@dataclass(slots=True)
class SeasonAward:
    """Registro individual de um prêmio concedido ao final da temporada."""

    competition: str
    category: str
    team_name: str
    amount: int
    player_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SeasonAward:
        return cls(
            competition=str(data["competition"]),
            category=str(data["category"]),
            team_name=str(data["team_name"]),
            amount=int(data["amount"]),
            player_name=data.get("player_name"),
        )


@dataclass(slots=True)
class SeasonAwardsResult:
    """Resultado completo das premiações de uma temporada."""

    season_year: int
    awards: list[SeasonAward] = field(default_factory=list)
    applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "season_year": self.season_year,
            "awards": [a.to_dict() for a in self.awards],
            "applied": self.applied,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SeasonAwardsResult | None:
        if not data or not isinstance(data, dict):
            return None

        awards = [SeasonAward.from_dict(a) for a in data.get("awards", []) if isinstance(a, dict)]
        return cls(
            season_year=int(data.get("season_year", 2026)),
            awards=awards,
            applied=bool(data.get("applied", False)),
        )


def build_season_awards(
    season_year: int,
    championship_standings: dict[CompetitionType, list[tuple[str, int]]],  # [(team_name, pos)]
    copa_brasil_result: tuple[str, str] | None = None,  # (champion, runner_up)
    super_champion_result: tuple[str, str] | None = None,  # (champion, runner_up)
    stats_manager: SeasonStatisticsManager | None = None,
    prizes_structure: PrizeStructure | None = None,
    economic_context: Any | None = None,
) -> SeasonAwardsResult:
    """Calcula puramente as premiações finais da temporada, ajustadas pelo contexto econômico se fornecido."""

    prizes = prizes_structure or PrizeStructure.default_brazil_2026()
    awards: list[SeasonAward] = []

    def _adjust(val: int) -> int:
        if economic_context and hasattr(economic_context, "adjusted_value"):
            return economic_context.adjusted_value(val)
        return val

    # 1. Premiações por Série (A/B/C/D)
    for comp_type, standings in championship_standings.items():
        if len(standings) >= 1:
            champ_team = standings[0][0]
            val = _adjust(prizes.prize_for(comp_type, PrizeCategory.CHAMPION))
            awards.append(
                SeasonAward(
                    competition=comp_type.value.upper(),
                    category=PrizeCategory.CHAMPION.value,
                    team_name=champ_team,
                    amount=val,
                )
            )
        if len(standings) >= 2:
            runner_team = standings[1][0]
            val = _adjust(prizes.prize_for(comp_type, PrizeCategory.RUNNER_UP))
            awards.append(
                SeasonAward(
                    competition=comp_type.value.upper(),
                    category=PrizeCategory.RUNNER_UP.value,
                    team_name=runner_team,
                    amount=val,
                )
            )

    # 2. Copa do Brasil
    if copa_brasil_result:
        champ, runner = copa_brasil_result
        awards.append(
            SeasonAward(
                competition=CompetitionType.BRAZIL_CUP.value.upper(),
                category=PrizeCategory.CHAMPION.value,
                team_name=champ,
                amount=_adjust(prizes.prize_for(CompetitionType.BRAZIL_CUP, PrizeCategory.CHAMPION)),
            )
        )
        awards.append(
            SeasonAward(
                competition=CompetitionType.BRAZIL_CUP.value.upper(),
                category=PrizeCategory.RUNNER_UP.value,
                team_name=runner,
                amount=_adjust(prizes.prize_for(CompetitionType.BRAZIL_CUP, PrizeCategory.RUNNER_UP)),
            )
        )

    # 3. Super Campeão
    if super_champion_result:
        champ, runner = super_champion_result
        awards.append(
            SeasonAward(
                competition=CompetitionType.SUPER_CHAMPION.value.upper(),
                category=PrizeCategory.CHAMPION.value,
                team_name=champ,
                amount=_adjust(prizes.prize_for(CompetitionType.SUPER_CHAMPION, PrizeCategory.CHAMPION)),
            )
        )
        awards.append(
            SeasonAward(
                competition=CompetitionType.SUPER_CHAMPION.value.upper(),
                category=PrizeCategory.RUNNER_UP.value,
                team_name=runner,
                amount=_adjust(prizes.prize_for(CompetitionType.SUPER_CHAMPION, PrizeCategory.RUNNER_UP)),
            )
        )

    # 4. Artilheiro do Ano / Chuteira de Ouro
    if stats_manager:
        top_scorers = stats_manager.build_top_scorers_ranking(limit=1)
        if top_scorers:
            golden_boot_player = top_scorers[0]
            awards.append(
                SeasonAward(
                    competition="TEMPORADA",
                    category=PrizeCategory.GOLDEN_BOOT.value,
                    team_name=golden_boot_player.team_name,
                    amount=_adjust(1_000_000),
                    player_name=golden_boot_player.player_name,
                )
            )

    return SeasonAwardsResult(season_year=season_year, awards=awards, applied=False)


def apply_season_awards(
    teams: list[Team],
    awards_result: SeasonAwardsResult,
) -> tuple[list[Team], SeasonAwardsResult]:
    """Aplica o pagamento das premiações aos orçamentos dos clubes de forma idetempotente."""

    if awards_result.applied:
        return teams, awards_result

    teams_map = {t.name: t for t in teams}

    for award in awards_result.awards:
        if award.team_name in teams_map:
            teams_map[award.team_name].budget += award.amount

    # Marca como aplicado para evitar pagamento duplo em saves/carregamentos
    new_result = SeasonAwardsResult(
        season_year=awards_result.season_year,
        awards=awards_result.awards,
        applied=True,
    )

    return list(teams_map.values()), new_result
