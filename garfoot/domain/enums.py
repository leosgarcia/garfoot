"""Enums compartilhados pelos modelos do jogo."""

from __future__ import annotations

from enum import StrEnum


class PlayerPosition(StrEnum):
    """Posicoes basicas para manter a primeira versao simples."""

    GOALKEEPER = "goleiro"
    DEFENDER = "defensor"
    MIDFIELDER = "meio-campo"
    FORWARD = "atacante"


class MatchStatus(StrEnum):
    """Estado de uma partida dentro do calendario."""

    SCHEDULED = "agendada"
    PLAYED = "jogada"
