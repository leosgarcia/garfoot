"""Carregamento de dados e conversão para modelos de domínio para a UI."""

from __future__ import annotations

import json
from pathlib import Path
from random import Random
from typing import Any

from garfoot.domain.stable_random import stable_composite_seed, stable_int_seed

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "brazil_2026_clubs.json"

# Posições para os 16 jogadores gerados em elencos temporários
GENERATED_SQUAD_POSITIONS = (
    [PlayerPosition.GOALKEEPER] * 2
    + [PlayerPosition.DEFENDER] * 5
    + [PlayerPosition.MIDFIELDER] * 5
    + [PlayerPosition.FORWARD] * 4
)


# Tabela Oficial do Ranking Nacional de Clubes CBF (RNC 2026) para os 60 clubes do dataset
CBF_RANKING_2026: dict[str, int] = {
    # Série A (2026)
    "Clube de Regatas do Flamengo": 1,
    "Sport Club Corinthians Paulista": 2,
    "Sociedade Esportiva Palmeiras": 3,
    "Clube Atlético Mineiro": 4,
    "São Paulo Futebol Clube": 5,
    "Fluminense Football Club": 6,
    "Botafogo de Futebol e Regatas": 7,
    "Club Athletico Paranaense": 8,
    "Esporte Clube Bahia": 9,
    "Club de Regatas Vasco da Gama SAF": 10,
    "Cruzeiro Esporte Clube SAF": 11,
    "Grêmio Foot-Ball Porto Alegrense": 12,
    "Sport Club Internacional": 14,
    "Red Bull Bragantino": 15,
    "Santos Futebol Clube": 16,
    "Esporte Clube Vitória": 20,
    "Coritiba Foot Ball Club SAF": 24,
    "Mirassol Futebol Clube": 28,
    "Associação Chapecoense de Futebol": 33,
    "Clube do Remo": 37,
    # Série B (2026)
    "Fortaleza Esporte Clube SAF": 13,
    "Esporte Clube Juventude": 17,
    "Atlético Clube Goianiense SAF": 18,
    "América Futebol Clube": 19,
    "Ceará Sporting Club": 21,
    "Cuiabá Esporte Clube": 22,
    "Goiás Esporte Clube": 23,
    "Sport Club do Recife": 25,
    "Clube de Regatas Brasil": 26,
    "Criciúma Esporte Clube": 27,
    "Vila Nova Futebol Clube": 29,
    "Operário Ferroviário Esporte Clube": 30,
    "Avaí Futebol Clube": 31,
    "Grêmio Novorizontino SAF": 32,
    "Botafogo Futebol Clube": 34,
    "Associação Atlética Ponte Preta": 38,
    "Clube Náutico Capibaribe": 44,
    "Londrina Esporte Clube SAF": 48,
    "Athletic Club SAF": 51,
    "São Bernardo Futebol Clube SAF": 57,
    # Série C (2026)
    "Paysandu Sport Club": 35,
    "Brusque Futebol Clube": 36,
    "Amazonas Futebol Clube SAF": 40,
    "Ituano Futebol Clube": 41,
    "Volta Redonda Futebol Clube": 43,
    "Guarani Futebol Clube": 45,
    "Ypiranga Futebol Clube": 50,
    "Botafogo Futebol Clube SAF": 52,
    "Associação Desportiva Confiança SAF": 53,
    "Associação Ferroviária de Esportes": 54,
    "Maringá Futebol Clube SAF": 56,
    "Sociedade Esportiva e Recreativa Caxias do Sul": 58,
    "Figueirense Futebol Clube": 59,
    "Floresta Esporte Clube": 61,
    "Anápolis Futebol Clube": 69,
    "Itabaiana Associação Olímpica": 84,
    "Maranhão Atlético Clube": 85,
    "Santa Cruz Futebol Clube": 86,
    "Barra Futebol Clube": 99,
    "Associação Atlética Internacional de Limeira": 105,
}

SERIES_BONUS: dict[str, float] = {
    "A": 2.5,
    "B": 0.0,
    "C": -2.0,
    "D": -4.0,  # progressão de -2.0 por divisão: A=+2.5, B=0, C=-2, D=-4
}


def load_clubs() -> list[dict[str, Any]]:
    """Carrega os dicionários crus de clubes a partir do JSON."""

    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def clubs_by_series(clubs: list[dict[str, Any]], series: str) -> list[dict[str, Any]]:
    """Filtra lista de dicionários por série."""

    return [club for club in clubs if club.get("series") == series]


def load_teams() -> list[Team]:
    """Carrega todos os clubes do JSON e os converte em objetos Team do domínio."""

    clubs = load_clubs()
    teams: list[Team] = []

    for club_dict in clubs:
        target_overall = _calculate_target_overall(club_dict)
        team = _convert_club_dict_to_team(club_dict, target_overall)
        teams.append(team)

    return teams


def load_teams_by_series(series: str) -> list[Team]:
    """Carrega apenas os objetos Team de uma série específica.

    ``Team`` é uma entidade de domínio pura e não armazena a série de origem.
    Por isso, o filtro é aplicado no dicionário cru do JSON antes da conversão
    para ``Team``. Assim evitamos adicionar estado de UI ao domínio.
    """

    normalized_series = series.upper()
    teams: list[Team] = []
    for club_dict in clubs_by_series(load_clubs(), normalized_series):
        target_overall = _calculate_target_overall(club_dict)
        teams.append(_convert_club_dict_to_team(club_dict, target_overall))
    return teams


