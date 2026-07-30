"""Modelo de configurações do jogo, velocidade e som."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class MatchSpeed(StrEnum):
    """Opções de velocidade da simulação ao vivo de partidas (apenas para exibição em UI)."""

    SLOW = "lenta"
    NORMAL = "normal"
    FAST = "rapida"
    INSTANT = "instantanea"

    @property
    def delay_seconds(self) -> float:
        """Mapeia cada opção para o delay em segundos entre ticks na UI."""

        if self == MatchSpeed.SLOW:
            return 0.45
        if self == MatchSpeed.FAST:
            return 0.08
        if self == MatchSpeed.INSTANT:
            return 0.0
        return 0.25  # MatchSpeed.NORMAL


class SoundMode(StrEnum):
    """Modos de áudio da UI."""

    DISABLED = "desligado"
    BEEP = "beep"
    WAV = "wav"


@dataclass(slots=True)
class GameSettings:
    """Configurações e preferências do jogador persistidas no save."""

    match_speed: MatchSpeed = MatchSpeed.NORMAL
    sound_enabled: bool = True
    sound_mode: SoundMode = SoundMode.BEEP

    def to_dict(self) -> dict[str, Any]:
        """Serializa as configurações para JSON."""

        return {
            "match_speed": self.match_speed.value,
            "sound_enabled": self.sound_enabled,
            "sound_mode": self.sound_mode.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> GameSettings:
        """Reconstrói as configurações do save, com fallback seguro para saves antigos."""

        if not data or not isinstance(data, dict):
            return cls()

        raw_speed = str(data.get("match_speed", MatchSpeed.NORMAL.value))
        try:
            speed = MatchSpeed(raw_speed)
        except ValueError:
            speed = MatchSpeed.NORMAL

        sound_enabled = bool(data.get("sound_enabled", True))
        raw_sound_mode = str(data.get("sound_mode", SoundMode.BEEP.value))
        try:
            sound_mode = SoundMode(raw_sound_mode)
        except ValueError:
            sound_mode = SoundMode.BEEP

        return cls(
            match_speed=speed,
            sound_enabled=sound_enabled,
            sound_mode=sound_mode,
        )
