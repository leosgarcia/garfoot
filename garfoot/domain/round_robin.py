"""Algoritmo puro para geração de calendários de pontos corridos (Berger/Circle Method)."""

from __future__ import annotations

from random import Random

from garfoot.domain.league import MatchFixture


def generate_round_robin_schedule(
    team_names: list[str],
    double_round: bool = True,
    seed: int | None = None,
) -> list[MatchFixture]:
    """Gera o calendário completo de partidas com distribuição por rodadas.

    Para um número N de times (par):
    - Turno: N - 1 rodadas com N/2 jogos por rodada.
    - Returno: N - 1 rodadas invertendo exatamente o mando de campo do turno.
    - Cada time joga exatamente uma vez por rodada.
    """

    if len(team_names) < 2:
        raise ValueError("É necessário ter pelo menos 2 times para gerar o calendário.")

    teams = list(team_names)
    if seed is not None:
        Random(seed).shuffle(teams)

    # Se a quantidade de times for ímpar, adiciona um 'BYE' temporário para o cálculo
    has_bye = len(teams) % 2 != 0
    if has_bye:
        teams.append("BYE")

    num_teams = len(teams)
    num_rounds = num_teams - 1
    matches_per_round = num_teams // 2

    first_half_fixtures: list[MatchFixture] = []
    second_half_fixtures: list[MatchFixture] = []

    # Rotação de Berger: o elemento index 0 fica fixo, e o restante rotaciona
    rotation = list(teams)

    for r in range(num_rounds):
        round_num_turn = r + 1
        round_num_return = num_rounds + r + 1

        for i in range(matches_per_round):
            t1 = rotation[i]
            t2 = rotation[num_teams - 1 - i]

            if t1 == "BYE" or t2 == "BYE":
                continue

            # Alterne o mando de campo com base na rodada para equilibrar jogos em casa/fora
            if r % 2 == 0:
                home, away = t1, t2
            else:
                home, away = t2, t1

            # Adiciona confronto no turno
            first_half_fixtures.append(
                MatchFixture(round_number=round_num_turn, home_team=home, away_team=away)
            )

            if double_round:
                # Adiciona confronto equivalente no returno (inversão estrita de mando)
                second_half_fixtures.append(
                    MatchFixture(round_number=round_num_return, home_team=away, away_team=home)
                )

        # Rotaciona os times (index 0 fica fixo, move o último elemento para a posição 1)
        rotation = [rotation[0]] + [rotation[-1]] + rotation[1:-1]

    if double_round:
        return first_half_fixtures + second_half_fixtures
    return first_half_fixtures