def _get_team_series(team: Team, series: str) -> bool:
    """Confere a série de um Team a partir do dataset original.

    Mantido como helper de compatibilidade para chamadas antigas. Como ``Team``
    não guarda a série, a origem confiável continua sendo o JSON.
    """

    normalized_series = series.upper()
    for club in load_clubs():
        if club.get("name") == team.name:
            return str(club.get("series", "")).upper() == normalized_series
    return False


def _calculate_target_overall(club_dict: dict[str, Any]) -> int:
    """Calcula o overall-alvo do clube com base no Ranking CBF 2026 e na Série do clube."""

    name = club_dict["name"]
    series = str(club_dict.get("series", "B"))

    # Posição no Ranking CBF (fallback para 100 se não estiver listado)
    rank = CBF_RANKING_2026.get(name, 100)

    # Fórmula Híbrida: Base = 86.0 - 0.28 * (rank - 1)
    base_ovr = 86.0 - 0.28 * (rank - 1)
    bonus = SERIES_BONUS.get(series, 0.0)

    final_ovr = round(base_ovr + bonus)
    return max(54, min(88, final_ovr))


def _convert_club_dict_to_team(club_dict: dict[str, Any], target_overall: int) -> Team:
    """Converte um dicionário de clube do JSON para a entidade Team."""

    name = club_dict["name"]
    city = club_dict.get("city", "Desconhecida")
    budget = club_dict.get("budget", 1_000_000)

    stadium_dict = club_dict.get("stadium")
    stadium = None
    if stadium_dict and isinstance(stadium_dict, dict):
        stadium = Stadium(
            name=stadium_dict.get("name", "Estádio"),
            city=stadium_dict.get("city", city),
            capacity=stadium_dict.get("capacity", 10_000),
        )

    raw_players = club_dict.get("players") or []
    players: list[Player] = []

    if raw_players:
        # Clube com elenco real no JSON
        for p_dict in raw_players:
            p_name = p_dict["name"]
            p_pos = PlayerPosition[p_dict["position"]]
            p_age = p_dict.get("age") or 24

            # Se contiver atributos completos de desempenho no JSON, usa-os
            if "attack" in p_dict and "defense" in p_dict:
                player = Player(
                    name=p_name,
                    age=p_age,
                    position=p_pos,
                    attack=p_dict["attack"],
                    defense=p_dict["defense"],
                    fitness=p_dict.get("fitness", target_overall),
                    morale=p_dict.get("morale", target_overall),
                    value=p_dict.get("value", target_overall * 10_000),
                )
            else:
                # Preenche atributos coerentes com o overall-alvo do clube
                player = _create_player_from_target(p_name, p_age, p_pos, target_overall, Random(stable_composite_seed((name, p_name), namespace="ui-data-player")))
            players.append(player)
    else:
        # Clube sem elenco real no JSON: gera elenco temporário baseado no ranking CBF
        rng = Random(stable_int_seed(name, namespace="ui-data-team"))
        for p_idx, pos in enumerate(GENERATED_SQUAD_POSITIONS, start=1):
            p_name = f"Jogador {p_idx:02d}"
            p_age = rng.randint(18, 34)
            # Variação individual em torno do overall-alvo do clube (ex: -3 a +3)
            player_ovr = max(1, min(100, target_overall + rng.randint(-3, 3)))
            player = _create_player_from_target(p_name, p_age, pos, player_ovr, rng)
            players.append(player)

    series = str(club_dict.get("series", "D"))
    raw_budget = club_dict.get("budget", 0)

    team = Team(
        name=name,
        city=city,
        budget=raw_budget if isinstance(raw_budget, int) and raw_budget > 0 else 0,
        players=players,
        stadium=stadium,
    )

    from garfoot.domain.club_finance import initialize_team_budget
    return initialize_team_budget(team, series=series)


def _create_player_from_target(
    name: str, age: int, position: PlayerPosition, target_ovr: int, rng: Random
) -> Player:
    """Cria um jogador distribuindo attack e defense conforme a posição."""

    if position == PlayerPosition.GOALKEEPER:
        def_val = target_ovr
        att_val = max(1, target_ovr - 40)
    elif position == PlayerPosition.DEFENDER:
        def_val = min(100, target_ovr + rng.randint(2, 6))
        att_val = max(1, target_ovr - rng.randint(15, 25))
    elif position == PlayerPosition.MIDFIELDER:
        def_val = target_ovr
        att_val = target_ovr
    else:  # FORWARD
        att_val = min(100, target_ovr + rng.randint(2, 6))
        def_val = max(1, target_ovr - rng.randint(15, 25))

    fitness = min(100, max(1, target_ovr + rng.randint(-5, 5)))
    morale = min(100, max(1, target_ovr + rng.randint(-5, 5)))
    val = target_ovr * 10_000

    return Player(
        name=name,
        age=age,
        position=position,
        attack=att_val,
        defense=def_val,
        fitness=fitness,
        morale=morale,
        value=val,
    )
