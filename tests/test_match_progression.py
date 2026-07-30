"""Testes unitários para a progressão de time pós-partida."""

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.engine.match_engine import simulate_match
from garfoot.engine.match_progression import apply_post_match_progression


def _make_team(name: str) -> Team:
    players = [
        Player(
            name=f"Jogador {i:02d}",
            age=25,
            position=PlayerPosition.MIDFIELDER if i > 2 else PlayerPosition.GOALKEEPER,
            attack=70,
            defense=70,
            fitness=80,
            morale=70,
            value=100_000,
        )
        for i in range(1, 14)
    ]
    return Team(name=name, city="Cidade", budget=100_000, players=players)


def test_apply_post_match_progression_fatigue_and_morale():
    home = _make_team("Flamengo")
    away = _make_team("Vasco")

    result = simulate_match(home, away, seed=42)
    assert len(result.starters_home) == 11
    assert len(result.starters_away) == 11

    new_home, new_away = apply_post_match_progression(home, away, result)

    # Titulares do Flamengo devem ter perdido fitness (80 -> 70 se não lesionado)
    home_starters_set = set(result.starters_home)
    for p in new_home.players:
        if p.name in home_starters_set:
            if p.is_injured:
                assert p.fitness < 70
            else:
                assert p.fitness == 70
        else:
            # Reservas descansam (80 -> 92)
            assert p.fitness == 92

    # Verifica moral do time vencedor/perdedor
    if result.home_score > result.away_score:
        # Flamengo venceu: titulares do Flamengo ganham moral
        st = next(p for p in new_home.players if p.name in home_starters_set)
        assert st.morale >= 74
