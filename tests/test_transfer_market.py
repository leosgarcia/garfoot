"""Testes unitários para o mercado de transferências."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.domain.transfer_market import (
    TransferListing,
    execute_player_purchase,
    filter_transfer_listings,
    get_available_transfer_market,
)


def _make_team_with_players(name: str, budget: int = 1_000_000) -> Team:
    players = [
        Player(name=f"{name} Titular {i}", age=24, position=PlayerPosition.MIDFIELDER, attack=60, defense=60, fitness=80, morale=80)
        for i in range(11)
    ]
    reserves = [
        Player(name=f"{name} Reserva 1", age=20, position=PlayerPosition.FORWARD, attack=65, defense=30, fitness=80, morale=80),
        Player(name=f"{name} Reserva 2", age=28, position=PlayerPosition.DEFENDER, attack=30, defense=65, fitness=80, morale=80),
    ]
    t = Team(name=name, city="Cidade Teste", budget=budget, players=players + reserves)
    t.starting_player_names = [p.name for p in players]
    return t


def test_get_available_transfer_market_excludes_user_and_starters():
    buyer = _make_team_with_players("Meu Clube", budget=2_000_000)
    cpu_team = _make_team_with_players("CPU Clube", budget=1_000_000)

    listings = get_available_transfer_market([buyer, cpu_team], user_team_name="Meu Clube", seed=42)

    # NENHUM jogador do comprador deve aparecer à venda
    assert not any(l.seller_team_name == "Meu Clube" for l in listings)

    # Apenas reservas da CPU devem aparecer à venda
    assert len(listings) == 2
    assert all(l.seller_team_name == "CPU Clube" for l in listings)


def test_filter_transfer_listings():
    buyer = _make_team_with_players("Meu Clube")
    cpu_team = _make_team_with_players("CPU Clube")
    listings = get_available_transfer_market([buyer, cpu_team], user_team_name="Meu Clube", seed=42)

    # Filtra por Atacantes
    fwds = filter_transfer_listings(listings, position=PlayerPosition.FORWARD)
    assert len(fwds) == 1
    assert fwds[0].player.position == PlayerPosition.FORWARD

    # Filtra por idade max 22
    youngs = filter_transfer_listings(listings, max_age=22)
    assert len(youngs) == 1
    assert youngs[0].player.age == 20


def test_execute_player_purchase_success():
    buyer = _make_team_with_players("Meu Clube", budget=2_000_000)
    seller = _make_team_with_players("Vendedor", budget=500_000)

    listings = get_available_transfer_market([buyer, seller], user_team_name="Meu Clube", seed=42)
    target = listings[0]

    updated_buyer, updated_seller = execute_player_purchase(buyer, seller, target)

    # 1. Caixa do comprador debitado, vendedor creditado
    assert updated_buyer.budget == 2_000_000 - target.asking_price
    assert updated_seller.budget == 500_000 + target.asking_price

    # 2. Jogador saiu do vendedor e entrou no comprador
    assert updated_seller.find_player(target.player.name) is None
    purchased = updated_buyer.find_player(target.player.name)
    assert purchased is not None

    # 3. Novo contrato de 3 anos com 1 ano de proteção no comprador
    assert purchased.contract.years_remaining == 3
    assert purchased.contract.is_protected is True
    assert purchased.contract.can_be_transferred is False


def test_execute_player_purchase_insufficient_budget():
    buyer = _make_team_with_players("Meu Clube", budget=10_000)  # caixa quase zerado
    seller = _make_team_with_players("Vendedor")
    listings = get_available_transfer_market([buyer, seller], user_team_name="Meu Clube")

    with pytest.raises(ValueError, match="Orçamento insuficiente"):
        execute_player_purchase(buyer, seller, listings[0])


def test_execute_release_clause_purchase_success_and_protection_bypass():
    from garfoot.domain.transfer_market import execute_release_clause_purchase

    buyer = _make_team_with_players("Comprador Rico", budget=30_000_000)
    seller = _make_team_with_players("Vendedor", budget=1_000_000)

    # Craque do vendedor está com contrato protegido contra venda comum (is_protected = True)
    star_player = Player(
        name="Craque Intocavel",
        age=21,
        position=PlayerPosition.FORWARD,
        attack=85,
        defense=40,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=3, is_protected=True, protection_years=2),
    )
    seller.add_player(star_player)

    # Venda comum deve ser bloqueada (can_be_transferred is False)
    assert star_player.contract.can_be_transferred is False

    clause_price = star_player.contract.release_clause
    assert clause_price > star_player.market_value

    # Compra forçada pela Cláusula de Rescisão deve ter SUCESSO!
    updated_buyer, updated_seller = execute_release_clause_purchase(buyer, seller, star_player)

    assert updated_buyer.budget == 30_000_000 - clause_price
    assert updated_seller.budget == 1_000_000 + clause_price

    transferred = updated_buyer.find_player("Craque Intocavel")
    assert transferred is not None
    assert transferred.contract.years_remaining == 3
    assert transferred.contract.release_clause > 0


def test_execute_release_clause_purchase_expired_contract_fails():
    from garfoot.domain.transfer_market import execute_release_clause_purchase

    buyer = _make_team_with_players("Comprador Rico", budget=20_000_000)
    seller = _make_team_with_players("Vendedor")

    free_player = Player(
        name="Jogador Sem Contrato",
        age=25,
        position=PlayerPosition.MIDFIELDER,
        attack=60,
        defense=60,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=0, release_clause=0),
    )
    seller.add_player(free_player)

    with pytest.raises(ValueError, match="não possui um contrato vigente com cláusula"):
        execute_release_clause_purchase(buyer, seller, free_player)
