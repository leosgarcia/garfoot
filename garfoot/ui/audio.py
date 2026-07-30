"""Camada de áudio exclusiva da UI do Garfoot (delays, beeps e efeitos sonoros)."""

from __future__ import annotations

from enum import StrEnum
import sys
from typing import Any

from garfoot.domain.game_settings import SoundMode
from garfoot.engine.events import CardEvent, CardType, GoalEvent, InjuryEvent, MatchEvent


class SoundEvent(StrEnum):
    """Tipos de eventos de áudio disparados pela UI."""

    MATCH_START = "match_start"
    HALF_TIME = "half_time"
    SECOND_HALF_START = "second_half_start"
    FULL_TIME = "full_time"
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    PENALTY = "penalty"
    INJURY = "injury"


def map_engine_event_to_sound_event(event: MatchEvent) -> SoundEvent | None:
    """Mapeia puramente um evento vindo da engine de partida para um SoundEvent de UI."""

    if isinstance(event, GoalEvent):
        return SoundEvent.GOAL

    if isinstance(event, CardEvent):
        if event.card_type == CardType.RED:
            return SoundEvent.RED_CARD
        return SoundEvent.YELLOW_CARD

    if isinstance(event, InjuryEvent):
        return SoundEvent.INJURY

    return None


def play_ui_sound(
    event: SoundEvent,
    sound_enabled: bool = True,
    sound_mode: SoundMode = SoundMode.BEEP,
    app: Any = None,
) -> None:
    """Emite o som do evento de forma segura e silenciosa se o ambiente for incompatível.

    A camada de áudio pertence 100% à UI. Nunca lança exceções para não travar a partida.
    """

    if not sound_enabled or sound_mode == SoundMode.DISABLED:
        return

    try:
        # Se a aplicação Textual estiver ativa e possuir o método bell(), tenta utilizá-lo
        if app is not None and hasattr(app, "bell") and callable(app.bell):
            app.bell()
            return

        # Fallback padrão: Beep de terminal (\a)
        if sound_mode in (SoundMode.BEEP, SoundMode.WAV):
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        # Fallback silencioso absoluto: ignora falhas de áudio/terminal remotos/headless
        pass
