"""Testes de idempotência financeira e histórica."""

from __future__ import annotations

from garfoot.domain.contract import Contract
from garfoot.domain.contract_lifecycle import process_end_of_season_contracts_idempotent
from garfoot.domain.economic_context import EconomicContext
from garfoot.domain.game_state import GameState
from garfoot.domain.idempotency import IdempotencyLedger
from garfoot.domain.operating_expenses import (
    generate_default_operating_expenses_for_team,
    process_round_operating_expenses_idempotent,
)
from garfoot.domain.player import Player, PlayerPosition
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.sponsorship import (
    calculate_sponsorship_match_bonus_idempotent,
    generate_default_sponsorships_for_team,
    process_round_sponsorship_income_idempotent,
)
from garfoot.domain.team import Team


def test_round_sponsorship_income_is_idempotent():
    ledger = IdempotencyLedger()
    team = Team(name="Fortaleza", city="Fortaleza", budget=1_000_000)
    portfolio = generate_default_sponsorships_for_team(team, series="B", seed=42)

    # Primeira execução: credita a renda da rodada
    team, income1 = process_round_sponsorship_income_idempotent(
        team=team,
        portfolio=portfolio,
        season_year=2026,
        round_number=1,
        ledger=ledger,
    )
    assert income1 > 0
    initial_budget_after_first = team.budget

    # Segunda execução com a mesma chave: não credita nada
    team, income2 = process_round_sponsorship_income_idempotent(
        team=team,
        portfolio=portfolio,
        season_year=2026,
        round_number=1,
        ledger=ledger,
    )
    assert income2 == 0
    assert team.budget == initial_budget_after_first


def test_operating_expenses_per_round_is_idempotent():
    ledger = IdempotencyLedger()
    team = Team(name="Fortaleza", city="Fortaleza", budget=10_000_000)
    profile = generate_default_operating_expenses_for_team(team, series="B")

    # Primeira dedução
    team, cost1 = process_round_operating_expenses_idempotent(
        team=team,
        expense_profile=profile,
        season_year=2026,
        round_number=1,
        ledger=ledger,
    )
    assert cost1 > 0
    budget_after_first = team.budget

    # Segunda chamada repetida
    team, cost2 = process_round_operating_expenses_idempotent(
        team=team,
        expense_profile=profile,
        season_year=2026,
        round_number=1,
        ledger=ledger,
    )
    assert cost2 == 0
    assert team.budget == budget_after_first


def test_win_bonus_is_idempotent():
    ledger = IdempotencyLedger()
    team = Team(name="Fortaleza", city="Fortaleza", budget=1_000_000)
    portfolio = generate_default_sponsorships_for_team(team, series="A", seed=10)

    bonus1 = calculate_sponsorship_match_bonus_idempotent(
        portfolio=portfolio,
        team_name="Fortaleza",
        match_id="MATCH-2026-R01-FOR-CEA",
        season_year=2026,
        ledger=ledger,
        is_win=True,
    )
    assert bonus1 > 0

    bonus2 = calculate_sponsorship_match_bonus_idempotent(
        portfolio=portfolio,
        team_name="Fortaleza",
        match_id="MATCH-2026-R01-FOR-CEA",
        season_year=2026,
        ledger=ledger,
        is_win=True,
    )
    assert bonus2 == 0


def test_economic_context_inflation_advance_is_idempotent():
    ledger = IdempotencyLedger()
    econ = EconomicContext(season_year=2026, economic_index=1.0)

    econ_next = econ.advance_season_idempotent(ledger)
    assert econ_next.season_year == 2027
    assert econ_next.economic_index > 1.0

    # Chamada duplicada para o mesmo ano base 2026
    econ_dup = econ.advance_season_idempotent(ledger)
    assert econ_dup.season_year == 2026
    assert econ_dup.economic_index == 1.0


def test_process_end_of_season_contracts_is_idempotent():
    ledger = IdempotencyLedger()
    p1 = Player(
        name="Veterano",
        age=32,
        position=PlayerPosition.MIDFIELDER,
        attack=60,
        defense=60,
        fitness=80,
        morale=80,
        value=100_000,
        contract=Contract(years_remaining=1),
    )
    team = Team(name="CPU Team", city="City", budget=1_000_000, players=[p1])
    free_agents: list[Player] = []

    teams1, fa1, res1 = process_end_of_season_contracts_idempotent(
        teams=[team],
        human_team_name="Human Team",
        free_agents=free_agents,
        season_year=2026,
        ledger=ledger,
    )
    assert len(teams1[0].players) == 1 or len(fa1) == 1

    # Segunda chamada repetida
    teams2, fa2, res2 = process_end_of_season_contracts_idempotent(
        teams=teams1,
        human_team_name="Human Team",
        free_agents=fa1,
        season_year=2026,
        ledger=ledger,
    )
    assert teams2 == teams1
    assert fa2 == fa1
    assert "já haviam sido processados" in res2.messages[0]


from garfoot.domain.cup import KnockoutCup


def test_game_state_persists_ledger_roundtrip():
    state = GameState(
        save_name="TestSave",
        player_team_name="Fortaleza",
        current_season=2026,
        current_round=1,
        season_orchestrator=SeasonOrchestrator(
            season_year=2026,
            championships={},
            copa_do_brasil=KnockoutCup(name="Copa do Brasil", season_year=2026, teams=[Team(name="Team A", city="City A", budget=1000000), Team(name="Team B", city="City B", budget=1000000)]),
        ),
    )
    state.idempotency_ledger.mark("sponsorship:round-income:2026:1:Fortaleza")

    data = state.to_dict()
    reconstructed = GameState.from_dict(data)

    assert reconstructed.idempotency_ledger.has("sponsorship:round-income:2026:1:Fortaleza")
