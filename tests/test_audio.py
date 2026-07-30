"""Testes automatizados para a camada de áudio da UI e sons de eventos de partida."""

import sys
from unittest.mock import MagicMock, patch
import pytest

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_settings import GameSettings, MatchSpeed, SoundMode
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.engine.events import CardEvent, CardType, GoalEvent, InjuryEvent, MissedChanceEvent
from garfoot.engine.match_engine import simulate_match
from garfoot.ui.audio import SoundEvent, map_engine_event_to_sound_event, play_ui_sound


def test_sound_settings_serialization_and_fallback():
    # 1. Defaults
    settings = GameSettings()
    assert settings.sound_enabled is True
    assert settings.sound_mode == SoundMode.BEEP

    # 2. to_dict & from_dict
    custom_settings = GameSettings(sound_enabled=False, sound_mode=SoundMode.DISABLED)
    serialized = custom_settings.to_dict()
    assert serialized["sound_enabled"] is False
    assert serialized["sound_mode"] == "desligado"

    deserialized = GameSettings.from_dict(serialized)
    assert deserialized.sound_enabled is False
    assert deserialized.sound_mode == SoundMode.DISABLED

    # 3. Fallback para saves antigos sem a chave de áudio
    data_old = {"match_speed": "rapida"}
    loaded_old = GameSettings.from_dict(data_old)
    assert loaded_old.match_speed == MatchSpeed.FAST
    assert loaded_old.sound_enabled is True
    assert loaded_old.sound_mode == SoundMode.BEEP


def test_engine_event_mapping_to_sound_event():
    # Gol -> GOAL
    g = GoalEvent(minute=10, team_name="Flamengo", player_name="Gabriel")
    assert map_engine_event_to_sound_event(g) == SoundEvent.GOAL

    # Cartão Amarelo -> YELLOW_CARD
    c1 = CardEvent(minute=20, team_name="Vasco", player_name="Nenê", card_type=CardType.YELLOW)
    assert map_engine_event_to_sound_event(c1) == SoundEvent.YELLOW_CARD

    # Cartão Vermelho -> RED_CARD
    c2 = CardEvent(minute=40, team_name="Vasco", player_name="Felipe", card_type=CardType.RED)
    assert map_engine_event_to_sound_event(c2) == SoundEvent.RED_CARD

    # Lesão -> INJURY
    inj = InjuryEvent(minute=30, team_name="Flamengo", player_name="Arrascaeta")
    assert map_engine_event_to_sound_event(inj) == SoundEvent.INJURY

    # Evento sem som mapeado (ex: chance perdida) -> None
    miss = MissedChanceEvent(minute=15, team_name="Flamengo", player_name="Pedro")
    assert map_engine_event_to_sound_event(miss) is None


def test_play_ui_sound_when_disabled():
    """Garante que com sons desligados a função retorna silenciosamente sem emitir áudio."""
    with patch("sys.stdout.write") as mock_write:
        play_ui_sound(SoundEvent.GOAL, sound_enabled=False, sound_mode=SoundMode.BEEP)
        play_ui_sound(SoundEvent.GOAL, sound_enabled=True, sound_mode=SoundMode.DISABLED)
        mock_write.assert_not_called()


def test_play_ui_sound_safe_fallback_on_internal_exception():
    """Garante que a função captura qualquer exceção interna sem quebrar a execução da UI."""
    with patch("sys.stdout.write", side_effect=OSError("Terminal de som indisponível")):
        # Não deve lançar nenhuma exceção
        play_ui_sound(SoundEvent.GOAL, sound_enabled=True, sound_mode=SoundMode.BEEP)


def test_play_ui_sound_with_textual_app_bell():
    """Testa que se o app do Textual possuir o método bell(), ele é preferido de forma limpa."""
    mock_app = MagicMock()
    play_ui_sound(SoundEvent.GOAL, sound_enabled=True, sound_mode=SoundMode.BEEP, app=mock_app)
    mock_app.bell.assert_called_once()


def test_engine_determinism_and_purity_unaffected_by_audio():
    """Garante que a engine de partida continue pura, sem dependência ou efeitos colaterais de áudio."""
    p1 = [Player(name=f"Home {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p2 = [Player(name=f"Away {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    from garfoot.domain.team import Team
    home = Team(name="Time A", city="Rio", budget=100, players=p1)
    away = Team(name="Time B", city="SP", budget=100, players=p2)

    res1 = simulate_match(home, away, seed=999)
    res2 = simulate_match(home, away, seed=999)

    assert res1.home_score == res2.home_score
    assert res1.away_score == res2.away_score
    assert len(res1.events) == len(res2.events)
