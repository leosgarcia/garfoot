"""Calculos puros de probabilidade para a simulacao de partidas."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Formation, Team


MIN_RATING = 1.0
NEUTRAL_FORMATION = Formation(4, 4, 2)
HOME_CONTROL_BONUS = 3.0

ATTACK_WEIGHTS = {
    PlayerPosition.GOALKEEPER: 0.05,
    PlayerPosition.DEFENDER: 0.35,
    PlayerPosition.MIDFIELDER: 0.75,
    PlayerPosition.FORWARD: 1.00,
}

DEFENSE_WEIGHTS = {
    PlayerPosition.GOALKEEPER: 1.00,
    PlayerPosition.DEFENDER: 1.00,
    PlayerPosition.MIDFIELDER: 0.65,
    PlayerPosition.FORWARD: 0.25,
}


@dataclass(frozen=True, slots=True)
class TeamMatchProfile:
    """Resumo numerico de um time para uma partida.

    Os ratings usam piso minimo para evitar divisoes por zero em elencos
    vazios ou dados carregados de forma incompleta. Se o time tiver menos de
    11 jogadores, o perfil usa todos os disponiveis; isso deixa prototipos e
    testes pequenos funcionarem, mas naturalmente gera um time mais limitado.
    """

    team_name: str
    starters: tuple[Player, ...]
    attack_rating: float
    defense_rating: float
    midfield_rating: float
    morale_avg: float
    fitness_avg: float
    is_home: bool


def select_starters(team: Team) -> tuple[Player, ...]:
    """Seleciona titulares para a simulacao.

    Se houver 11 nomes validos em ``starting_player_names``, eles sao usados.
    Caso contrario, entram os 11 melhores por overall. Elencos com menos de
    11 jogadores nao falham: todos os jogadores disponiveis sao usados.
    """

    players_by_name = {player.name: player for player in team.players}
    named_starters = [
        players_by_name[name]
        for name in team.starting_player_names
        if name in players_by_name
    ]

    if len(named_starters) == 11 and len({player.name for player in named_starters}) == 11:
        return tuple(named_starters)

    return tuple(
        sorted(team.players, key=lambda player: player.overall, reverse=True)[:11]
    )


def build_team_profile(team: Team, is_home: bool) -> TeamMatchProfile:
    """Calcula ratings de ataque, defesa e meio-campo para uma partida.

    A formacao e lida diretamente de ``team.formation``. Caso dados externos
    deixem a formacao ausente ou invalida, usa-se 4-4-2 como fallback neutro.
    O ``midfield_rating`` usa a media simples de ataque e defesa apenas dos
    meio-campistas, pois posse representa controle de jogo, nao so agressividade.
    """

    starters = select_starters(team)
    formation = _safe_formation(team)
    morale_avg = _average_attribute(starters, "morale")
    fitness_avg = _average_attribute(starters, "fitness")

    attack_rating = (
        _weighted_average(starters, "attack", ATTACK_WEIGHTS)
        + _formation_attack_bonus(formation)
    )
    defense_rating = (
        _weighted_average(starters, "defense", DEFENSE_WEIGHTS)
        + _formation_defense_bonus(formation)
    )

    attack_rating = _apply_condition_adjustment(attack_rating, fitness_avg, morale_avg)
    defense_rating = _apply_condition_adjustment(defense_rating, fitness_avg, morale_avg)

    # Aplica o bônus temporário de chicotada psicológica, se houver
    if getattr(team, "bounce_effect", None) and team.bounce_effect.is_active:
        bounce_mult = 1.0 + team.bounce_effect.rating_bonus
        attack_rating *= bounce_mult
        defense_rating *= bounce_mult

    if is_home:
        attack_rating *= 1.05
        defense_rating *= 1.03

    return TeamMatchProfile(
        team_name=team.name,
        starters=starters,
        attack_rating=max(MIN_RATING, attack_rating),
        defense_rating=max(MIN_RATING, defense_rating),
        midfield_rating=max(MIN_RATING, _midfield_rating(starters)),
        morale_avg=morale_avg,
        fitness_avg=fitness_avg,
        is_home=is_home,
    )


def calculate_possession(
    home: TeamMatchProfile,
    away: TeamMatchProfile,
) -> tuple[float, float]:
    """Calcula posse aproximada para casa e visitante.

    O retorno sempre soma 1.0. A posse do mandante e limitada entre 35% e 65%
    para evitar resultados extremos demais nesta primeira versao.
    """

    home_control = home.midfield_rating + home.morale_avg * 0.15 + HOME_CONTROL_BONUS
    away_control = away.midfield_rating + away.morale_avg * 0.15
    total_control = home_control + away_control

    if total_control <= 0:
        return 0.5, 0.5

    home_possession = _clamp(home_control / total_control, 0.35, 0.65)
    return home_possession, 1 - home_possession


def calculate_goal_chance(
    attacking: TeamMatchProfile,
    defending: TeamMatchProfile,
    shot_quality: float,
) -> float:
    """Calcula chance de gol dado que houve chute ou chance clara."""

    base_goal_rate = 0.10
    defense_rating = max(MIN_RATING, defending.defense_rating)
    goal_chance = (
        base_goal_rate
        * (attacking.attack_rating / defense_rating)
        * shot_quality
    )
    return _clamp(goal_chance, 0.03, 0.35)


def _safe_formation(team: Team) -> Formation:
    formation = getattr(team, "formation", None)
    if not isinstance(formation, Formation):
        return NEUTRAL_FORMATION
    if formation.defenders + formation.midfielders + formation.forwards != 10:
        return NEUTRAL_FORMATION
    if min(formation.defenders, formation.midfielders, formation.forwards) < 1:
        return NEUTRAL_FORMATION
    return formation


def _weighted_average(
    players: tuple[Player, ...],
    attribute_name: str,
    weights: dict[PlayerPosition, float],
) -> float:
    weighted_values = [
        getattr(player, attribute_name) * weights[player.position]
        for player in players
    ]
    total_weight = sum(weights[player.position] for player in players)
    if total_weight <= 0:
        return MIN_RATING
    return sum(weighted_values) / total_weight


def _average_attribute(players: tuple[Player, ...], attribute_name: str) -> float:
    if not players:
        return 50.0
    return mean(getattr(player, attribute_name) for player in players)


def _midfield_rating(players: tuple[Player, ...]) -> float:
    midfielders = [
        (player.attack + player.defense) / 2
        for player in players
        if player.position == PlayerPosition.MIDFIELDER
    ]
    if midfielders:
        return mean(midfielders)
    if not players:
        return MIN_RATING
    return mean((player.attack + player.defense) / 2 for player in players)


def _formation_attack_bonus(formation: Formation) -> float:
    return (formation.forwards - 2) * 3 + (formation.midfielders - 4)


def _formation_defense_bonus(formation: Formation) -> float:
    return (formation.defenders - 4) * 3 + (formation.midfielders - 4)


def _apply_condition_adjustment(
    rating: float,
    fitness_avg: float,
    morale_avg: float,
) -> float:
    fitness_factor = (fitness_avg - 50) / 50
    morale_factor = (morale_avg - 50) / 50
    return rating * (1 + fitness_factor * 0.08 + morale_factor * 0.06)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
