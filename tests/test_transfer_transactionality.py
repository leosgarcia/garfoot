"""Testes para validação transacional e atômica de transferências de jogadores."""

from __future__ import annotations

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.contract_lifecycle import sign_free_agent
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.squad_rules import SquadLimitConfig
from garfoot.domain.team import Team
from garfoot.domain.transfer_market import (
    TransferExecutionResult,
    TransferFailureReason,
    TransferListing,
    execute_player_purchase,
    execute_release_clause_purchase,
    validate_transfer_preconditions,
)


def test_successful_purchase_updates_both_teams_atomically():
    player = Player(
        name="Craque",
        age=25,
        position=PlayerPosition.MIDFIELDER,
        attack=75,
        defense=75,
        fitness=90,
        morale=90,
        value=500_000,
        contract=Contract(years_remaining=2, is_protected=False),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])
    buyer = Team(name="Comprador FC", city="Cidade B", budget=2_000_000, players=[])
    listing = TransferListing(player=player, seller_team_name=seller.name, asking_price=500_000)

    execute_player_purchase(buyer, seller, listing)

    assert len(seller.players) == 0
    assert seller.budget == 1_500_000
    assert len(buyer.players) == 1
    assert buyer.players[0].name == "Craque"
    assert buyer.budget == 1_500_000


def test_insufficient_budget_prevents_partial_state_change():
    player = Player(
        name="Craque Caro",
        age=25,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=50,
        fitness=90,
        morale=90,
        value=1_000_000,
        contract=Contract(years_remaining=2, is_protected=False),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])
    buyer = Team(name="Comprador Pobre", city="Cidade B", budget=100_000, players=[])
    listing = TransferListing(player=player, seller_team_name=seller.name, asking_price=1_000_000)

    with pytest.raises(ValueError, match="Orçamento insuficiente"):
        execute_player_purchase(buyer, seller, listing)

    # Verifica que NADA mudou (estado mantido intacto)
    assert len(seller.players) == 1
    assert seller.players[0].name == "Craque Caro"
    assert seller.budget == 1_000_000
    assert len(buyer.players) == 0
    assert buyer.budget == 100_000


def test_full_squad_prevents_partial_state_change():
    player = Player(
        name="Alvo",
        age=22,
        position=PlayerPosition.MIDFIELDER,
        attack=70,
        defense=70,
        fitness=80,
        morale=80,
        value=200_000,
        contract=Contract(years_remaining=2, is_protected=False),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])

    # Elenco do comprador com 30 atletas (máximo teto)
    buyer_players = [
        Player(name=f"Atleta {i:02d}", age=20, position=PlayerPosition.DEFENDER, attack=50, defense=50, fitness=80, morale=80, value=50_000)
        for i in range(30)
    ]
    buyer = Team(name="Comprador Lotado", city="Cidade B", budget=10_000_000, players=buyer_players)
    listing = TransferListing(player=player, seller_team_name=seller.name, asking_price=200_000)

    with pytest.raises(ValueError, match="elenco"):
        execute_player_purchase(buyer, seller, listing)

    # Verifica que vendedor e comprador não sofreram alteração
    assert len(seller.players) == 1
    assert len(buyer.players) == 30
    assert buyer.budget == 10_000_000
    assert seller.budget == 1_000_000


def test_duplicate_player_in_buyer_blocks_transfer():
    player = Player(
        name="Repetido",
        age=24,
        position=PlayerPosition.GOALKEEPER,
        attack=10,
        defense=70,
        fitness=80,
        morale=80,
        value=100_000,
        contract=Contract(years_remaining=2, is_protected=False),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])
    
    # Comprador já tem um jogador com o mesmo nome
    existing = Player(name="Repetido", age=24, position=PlayerPosition.GOALKEEPER, attack=10, defense=70, fitness=80, morale=80, value=100_000)
    buyer = Team(name="Comprador FC", city="Cidade B", budget=500_000, players=[existing])
    listing = TransferListing(player=player, seller_team_name=seller.name, asking_price=100_000)

    with pytest.raises(ValueError, match="já pertence ao elenco"):
        execute_player_purchase(buyer, seller, listing)

    assert len(seller.players) == 1
    assert seller.budget == 1_000_000
    assert len(buyer.players) == 1


def test_protected_contract_blocks_common_purchase():
    player = Player(
        name="Protegido",
        age=22,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=40,
        fitness=90,
        morale=90,
        value=800_000,
        contract=Contract(years_remaining=3, is_protected=True, protection_years=2),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])
    buyer = Team(name="Comprador FC", city="Cidade B", budget=5_000_000, players=[])
    listing = TransferListing(player=player, seller_team_name=seller.name, asking_price=800_000)

    with pytest.raises(ValueError, match="não permite transferência"):
        execute_player_purchase(buyer, seller, listing)

    assert len(seller.players) == 1
    assert len(buyer.players) == 0


def test_release_clause_purchase_success():
    player = Player(
        name="Joia",
        age=20,
        position=PlayerPosition.FORWARD,
        attack=82,
        defense=40,
        fitness=90,
        morale=90,
        value=1_000_000,
        contract=Contract(years_remaining=3, is_protected=True, release_clause=4_000_000),
    )
    seller = Team(name="Vendedor FC", city="Cidade A", budget=1_000_000, players=[player])
    buyer = Team(name="Comprador Rico", city="Cidade B", budget=10_000_000, players=[])

    execute_release_clause_purchase(buyer, seller, player)

    assert len(seller.players) == 0
    assert seller.budget == 5_000_000
    assert len(buyer.players) == 1
    assert buyer.players[0].name == "Joia"
    assert buyer.budget == 6_000_000


def test_free_agent_signing_transactionality():
    player = Player(
        name="Livre",
        age=28,
        position=PlayerPosition.MIDFIELDER,
        attack=65,
        defense=65,
        fitness=80,
        morale=80,
        value=300_000,
        contract=Contract(years_remaining=0),
    )
    buyer = Team(name="Comprador FC", city="Cidade A", budget=50_000, players=[])

    # Luvas acima do orçamento
    with pytest.raises(ValueError, match="Orçamento insuficiente"):
        sign_free_agent(buyer, player, signing_bonus=100_000)

    assert len(buyer.players) == 0
    assert buyer.budget == 50_000


def test_cpu_auto_transfer_protects_human_team():
    player = Player(
        name="Titular Humano",
        age=25,
        position=PlayerPosition.MIDFIELDER,
        attack=70,
        defense=70,
        fitness=80,
        morale=80,
        value=400_000,
        contract=Contract(years_remaining=2, is_protected=False),
    )
    human_team = Team(name="Meu Time Humano", city="Minha Cidade", budget=1_000_000, players=[player])
    cpu_buyer = Team(name="CPU FC", city="Outra Cidade", budget=2_000_000, players=[])
    listing = TransferListing(player=player, seller_team_name=human_team.name, asking_price=400_000)

    is_valid, reason, msg = validate_transfer_preconditions(
        buyer_team=cpu_buyer,
        seller_team=human_team,
        player=player,
        amount=400_000,
        is_cpu_auto=True,
        human_team_name="Meu Time Humano",
    )

    assert not is_valid
    assert reason == TransferFailureReason.HUMAN_TEAM_PROTECTED
