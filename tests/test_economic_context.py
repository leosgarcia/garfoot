"""Testes unitários para o contexto econômico global e sistema de inflação da temporada."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.economic_context import EconomicContext, apply_economic_index
from garfoot.domain.economy import calculate_player_market_value, calculate_release_clause
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.finance import calculate_upgrade_cost
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.prizes import CompetitionType, PrizeCategory, PrizeStructure, build_season_awards
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.cup import KnockoutCup
from garfoot.domain.team import Team


def test_economic_context_defaults_and_advance_season():
    ctx = EconomicContext(season_year=2026, economic_index=1.0, inflation_rate=0.05)
    assert ctx.season_year == 2026
    assert ctx.economic_index == 1.0

    # Avança 1 temporada (2027, índice = 1.05)
    ctx2 = ctx.advance_season()
    assert ctx2.season_year == 2027
    assert ctx2.economic_index == 1.05

    # Avança mais 1 temporada (2028, índice ~ 1.1025)
    ctx3 = ctx2.advance_season()
    assert ctx3.season_year == 2028
    assert ctx3.economic_index == pytest.approx(1.1025, 0.0001)


def test_economic_context_limits_and_validation():
    # Inflação negativa deve falhar
    with pytest.raises(ValueError, match="taxa de inflação deve ficar entre"):
        EconomicContext(inflation_rate=-0.01)

    # Inflação acima do teto normal (0.08) deve falhar
    with pytest.raises(ValueError, match="taxa de inflação deve ficar entre"):
        EconomicContext(inflation_rate=0.10)

    # Índice econômico zerado ou negativo deve falhar
    with pytest.raises(ValueError, match="índice econômico deve ser positivo"):
        EconomicContext(economic_index=0.0)

    with pytest.raises(ValueError, match="índice econômico deve ser positivo"):
        apply_economic_index(100_000, 0.0)


def test_economic_index_impact_on_new_market_values_and_contracts():
    ctx1 = EconomicContext(economic_index=1.0)
    ctx2 = EconomicContext(economic_index=1.10)  # 10% inflacionado

    v1 = calculate_player_market_value(overall=80, age=22, position=PlayerPosition.FORWARD, economic_index=ctx1.economic_index)
    v2 = calculate_player_market_value(overall=80, age=22, position=PlayerPosition.FORWARD, economic_index=ctx2.economic_index)

    # Novo valor de mercado no índice 1.10 deve ser aproximadamente 10% maior
    assert v2 > v1
    assert v2 == pytest.approx(v1 * 1.10, abs=2)

    # Jogador antigo mantém contrato e cláusula originais
    old_contract = Contract(years_remaining=2, release_clause=5_000_000)
    p_old = Player(name="Antigo", age=25, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80, contract=old_contract)
    assert p_old.contract.release_clause == 5_000_000  # Não sofre alteração retroativa


def test_economic_index_impact_on_stadium_upgrade_cost():
    cost_base = calculate_upgrade_cost(current_capacity=20_000, economic_index=1.0)
    cost_inflated = calculate_upgrade_cost(current_capacity=20_000, economic_index=1.05)

    assert cost_inflated > cost_base
    assert cost_inflated == round(cost_base * 1.05)


def test_economic_index_impact_on_future_prizes():
    ctx_inflated = EconomicContext(economic_index=1.10)
    standings = {CompetitionType.SERIE_A: [("Flamengo", 1), ("Palmeiras", 2)]}

    awards_base = build_season_awards(season_year=2026, championship_standings=standings)
    awards_inflated = build_season_awards(season_year=2026, championship_standings=standings, economic_context=ctx_inflated)

    base_champ = next(a for a in awards_base.awards if a.category == "campeao")
    inflated_champ = next(a for a in awards_inflated.awards if a.category == "campeao")

    assert inflated_champ.amount > base_champ.amount
    assert inflated_champ.amount == round(base_champ.amount * 1.10)


def test_game_state_economic_context_serialization_and_backwards_compatibility():
    ctx = EconomicContext(season_year=2026, economic_index=1.05, inflation_rate=0.05)
    dummy_teams = [Team(name="A", city="A", budget=100), Team(name="B", city="B", budget=100)]
    orchestrator = SeasonOrchestrator(season_year=2026, championships={}, copa_do_brasil=KnockoutCup(name="Copa do Brasil", season_year=2026, teams=dummy_teams))

    state = GameState(
        save_name="SaveEcon",
        player_team_name="Flamengo",
        current_season=2026,
        current_round=1,
        season_orchestrator=orchestrator,
        economic_context=ctx,
    )

    serialized = state.to_dict()
    assert "economic_context" in serialized
    assert serialized["economic_context"]["economic_index"] == 1.05

    restored = GameState.from_dict(serialized)
    assert restored.economic_context.economic_index == 1.05

    # Compatibilidade com save antigo sem economic_context
    del serialized["economic_context"]
    restored_legacy = GameState.from_dict(serialized)
    assert restored_legacy.economic_context is not None
    assert restored_legacy.economic_context.economic_index == 1.0
