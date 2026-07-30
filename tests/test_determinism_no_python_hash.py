"""Teste de regressão para comprovar determinismo entre processos sem depender do hash() do Python."""

from __future__ import annotations

import subprocess
import sys


def test_no_python_hash_in_garfoot_codebase():
    """Garante que não há chamadas a hash() em código de produção."""
    cmd = ["grep", "-R", "hash(", "garfoot"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    # Deve encontrar apenas no comentário de docstring de stable_random.py
    lines = [line for line in result.stdout.splitlines() if not line.endswith(" native `hash()`...")]
    cleaned_lines = [l for l in lines if "substitui o uso do `hash()` nativo" not in l]
    assert len(cleaned_lines) == 0, f"Encontrado uso de hash() em: {cleaned_lines}"


def test_cross_process_determinism_real_cases():
    """Testa que geração de preço de mercado e patrocínios são idênticos entre processos Python distintos."""

    code_market = (
        "from garfoot.domain.player import Player, PlayerPosition; "
        "from garfoot.domain.team import Team; "
        "from garfoot.domain.transfer_market import get_available_transfer_market; "
        "p = Player(name='Test Player', age=25, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80, value=500000); "
        "t = Team(name='CPU Team', city='City', budget=1000000, players=[p]); "
        "listings = get_available_transfer_market([t], user_team_name='User Team', seed=123); "
        "print(listings[0].asking_price if listings else 0)"
    )

    out1 = subprocess.check_output([sys.executable, "-c", code_market], text=True).strip()
    out2 = subprocess.check_output([sys.executable, "-c", code_market], text=True).strip()
    assert out1 == out2

    code_sponsorship = (
        "from garfoot.domain.team import Team; "
        "from garfoot.domain.sponsorship import generate_default_sponsorships_for_team; "
        "t = Team(name='Fortaleza', city='Fortaleza', budget=1000000); "
        "portfolio = generate_default_sponsorships_for_team(t, series='B', seed=42); "
        "print(portfolio.contracts[0].sponsor_name, portfolio.contracts[0].annual_value)"
    )

    spon1 = subprocess.check_output([sys.executable, "-c", code_sponsorship], text=True).strip()
    spon2 = subprocess.check_output([sys.executable, "-c", code_sponsorship], text=True).strip()
    assert spon1 == spon2
