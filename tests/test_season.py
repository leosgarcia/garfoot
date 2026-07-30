"""Testes unitários para regras de promoção/rebaixamento entre as 4 séries."""

import pytest

from garfoot.domain.league import LeagueStanding
from garfoot.domain.season import (
    LeagueTier,
    NextSeasonComposition,
    apply_promotion_relegation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _standings(names: list[str]) -> list[LeagueStanding]:
    """Cria uma tabela ordenada a partir de uma lista de nomes (melhor→pior)."""
    return [
        LeagueStanding(
            team_name=name,
            played=38,
            wins=0,
            draws=0,
            losses=38,
            goals_for=0,
            goals_against=0,
        )
        for name in names
    ]



def _make_series(n: int, prefix: str) -> list[LeagueStanding]:
    """Gera tabela com *n* times usando o prefixo dado (ex: 'A' -> 'A01'..'A20')."""
    return _standings([f"{prefix}{i:02d}" for i in range(1, n + 1)])


# ---------------------------------------------------------------------------
# LeagueTier
# ---------------------------------------------------------------------------

def test_league_tier_has_serie_d():
    assert LeagueTier.SERIE_D == "D"
    assert "D" in [t.value for t in LeagueTier]


def test_league_tier_all_four_series_present():
    values = {t.value for t in LeagueTier}
    assert values == {"A", "B", "C", "D"}


# ---------------------------------------------------------------------------
# NextSeasonComposition
# ---------------------------------------------------------------------------

def test_next_season_composition_has_serie_d_field():
    comp = NextSeasonComposition(
        serie_a=("T1",),
        serie_b=("T2",),
        serie_c=("T3",),
        serie_d=("T4",),
    )
    assert comp.serie_d == ("T4",)


# ---------------------------------------------------------------------------
# apply_promotion_relegation — caso padrão com 20 times por série
# ---------------------------------------------------------------------------

def test_promotion_relegation_sizes_standard():
    """Com 20 times por série, cada nova série deve ter exatamente 20 times."""
    result = apply_promotion_relegation(
        _make_series(20, "A"),
        _make_series(20, "B"),
        _make_series(20, "C"),
        _make_series(20, "D"),
    )

    assert len(result.serie_a) == 20
    assert len(result.serie_b) == 20
    assert len(result.serie_c) == 20
    assert len(result.serie_d) == 20


def test_promotion_relegation_serie_a_composition():
    """nova A = A sem 4 últimos + 4 primeiros da B."""
    a = _standings([f"A{i}" for i in range(1, 21)])   # A1..A20
    b = _standings([f"B{i}" for i in range(1, 21)])   # B1..B20
    c = _make_series(20, "C")
    d = _make_series(20, "D")

    result = apply_promotion_relegation(a, b, c, d)

    # Permanecem A1..A16 (sem rebaixados A17..A20)
    assert "A1" in result.serie_a
    assert "A16" in result.serie_a
    assert "A17" not in result.serie_a  # rebaixado
    assert "A20" not in result.serie_a  # rebaixado

    # Promovidos da B: B1..B4
    assert "B1" in result.serie_a
    assert "B4" in result.serie_a
    assert "B5" not in result.serie_a   # não subiu


def test_promotion_relegation_serie_b_composition():
    """nova B = B sem 4 primeiros e sem 4 últimos + rebaixados da A + promovidos da C."""
    a = _standings([f"A{i}" for i in range(1, 21)])
    b = _standings([f"B{i}" for i in range(1, 21)])
    c = _standings([f"C{i}" for i in range(1, 21)])
    d = _make_series(20, "D")

    result = apply_promotion_relegation(a, b, c, d)

    # Permanentes: B5..B16 (sem B1-B4 promovidos e sem B17-B20 rebaixados)
    assert "B5" in result.serie_b
    assert "B16" in result.serie_b
    assert "B1" not in result.serie_b   # subiu para A
    assert "B17" not in result.serie_b  # desceu para C

    # Rebaixados da A: A17..A20
    assert "A17" in result.serie_b
    assert "A20" in result.serie_b

    # Promovidos da C: C1..C4
    assert "C1" in result.serie_b
    assert "C4" in result.serie_b
    assert "C5" not in result.serie_b


def test_promotion_relegation_serie_c_composition():
    """nova C = C sem 4 primeiros e sem 4 últimos + rebaixados da B + promovidos da D."""
    a = _make_series(20, "A")
    b = _standings([f"B{i}" for i in range(1, 21)])
    c = _standings([f"C{i}" for i in range(1, 21)])
    d = _standings([f"D{i}" for i in range(1, 21)])

    result = apply_promotion_relegation(a, b, c, d)

    # Permanentes: C5..C16
    assert "C5" in result.serie_c
    assert "C16" in result.serie_c
    assert "C1" not in result.serie_c   # subiu para B
    assert "C17" not in result.serie_c  # desceu para D

    # Rebaixados da B: B17..B20
    assert "B17" in result.serie_c
    assert "B20" in result.serie_c

    # Promovidos da D: D1..D4
    assert "D1" in result.serie_c
    assert "D4" in result.serie_c
    assert "D5" not in result.serie_c


def test_promotion_relegation_serie_d_composition():
    """nova D = D sem os 4 primeiros + rebaixados da C (4 piores da D ficam)."""
    a = _make_series(20, "A")
    b = _make_series(20, "B")
    c = _standings([f"C{i}" for i in range(1, 21)])
    d = _standings([f"D{i}" for i in range(1, 21)])

    result = apply_promotion_relegation(a, b, c, d)

    # Permanentes da D: D5..D20
    assert "D5" in result.serie_d
    assert "D20" in result.serie_d
    assert "D1" not in result.serie_d   # subiu para C
    assert "D4" not in result.serie_d   # subiu para C

    # Rebaixados da C: C17..C20
    assert "C17" in result.serie_d
    assert "C20" in result.serie_d
    assert "C16" not in result.serie_d  # permaneceu na C


def test_promotion_relegation_no_team_in_two_series():
    """Nenhum time pode aparecer em duas séries diferentes ao mesmo tempo."""
    result = apply_promotion_relegation(
        _make_series(20, "A"),
        _make_series(20, "B"),
        _make_series(20, "C"),
        _make_series(20, "D"),
    )

    all_teams = (
        list(result.serie_a)
        + list(result.serie_b)
        + list(result.serie_c)
        + list(result.serie_d)
    )
    assert len(all_teams) == len(set(all_teams)), "Algum time aparece em mais de uma série"


def test_promotion_relegation_total_teams_conserved():
    """O número total de times deve ser conservado (20*4 = 80)."""
    result = apply_promotion_relegation(
        _make_series(20, "A"),
        _make_series(20, "B"),
        _make_series(20, "C"),
        _make_series(20, "D"),
    )

    total = (
        len(result.serie_a)
        + len(result.serie_b)
        + len(result.serie_c)
        + len(result.serie_d)
    )
    assert total == 80


def test_promotion_relegation_order_preserved_within_group():
    """A ordem interna dos permanentes deve ser preservada."""
    a = _standings(["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"])
    b = _standings(["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"])
    c = _standings(["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"])
    d = _standings(["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"])

    result = apply_promotion_relegation(a, b, c, d)

    # Os permanentes da A (A1..A4) devem manter A1 antes de A4
    perm_a = [t for t in result.serie_a if t.startswith("A")]
    assert perm_a == ["A1", "A2", "A3", "A4"]

    # Os permanentes da D (D5..D8) devem manter D5 antes de D8
    perm_d = [t for t in result.serie_d if t.startswith("D")]
    assert perm_d == ["D5", "D6", "D7", "D8"]


# ---------------------------------------------------------------------------
# apply_promotion_relegation — validação de erros
# ---------------------------------------------------------------------------

def test_promotion_relegation_raises_if_serie_a_too_small():
    with pytest.raises(ValueError, match="A precisa ter pelo menos 4 times"):
        apply_promotion_relegation(
            _standings(["T1", "T2", "T3"]),  # apenas 3 times
            _make_series(4, "B"),
            _make_series(4, "C"),
            _make_series(4, "D"),
        )


def test_promotion_relegation_raises_if_serie_b_too_small():
    with pytest.raises(ValueError, match="B precisa ter pelo menos 4 times"):
        apply_promotion_relegation(
            _make_series(4, "A"),
            _standings(["T1"]),              # apenas 1 time
            _make_series(4, "C"),
            _make_series(4, "D"),
        )


def test_promotion_relegation_raises_if_serie_c_too_small():
    with pytest.raises(ValueError, match="C precisa ter pelo menos 4 times"):
        apply_promotion_relegation(
            _make_series(4, "A"),
            _make_series(4, "B"),
            _standings([]),                  # vazia
            _make_series(4, "D"),
        )


def test_promotion_relegation_raises_if_serie_d_too_small():
    with pytest.raises(ValueError, match="D precisa ter pelo menos 4 times"):
        apply_promotion_relegation(
            _make_series(4, "A"),
            _make_series(4, "B"),
            _make_series(4, "C"),
            _standings(["T1", "T2"]),        # apenas 2 times
        )


# ---------------------------------------------------------------------------
# apply_promotion_relegation — caso mínimo (4 times por série)
# ---------------------------------------------------------------------------

def test_promotion_relegation_minimum_four_teams_per_series():
    """Com 4 times por série, todos sobem/descem; nenhum permanece."""
    a = _standings(["A1", "A2", "A3", "A4"])
    b = _standings(["B1", "B2", "B3", "B4"])
    c = _standings(["C1", "C2", "C3", "C4"])
    d = _standings(["D1", "D2", "D3", "D4"])

    result = apply_promotion_relegation(a, b, c, d)

    # nova A = [] + [B1,B2,B3,B4] = 4 times (todos da B)
    assert set(result.serie_a) == {"B1", "B2", "B3", "B4"}

    # nova B = [] + [A1,A2,A3,A4] + [C1,C2,C3,C4] = 8 times
    assert set(result.serie_b) == {"A1", "A2", "A3", "A4", "C1", "C2", "C3", "C4"}

    # nova C = [] + [B1,B2,B3,B4] + [D1,D2,D3,D4] = 8 times
    assert set(result.serie_c) == {"B1", "B2", "B3", "B4", "D1", "D2", "D3", "D4"}

    # nova D = [D1..D4 sem os 4 primeiros = []] + [C1,C2,C3,C4] = 4 times
    assert set(result.serie_d) == {"C1", "C2", "C3", "C4"}
