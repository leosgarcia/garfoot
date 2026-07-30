"""Testes unitários para o sistema de substituições de jogadores."""

import pytest

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.injury import Injury, InjurySeverity
from garfoot.domain.player import Player
from garfoot.domain.substitution import (
    TeamMatchLineupState,
    apply_substitution,
    can_substitute,
    suggest_cpu_substitution,
)
from garfoot.domain.team import Team
from garfoot.engine.events import SubstitutionReason
from garfoot.engine.match_engine import simulate_match


def _make_lineup_state() -> TeamMatchLineupState:
    pitch = [
        Player(name=f"Titular {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80)
        for i in range(11)
    ]
    bench = [
        Player(name=f"Reserva {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=55, defense=55, fitness=80, morale=80)
        for i in range(5)
    ]
    return TeamMatchLineupState(team_name="Time A", players_on_pitch=pitch, bench=bench)


def test_can_substitute_valid_and_invalid():
    state = _make_lineup_state()

    # Substituição válida
    ok, msg = can_substitute(state, "Titular 0", "Reserva 0")
    assert ok is True

    # Bloqueia jogador que não está em campo
    ok1, msg1 = can_substitute(state, "Reserva 0", "Reserva 1")
    assert ok1 is False
    assert "não está em campo" in msg1

    # Bloqueia reserva que não está no banco
    ok2, msg2 = can_substitute(state, "Titular 0", "Inexistente")
    assert ok2 is False
    assert "não está disponível no banco" in msg2


def test_can_substitute_blocked_for_injured_reserve():
    pitch = [Player(name=f"Titular {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    injured_bench_player = Player(
        name="Reserva Lesionado",
        age=20,
        position=PlayerPosition.FORWARD,
        attack=60,
        defense=60,
        fitness=30,
        morale=80,
        injury=Injury(severity=InjurySeverity.MODERATE, rounds_remaining=3),
    )
    state = TeamMatchLineupState(team_name="Time A", players_on_pitch=pitch, bench=[injured_bench_player])

    ok, msg = can_substitute(state, "Titular 0", "Reserva Lesionado")
    assert ok is False
    assert "lesionado e indisponível" in msg


def test_apply_substitution_updates_pitch_bench_history_and_limit():
    state = _make_lineup_state()
    assert state.remaining_substitutions == 5

    # 1ª Substituição
    new_state, event = apply_substitution(state, minute=60, player_out_name="Titular 0", player_in_name="Reserva 0")
    assert new_state.remaining_substitutions == 4
    assert event.player_out_name == "Titular 0"
    assert event.player_in_name == "Reserva 0"
    assert event.minute == 60
    assert new_state.find_player_on_pitch("Titular 0") is None
    assert new_state.find_player_on_pitch("Reserva 0") is not None

    # Bloqueia jogador substituído (Titular 0) tentando voltar a entrar
    ok, _ = can_substitute(new_state, "Titular 1", "Titular 0")
    assert ok is False


def test_limit_five_substitutions_max():
    state = _make_lineup_state()
    current = state

    for i in range(5):
        current, _ = apply_substitution(current, minute=50 + i, player_out_name=f"Titular {i}", player_in_name=f"Reserva {i}")

    assert current.remaining_substitutions == 0

    with pytest.raises(ValueError, match="Limite de substituições da equipe já foi atingido"):
        apply_substitution(current, minute=88, player_out_name="Titular 6", player_in_name="Reserva 0")


def test_cpu_suggests_substitution_for_injured_or_fatigued_player():
    pitch = [Player(name=f"Titular {i}", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    # Titular 0 está muito cansado (fitness = 30)
    pitch[0] = Player(name="Titular Cansado", age=22, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=30, morale=80)

    bench = [Player(name="Reserva 0", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80)]
    state = TeamMatchLineupState(team_name="Time CPU", players_on_pitch=pitch, bench=bench)

    cpu_res = suggest_cpu_substitution(state, minute=65)
    assert cpu_res is not None
    new_state, event = cpu_res

    assert event.player_out_name == "Titular Cansado"
    assert event.player_in_name == "Reserva 0"
    assert event.reason == SubstitutionReason.FITNESS
    assert new_state.find_player_on_pitch("Titular Cansado") is None


def test_simulation_determinism_and_substitutions_history():
    p1 = [Player(name=f"Home {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]
    p2 = [Player(name=f"Away {i}", age=20, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80) for i in range(11)]

    home = Team(name="Time A", city="Rio", budget=100, players=p1)
    away = Team(name="Time B", city="SP", budget=100, players=p2)

    res1 = simulate_match(home, away, seed=42)
    res2 = simulate_match(home, away, seed=42)

    assert res1.home_score == res2.home_score
    assert res1.away_score == res2.away_score
    assert res1.starters_home == res2.starters_home
