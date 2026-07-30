"""Narração textual para eventos de partida."""

from __future__ import annotations

from random import Random

from garfoot.engine.events import (
    CardEvent,
    CardType,
    GoalEvent,
    InjuryEvent,
    MatchEvent,
    MissedChanceEvent,
    ShotEvent,
)
from garfoot.engine.match_engine import MatchResult


DEFAULT_SEED = 0


GOAL_WITH_ASSIST_TEMPLATES = [
    "{minute}' GOL DO {team}! {player} aparece na hora certa. Passe de {assist}.",
    "{minute}' GOOOOOL! {player} conclui para o {team}. Assistência de {assist}.",
    "{minute}' É rede! {assist} serve, {player} bate e marca para o {team}!",
]

GOAL_TEMPLATES = [
    "{minute}' GOL DO {team}! {player} bate firme e manda para o fundo da rede!",
    "{minute}' GOOOOOL! {player} decide a jogada e marca para o {team}!",
    "{minute}' É rede! {player} conclui para o {team} e levanta a torcida!",
    "{minute}' Gol do {team}! {player} não desperdiça e muda o placar!",
]

SHOT_ON_TARGET_TEMPLATES = [
    "{minute}' {player} bate pelo {team}, mas o goleiro encaixa.",
    "{minute}' Boa tentativa de {player}! Defesa segura no centro do gol.",
    "{minute}' {team} finaliza com {player}. O goleiro trabalha bem.",
    "{minute}' Chute de {player}, do {team}. Defesa firme.",
]

SHOT_OFF_TARGET_TEMPLATES = [
    "{minute}' {player} arrisca pelo {team}... para fora.",
    "{minute}' Chute de {player}. A bola sobe demais e sai sem perigo.",
    "{minute}' {team} chega com {player}, mas a finalização vai pela linha de fundo.",
    "{minute}' {player} tenta de longe para o {team}. Sem direção.",
]

YELLOW_CARD_TEMPLATES = [
    "{minute}' Cartão amarelo para {player}, do {team}. Entrada dura.",
    "{minute}' O árbitro chama {player} e mostra o amarelo.",
    "{minute}' {player} exagera na disputa. Amarelo para o {team}.",
]

RED_CARD_TEMPLATES = [
    "{minute}' Cartão vermelho! {player} está expulso do {team}.",
    "{minute}' O árbitro não perdoa: vermelho direto para {player}.",
    "{minute}' {team} fica com um a menos. {player} recebe o vermelho.",
]

INJURY_TEMPLATES = [
    "{minute}' {player} sente a perna e cai no gramado. Atendimento para o {team}.",
    "{minute}' Preocupação no {team}: {player} pede atendimento. Lesão {severity}.",
    "{minute}' {player} não parece bem depois da dividida. O jogo para por instantes.",
]

MISSED_CHANCE_ON_TARGET_TEMPLATES = [
    "{minute}' Chance clara para o {team}! {player} bate, mas o goleiro salva.",
    "{minute}' Que defesa! {player} tinha boa chance para o {team}.",
    "{minute}' {team} quase marca com {player}. O goleiro evita o gol.",
]

MISSED_CHANCE_OFF_TARGET_TEMPLATES = [
    "{minute}' Chance clara para o {team}! {player} tinha tudo para marcar, mas desperdiça.",
    "{minute}' Inacreditável! {player} recebe livre e não consegue fazer o gol.",
    "{minute}' {team} perde grande oportunidade com {player}. Essa fez falta.",
]


def narrate_event(event: MatchEvent, seed: int | None = None) -> str:
    """Retorna uma linha narrativa para um único evento."""

    return _narrate_event(event, Random(seed if seed is not None else DEFAULT_SEED))


def narrate_match(result: MatchResult, seed: int | None = None) -> list[str]:
    """Retorna a narração completa de uma partida simulada.

    O parâmetro ``seed`` controla apenas a escolha das frases, não altera o
    resultado da partida nem os eventos recebidos do motor.
    """

    random = Random(seed)
    lines = [
        f"0' Começa a partida: {result.home_team_name} x {result.away_team_name}. Bola rolando."
    ]
    lines.extend(_narrate_event(event, random) for event in result.events)
    lines.append(
        f"90' Fim de jogo: {result.home_team_name} {result.home_score} x "
        f"{result.away_score} {result.away_team_name}."
    )
    return lines


def narrate_summary(result: MatchResult) -> str:
    """Retorna ficha técnica curta de fim de partida."""

    scorers = _goal_scorers(result.events)
    scorers_text = ", ".join(scorers) if scorers else "sem gols"
    return (
        f"Resumo: {result.home_team_name} {result.home_score} x "
        f"{result.away_score} {result.away_team_name}. "
        f"Chutes: {result.shots_home} a {result.shots_away}. "
        f"Cartões: {result.cards_home} a {result.cards_away}. "
        f"Gols: {scorers_text}."
    )


def _narrate_event(event: MatchEvent, random: Random) -> str:
    if isinstance(event, GoalEvent):
        return _narrate_goal(event, random)
    if isinstance(event, ShotEvent):
        return _narrate_shot(event, random)
    if isinstance(event, CardEvent):
        return _narrate_card(event, random)
    if isinstance(event, InjuryEvent):
        return _narrate_injury(event, random)
    if isinstance(event, MissedChanceEvent):
        return _narrate_missed_chance(event, random)
    return f"{event.minute}' Lance registrado para {event.team_name}."


def _narrate_goal(event: GoalEvent, random: Random) -> str:
    if event.assisted_by is not None:
        template = random.choice(GOAL_WITH_ASSIST_TEMPLATES)
        return template.format(
            minute=event.minute,
            team=event.team_name,
            player=event.player_name,
            assist=event.assisted_by,
        )

    template = random.choice(GOAL_TEMPLATES)
    return template.format(
        minute=event.minute,
        team=event.team_name,
        player=event.player_name,
    )


def _narrate_shot(event: ShotEvent, random: Random) -> str:
    templates = SHOT_ON_TARGET_TEMPLATES if event.on_target else SHOT_OFF_TARGET_TEMPLATES
    return random.choice(templates).format(
        minute=event.minute,
        team=event.team_name,
        player=event.player_name,
    )


def _narrate_card(event: CardEvent, random: Random) -> str:
    templates = (
        YELLOW_CARD_TEMPLATES
        if event.card_type == CardType.YELLOW
        else RED_CARD_TEMPLATES
    )
    return random.choice(templates).format(
        minute=event.minute,
        team=event.team_name,
        player=event.player_name,
    )


def _narrate_injury(event: InjuryEvent, random: Random) -> str:
    return random.choice(INJURY_TEMPLATES).format(
        minute=event.minute,
        team=event.team_name,
        player=event.player_name,
        severity=event.severity,
    )


def _narrate_missed_chance(event: MissedChanceEvent, random: Random) -> str:
    templates = (
        MISSED_CHANCE_ON_TARGET_TEMPLATES
        if event.on_target
        else MISSED_CHANCE_OFF_TARGET_TEMPLATES
    )
    return random.choice(templates).format(
        minute=event.minute,
        team=event.team_name,
        player=event.player_name,
    )


def _goal_scorers(events: tuple[MatchEvent, ...]) -> list[str]:
    return [
        f"{event.player_name} ({event.team_name})"
        for event in events
        if isinstance(event, GoalEvent)
    ]
