"""Regras de fim de temporada entre series nacionais."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from garfoot.domain.league import LeagueStanding


class LeagueTier(StrEnum):
    """Series nacionais modeladas para acesso e rebaixamento."""

    SERIE_A = "A"
    SERIE_B = "B"
    SERIE_C = "C"
    SERIE_D = "D"


@dataclass(frozen=True, slots=True)
class NextSeasonComposition:
    """Composicao das series para a temporada seguinte."""

    serie_a: tuple[str, ...]
    serie_b: tuple[str, ...]
    serie_c: tuple[str, ...]
    serie_d: tuple[str, ...]


def apply_promotion_relegation(
    serie_a_standings: list[LeagueStanding],
    serie_b_standings: list[LeagueStanding],
    serie_c_standings: list[LeagueStanding],
    serie_d_standings: list[LeagueStanding],
) -> NextSeasonComposition:
    """Aplica acesso e rebaixamento ao fim da temporada entre as 4 series.

    As tabelas devem chegar ordenadas do melhor para o pior, normalmente pelo
    criterio de ``Championship.standings()``: pontos, vitorias, saldo de gols,
    gols pro e nome do time, todos em ordem decrescente. Isso significa que,
    em empates totais hipoteticos, ``team_name`` tambem e decrescente, nao
    alfabetico crescente; esta funcao apenas respeita esse criterio existente.

    Regras de acesso e rebaixamento (4 times por divisa):

    - nova Serie A  = Serie A (sem os 4 ultimos) + 4 primeiros da Serie B
    - nova Serie B  = Serie B (sem 4 primeiros e sem 4 ultimos)
                      + 4 ultimos da Serie A
                      + 4 primeiros da Serie C
    - nova Serie C  = Serie C (sem 4 primeiros e sem 4 ultimos)
                      + 4 ultimos da Serie B
                      + 4 primeiros da Serie D
    - nova Serie D  = Serie D (sem os 4 primeiros)
                      + 4 ultimos da Serie C
      (os 4 piores da Serie D permanecem; nao ha quinta divisao modelada)
    """

    _validate_standings(LeagueTier.SERIE_A, serie_a_standings)
    _validate_standings(LeagueTier.SERIE_B, serie_b_standings)
    _validate_standings(LeagueTier.SERIE_C, serie_c_standings)
    _validate_standings(LeagueTier.SERIE_D, serie_d_standings)

    # --- Serie A ---
    serie_a_relegated = serie_a_standings[-4:]       # 4 piores: descem para B
    serie_b_promoted  = serie_b_standings[:4]        # 4 melhores da B: sobem para A

    # --- Serie B ---
    serie_b_relegated = serie_b_standings[-4:]       # 4 piores: descem para C
    serie_c_promoted  = serie_c_standings[:4]        # 4 melhores da C: sobem para B

    # --- Serie C ---
    serie_c_relegated = serie_c_standings[-4:]       # 4 piores: descem para D
    serie_d_promoted  = serie_d_standings[:4]        # 4 melhores da D: sobem para C

    # Monta as composicoes da proxima temporada preservando a ordem interna
    # de cada grupo (do melhor para o pior, dentro de cada bloco)
    next_serie_a = (
        _team_names(serie_a_standings[:-4])   # permanentes da A
        + _team_names(serie_b_promoted)        # recém-promovidos da B
    )

    next_serie_b = (
        _team_names(serie_b_standings[4:-4])  # permanentes da B
        + _team_names(serie_a_relegated)       # recém-rebaixados da A
        + _team_names(serie_c_promoted)        # recém-promovidos da C
    )

    next_serie_c = (
        _team_names(serie_c_standings[4:-4])  # permanentes da C
        + _team_names(serie_b_relegated)       # recém-rebaixados da B
        + _team_names(serie_d_promoted)        # recém-promovidos da D
    )

    next_serie_d = (
        _team_names(serie_d_standings[4:])    # permanentes da D (4 piores ficam)
        + _team_names(serie_c_relegated)       # recém-rebaixados da C
    )

    return NextSeasonComposition(
        serie_a=next_serie_a,
        serie_b=next_serie_b,
        serie_c=next_serie_c,
        serie_d=next_serie_d,
    )


def _team_names(standings: list[LeagueStanding]) -> tuple[str, ...]:
    return tuple(standing.team_name for standing in standings)


def _validate_standings(tier: LeagueTier, standings: list[LeagueStanding]) -> None:
    if len(standings) < 4:
        raise ValueError(
            f"{tier.value} precisa ter pelo menos 4 times na tabela final; "
            f"recebeu {len(standings)}."
        )
