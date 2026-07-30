"""Testes unitários para o ciclo de vida dos contratos, renovações e jogadores livres."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.contract_lifecycle import (
    ContractSeasonResult,
    FreeAgentPool,
    advance_player_contract,
    advance_team_contracts,
    process_end_of_season_contracts,
    renew_player_contract,
    should_cpu_renew_contract,
    sign_free_agent,
)
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.game_state import GameState
from garfoot.domain.player import Player
from garfoot.domain.cup import KnockoutCup
from garfoot.domain.season_orchestrator import SeasonOrchestrator
from garfoot.domain.team import Team


def test_advance_player_contract_and_team_contracts():
    p1 = Player(
        name="Craque 3 Anos",
        age=22,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=40,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=3, is_protected=True, release_clause=5_000_000),
    )

    p2 = Player(
        name="Veterano 1 Ano",
        age=34,
        position=PlayerPosition.DEFENDER,
        attack=30,
        defense=70,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=1, is_protected=False, release_clause=1_000_000),
    )

    # 1. Redução de 3 para 2 anos
    p1_next = advance_player_contract(p1)
    assert p1_next.contract.years_remaining == 2
    assert p1_next.contract.release_clause == 5_000_000

    # 2. Redução de 1 para 0 anos (zerado desativa cláusula)
    p2_next = advance_player_contract(p2)
    assert p2_next.contract.years_remaining == 0
    assert p2_next.contract.release_clause == 0

    # 3. Avanço em todo o elenco do time
    team = Team(name="Clube A", city="Cidade", budget=1_000_000, players=[p1, p2])
    team_next = advance_team_contracts(team)
    assert team_next.players[0].contract.years_remaining == 2
    assert team_next.players[1].contract.years_remaining == 0


def test_renew_player_contract_recalculates_salary_and_clause():
    old_contract = Contract(years_remaining=1, release_clause=1_000_000)
    p = Player(
        name="Renovando",
        age=25,
        position=PlayerPosition.MIDFIELDER,
        attack=70,
        defense=70,
        fitness=80,
        morale=80,
        salary=100_000,
        contract=old_contract,
    )

    renewed = renew_player_contract(p, years=4, is_protected=True, protection_years=1)
    assert renewed.contract.years_remaining == 4
    assert renewed.contract.is_protected is True
    assert renewed.contract.release_clause > p.market_value
    assert renewed.salary > 0

    # Salário antigo no objeto 'p' imutável não foi alterado sem renovar
    assert p.contract.years_remaining == 1


def test_should_cpu_renew_contract_logic():
    team = Team(name="CPU", city="Cidade", budget=5_000_000)
    starter = Player(name="Titular", age=26, position=PlayerPosition.FORWARD, attack=80, defense=40, fitness=80, morale=80, contract=Contract(years_remaining=1))
    old_reserve = Player(name="Velho Reserva", age=36, position=PlayerPosition.DEFENDER, attack=30, defense=50, fitness=80, morale=80, contract=Contract(years_remaining=1))

    team.players = [starter, old_reserve]
    team.starting_player_names = ["Titular"]

    # Titular deve ser renovado
    assert should_cpu_renew_contract(team, starter, seed=42) is True

    # Velho reserva não titular não deve ser renovado
    assert should_cpu_renew_contract(team, old_reserve, seed=42) is False


def test_sign_free_agent_no_transfer_fee():
    buyer = Team(name="Comprador", city="Cidade", budget=2_000_000)
    free_p = Player(
        name="Jogador Livre",
        age=24,
        position=PlayerPosition.MIDFIELDER,
        attack=65,
        defense=65,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=0, release_clause=0),
    )

    updated_buyer, signed_p = sign_free_agent(buyer, free_p, years=3, signing_bonus=0)

    # Nenhuma taxa de transferência debitada
    assert updated_buyer.budget == 2_000_000
    assert signed_p.contract.years_remaining == 3
    assert signed_p.contract.release_clause > 0
    assert updated_buyer.find_player("Jogador Livre") is not None


def test_process_end_of_season_contracts_and_free_agents_pool():
    human = Team(name="Meu Clube", city="Rio", budget=1_000_000)
    p_human_exp = Player(name="Humano Exp", age=25, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80, contract=Contract(years_remaining=1))
    human.players = [p_human_exp]

    cpu = Team(name="CPU Time", city="SP", budget=1_000_000)
    p_cpu_old = Player(name="CPU Velho", age=36, position=PlayerPosition.DEFENDER, attack=30, defense=50, fitness=80, morale=80, contract=Contract(years_remaining=1))
    cpu.players = [p_cpu_old]

    free_pool: list[Player] = []

    teams, new_free, res = process_end_of_season_contracts(
        teams=[human, cpu],
        human_team_name="Meu Clube",
        free_agents=free_pool,
        seed=42,
    )

    # 1. Jogador do time humano que expirou recebe ALERTA em res.human_team_expired_warnings sem ser deletado
    assert len(res.human_team_expired_warnings) == 1

    # 2. CPU velho reserva não renovado vai para o pool de free_agents
    assert any(p.name == "CPU Velho" for p in new_free)


def test_free_agent_pool_serialization_and_backwards_compatibility():
    free_p = Player(name="Livre", age=22, position=PlayerPosition.FORWARD, attack=60, defense=40, fitness=80, morale=80, contract=Contract(years_remaining=0))
    pool = FreeAgentPool(players=[free_p])

    serialized = pool.to_dict()
    restored = FreeAgentPool.from_dict(serialized)
    assert len(restored.players) == 1
    assert restored.players[0].name == "Livre"

    # Compatibilidade GameState sem free_agents
    dummy_teams = [Team(name="A", city="A", budget=100), Team(name="B", city="B", budget=100)]
    orchestrator = SeasonOrchestrator(season_year=2026, championships={}, copa_do_brasil=KnockoutCup(name="Copa do Brasil", season_year=2026, teams=dummy_teams))
    state = GameState(save_name="SaveState", player_team_name="Flamengo", current_season=2026, current_round=1, season_orchestrator=orchestrator)

    state_dict = state.to_dict()
    del state_dict["free_agents"]

    restored_legacy = GameState.from_dict(state_dict)
    assert restored_legacy.free_agents == []
