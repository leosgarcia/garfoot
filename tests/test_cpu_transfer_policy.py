"""Testes unitários para a política de transferências dos clubes da CPU."""

import pytest

from garfoot.domain.contract import Contract
from garfoot.domain.cpu_transfer_policy import (
    ClubTransferProfile,
    calculate_cpu_asking_price,
    calculate_wage_bill,
    evaluate_player_sale_priority,
    evaluate_team_needs,
    execute_cpu_transfer_window,
    infer_club_transfer_profile,
    select_cpu_purchase_targets,
    should_accept_transfer_offer,
)
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.team import Team
from garfoot.domain.transfer_market import TransferListing


def _make_team(name: str, budget: int = 1_000_000, num_players: int = 14) -> Team:
    players = [
        Player(name=f"{name} P{i}", age=22 + (i % 8), position=PlayerPosition.MIDFIELDER if i % 2 == 0 else PlayerPosition.DEFENDER, attack=60, defense=60, fitness=80, morale=80)
        for i in range(num_players)
    ]
    t = Team(name=name, city="Cidade", budget=budget, players=players)
    t.starting_player_names = [p.name for p in players[:11]]
    return t


def test_infer_club_transfer_profile():
    # 1. Caixa zerado -> DEBT_PRESSURED
    poor_team = _make_team("Sem Caixa", budget=10_000)
    assert infer_club_transfer_profile(poor_team, series="A") == ClubTransferProfile.DEBT_PRESSURED

    # 2. Caixa alto na Série A -> RICH
    rich_team = _make_team("Rico A", budget=20_000_000)
    assert infer_club_transfer_profile(rich_team, series="A") == ClubTransferProfile.RICH

    # 3. Pequeno na Série D -> SMALL_CLUB
    small_team = _make_team("Pequeno D", budget=800_000)
    assert infer_club_transfer_profile(small_team, series="D") == ClubTransferProfile.SMALL_CLUB


def test_evaluate_player_sale_priority_and_asking_price():
    team = _make_team("Clube A", budget=1_000_000)
    starter = team.players[0]
    reserve = team.players[11]

    # Reserva tem prioridade de venda maior que titular
    prio_starter = evaluate_player_sale_priority(team, starter, ClubTransferProfile.BALANCED)
    prio_reserve = evaluate_player_sale_priority(team, reserve, ClubTransferProfile.BALANCED)

    assert prio_reserve > prio_starter

    # Preço pedido do titular deve ser maior que o do reserva
    price_starter = calculate_cpu_asking_price(team, starter, ClubTransferProfile.BALANCED)
    price_reserve = calculate_cpu_asking_price(team, reserve, ClubTransferProfile.BALANCED)

    assert price_starter > price_reserve


def test_should_accept_transfer_offer():
    team = _make_team("Clube Vendedor")
    player = team.players[11]  # Reserva
    asking = calculate_cpu_asking_price(team, player, ClubTransferProfile.BALANCED)

    # 1. Oferta abaixo do preço pedido -> Recusa
    assert should_accept_transfer_offer(team, player, offer_amount=asking - 10_000) is False

    # 2. Oferta muito acima -> Aceita
    assert should_accept_transfer_offer(team, player, offer_amount=asking * 2) is True

    # 3. Jogador protegido sem atingir cláusula -> Recusa
    protected_player = Player(
        name="Protegido",
        age=20,
        position=PlayerPosition.FORWARD,
        attack=80,
        defense=40,
        fitness=80,
        morale=80,
        contract=Contract(years_remaining=3, is_protected=True, release_clause=10_000_000),
    )
    team.add_player(protected_player)
    assert should_accept_transfer_offer(team, protected_player, offer_amount=2_000_000) is False

    # 4. Oferta igual/acima da cláusula -> Aceita
    assert should_accept_transfer_offer(team, protected_player, offer_amount=10_000_000) is True


def test_evaluate_team_needs_and_select_targets():
    team = _make_team("Clube Carente", budget=5_000_000)
    # Remove goleiros para gerar carência explícita
    team.players = [p for p in team.players if p.position != PlayerPosition.GOALKEEPER]

    needs = evaluate_team_needs(team, series="A")
    assert any(n.position == PlayerPosition.GOALKEEPER for n in needs)

    gk = Player(name="Goleiro Novo", age=24, position=PlayerPosition.GOALKEEPER, attack=30, defense=75, fitness=80, morale=80)
    listing = TransferListing(player=gk, seller_team_name="Vendedor GK", asking_price=1_000_000)

    targets = select_cpu_purchase_targets(
        buying_team=team,
        candidate_listings=[listing],
        profile=ClubTransferProfile.BALANCED,
        needs=needs,
        max_targets=1,
    )

    assert len(targets) == 1
    assert targets[0].player.name == "Goleiro Novo"


def test_execute_cpu_transfer_window_protection_and_determinism():
    human_team = _make_team("Meu Clube Humano", budget=10_000_000)
    cpu_1 = _make_team("CPU 1", budget=5_000_000)
    cpu_2 = _make_team("CPU 2", budget=5_000_000)

    tiers = {"Meu Clube Humano": "A", "CPU 1": "A", "CPU 2": "A"}

    # Executa a janela com seed 42
    plan1 = execute_cpu_transfer_window([human_team, cpu_1, cpu_2], human_team_name="Meu Clube Humano", league_tiers_by_team=tiers, seed=42)

    # 1. NENHUM jogador do time humano deve ser transferido
    for t in plan1.executed_transfers:
        assert t.buyer_team_name != "Meu Clube Humano"
        assert t.seller_team_name != "Meu Clube Humano"

    # 2. Determinismo: mesma seed produz o mesmo plano
    plan2 = execute_cpu_transfer_window([human_team, cpu_1, cpu_2], human_team_name="Meu Clube Humano", league_tiers_by_team=tiers, seed=42)
    assert len(plan1.executed_transfers) == len(plan2.executed_transfers)
