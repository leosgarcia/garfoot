"""Testes unitários para o gerador de calendários de pontos corridos (round-robin)."""

from collections import Counter
import pytest

from garfoot.domain.round_robin import generate_round_robin_schedule


def test_round_robin_schedule_20_teams_properties():
    teams = [f"Time {i:02d}" for i in range(1, 21)]

    fixtures = generate_round_robin_schedule(teams, double_round=True)

    # 1. Total de jogos: 20 * 19 = 380 jogos
    assert len(fixtures) == 380

    # 2. Total de rodadas: 38 rodadas
    rounds = {f.round_number for f in fixtures}
    assert len(rounds) == 38
    assert min(rounds) == 1
    assert max(rounds) == 38

    # 3. Cada rodada deve ter exatamente 10 jogos e 20 times únicos
    by_round: dict[int, list] = {}
    for f in fixtures:
        by_round.setdefault(f.round_number, []).append(f)

    for r, r_fixtures in by_round.items():
        assert len(r_fixtures) == 10
        round_teams = set()
        for f in r_fixtures:
            round_teams.add(f.home_team)
            round_teams.add(f.away_team)
        assert len(round_teams) == 20  # Nenhum time joga 2 vezes na mesma rodada

    # 4. Mando de campo equilibrado: cada time joga 19 vezes em casa e 19 fora
    home_counts = Counter(f.home_team for f in fixtures)
    away_counts = Counter(f.away_team for f in fixtures)

    for team in teams:
        assert home_counts[team] == 19
        assert away_counts[team] == 19

    # 5. Inversão estrita no returno: confronto do turno R vira away x home na rodada R + 19
    r1_fixtures = { (f.home_team, f.away_team) for f in by_round[1] }
    r20_fixtures = { (f.home_team, f.away_team) for f in by_round[20] }

    for home, away in r1_fixtures:
        assert (away, home) in r20_fixtures


def test_round_robin_determinism_and_seed():
    teams = [f"Time {i:02d}" for i in range(1, 21)]

    # Sem seed / mesma ordem
    s1 = generate_round_robin_schedule(teams, double_round=True)
    s2 = generate_round_robin_schedule(teams, double_round=True)
    assert [(f.home_team, f.away_team) for f in s1] == [(f.home_team, f.away_team) for f in s2]

    # Com seed para embaralhar a ordem inicial
    s_seeded = generate_round_robin_schedule(teams, double_round=True, seed=42)
    assert [(f.home_team, f.away_team) for f in s1] != [(f.home_team, f.away_team) for f in s_seeded]
