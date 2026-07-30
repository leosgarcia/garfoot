"""Modelo e regras puras do mercado de transferências."""

from __future__ import annotations

from dataclasses import dataclass, replace
from random import Random

from garfoot.domain.contract import Contract
from garfoot.domain.economy import calculate_initial_salary
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.stable_random import combine_seed, stable_composite_seed


from enum import StrEnum


class TransferFailureReason(StrEnum):
    """Motivos explícitos de falha na validação transacional de transferências."""

    BUYER_NOT_FOUND = "buyer_not_found"
    SELLER_NOT_FOUND = "seller_not_found"
    PLAYER_NOT_FOUND = "player_not_found"
    PLAYER_ALREADY_IN_BUYER = "player_already_in_buyer"
    INSUFFICIENT_BUDGET = "insufficient_budget"
    SQUAD_FULL = "squad_full"
    WAGE_BLOCKED = "wage_blocked"
    FINANCIAL_RESTRICTION = "financial_restriction"
    CONTRACT_BLOCKED = "contract_blocked"
    INVALID_RELEASE_CLAUSE = "invalid_release_clause"
    HUMAN_TEAM_PROTECTED = "human_team_protected"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TransferExecutionResult:
    """Resultado imutável e transacional de uma tentativa de transferência."""

    success: bool
    buyer: Team | None
    seller: Team | None
    player: Player | None
    amount: int
    reason: TransferFailureReason | None = None
    message: str = ""


@dataclass(frozen=True, slots=True)
class TransferListing:
    """Representa um jogador anunciado no mercado de transferências."""

    player: Player
    seller_team_name: str
    asking_price: int

    def __post_init__(self) -> None:
        if self.asking_price <= 0:
            raise ValueError("O preço pedido deve ser positivo.")


def get_available_transfer_market(
    teams: list[Team],
    user_team_name: str,
    seed: int | None = None,
) -> list[TransferListing]:
    """Gera a lista de jogadores colocados à venda pelos times da CPU.

    Critérios da CPU:
    - O jogador não pertence ao time do usuário.
    - O contrato permite transferência (can_be_transferred is True).
    - O jogador é reserva (não está nos 11 titulares).
    """

    listings: list[TransferListing] = []

    for team in teams:
        if team.name == user_team_name:
            continue

        starters = set(team.starting_player_names)
        for player in team.players:
            # 1. Checa contrato
            if not player.contract.can_be_transferred:
                continue

            # 2. Checa se é reserva
            if player.name in starters:
                continue

            # 3. Calcula preço pedido com margem determinística entre 95% e 110%
            if seed is not None:
                rng_seed = combine_seed(seed, team.name, player.name, namespace="transfer-market")
            else:
                rng_seed = stable_composite_seed((team.name, player.name), namespace="transfer-market")
            margin = 0.95 + (rng_seed % 16) * 0.01  # 0.95 a 1.10
            asking_price = max(50_000, round(player.market_value * margin))

            listings.append(
                TransferListing(
                    player=player,
                    seller_team_name=team.name,
                    asking_price=asking_price,
                )
            )

    return listings


def filter_transfer_listings(
    listings: list[TransferListing],
    position: PlayerPosition | None = None,
    min_overall: int | None = None,
    max_overall: int | None = None,
    max_price: int | None = None,
    max_age: int | None = None,
) -> list[TransferListing]:
    """Filtra as ofertas de mercado com base nas restrições fornecidas."""

    filtered = listings

    if position is not None:
        filtered = [l for l in filtered if l.player.position == position]

    if min_overall is not None:
        filtered = [l for l in filtered if l.player.overall >= min_overall]

    if max_overall is not None:
        filtered = [l for l in filtered if l.player.overall <= max_overall]

    if max_price is not None:
        filtered = [l for l in filtered if l.asking_price <= max_price]

    if max_age is not None:
        filtered = [l for l in filtered if l.player.age <= max_age]

    return filtered


def validate_transfer_preconditions(
    buyer_team: Team,
    seller_team: Team | None,
    player: Player,
    amount: int,
    is_release_clause: bool = False,
    is_free_agent: bool = False,
    is_cpu_auto: bool = False,
    human_team_name: str | None = None,
) -> tuple[bool, TransferFailureReason | None, str]:
    """Realiza a pré-validação completa de pré-condições de transferência antes de mutar qualquer estado."""

    # 1. Checa proteção do time humano em transferências da CPU
    if is_cpu_auto and human_team_name:
        if (seller_team and seller_team.name == human_team_name) or buyer_team.name == human_team_name:
            return False, TransferFailureReason.HUMAN_TEAM_PROTECTED, "O time do usuário é protegido contra transferências automáticas da CPU."

    # 2. Checa se o comprador já possui jogador com o mesmo nome
    if any(p.name == player.name for p in buyer_team.players):
        return False, TransferFailureReason.PLAYER_ALREADY_IN_BUYER, f"O jogador {player.name} já pertence ao elenco de {buyer_team.name}."

    # 3. Checa se o vendedor possui o jogador (se houver vendedor)
    if seller_team is not None:
        if not any(p.name == player.name for p in seller_team.players):
            return False, TransferFailureReason.PLAYER_NOT_FOUND, f"O jogador {player.name} não foi encontrado no elenco de {seller_team.name}."

    # 4. Checa regras de contrato (compra comum vs cláusula vs free agent)
    if is_free_agent:
        if player.contract.years_remaining > 0:
            return False, TransferFailureReason.CONTRACT_BLOCKED, f"O jogador {player.name} não é um agente livre."
    elif is_release_clause:
        if player.contract.years_remaining <= 0 or player.contract.release_clause <= 0:
            return False, TransferFailureReason.INVALID_RELEASE_CLAUSE, f"O jogador {player.name} não possui um contrato vigente com cláusula de rescisão válida."
    else:
        if not player.contract.can_be_transferred:
            return False, TransferFailureReason.CONTRACT_BLOCKED, f"O contrato de {player.name} não permite transferência direta."

    # 5. Checa limite de tamanho do elenco do comprador
    from garfoot.domain.squad_rules import can_add_player_to_squad, can_afford_new_salary
    can_add, squad_reason = can_add_player_to_squad(buyer_team)
    if not can_add:
        return False, TransferFailureReason.SQUAD_FULL, squad_reason

    # 6. Checa orçamento do comprador (taxa ou luvas)
    if amount > 0 and buyer_team.budget < amount:
        return False, TransferFailureReason.INSUFFICIENT_BUDGET, f"Orçamento insuficiente em {buyer_team.name} (R$ {buyer_team.budget:,} < R$ {amount:,})."

    # 7. Checa comprometimento e saúde da folha salarial
    new_salary = calculate_initial_salary(max(amount, player.market_value))
    can_afford, wage_reason = can_afford_new_salary(buyer_team, new_salary)
    if not can_afford:
        return False, TransferFailureReason.WAGE_BLOCKED, wage_reason

    return True, None, "Validação concluída com sucesso."


def execute_player_purchase(
    buyer_team: Team,
    seller_team: Team,
    listing: TransferListing,
    is_cpu_auto: bool = False,
    human_team_name: str | None = None,
) -> tuple[Team, Team]:
    """Executa a compra do jogador entre dois times de forma atômica e pré-validada."""

    is_valid, reason, msg = validate_transfer_preconditions(
        buyer_team=buyer_team,
        seller_team=seller_team,
        player=listing.player,
        amount=listing.asking_price,
        is_release_clause=False,
        is_free_agent=False,
        is_cpu_auto=is_cpu_auto,
        human_team_name=human_team_name,
    )
    if not is_valid:
        raise ValueError(msg)

    # 1. Remove do vendedor
    seller_team.remove_player(listing.player.name)

    # 2. Cria novo contrato e salário no novo clube
    new_salary = calculate_initial_salary(listing.asking_price)
    new_contract = Contract(years_remaining=3, is_protected=True, protection_years=1)

    transferred_player = replace(
        listing.player,
        contract=new_contract,
        salary=new_salary,
        value=listing.asking_price,
    )

    # 3. Adiciona ao comprador
    buyer_team.add_player(transferred_player)

    # 4. Ajusta orçamentos
    buyer_team.budget -= listing.asking_price
    seller_team.budget += listing.asking_price

    return buyer_team, seller_team


def execute_release_clause_purchase(
    buyer_team: Team,
    seller_team: Team,
    player: Player,
    is_cpu_auto: bool = False,
    human_team_name: str | None = None,
) -> tuple[Team, Team]:
    """Executa a compra por cláusula de rescisão de forma atômica e pré-validada."""

    clause_amount = player.contract.release_clause if player.contract else 0
    is_valid, reason, msg = validate_transfer_preconditions(
        buyer_team=buyer_team,
        seller_team=seller_team,
        player=player,
        amount=clause_amount,
        is_release_clause=True,
        is_free_agent=False,
        is_cpu_auto=is_cpu_auto,
        human_team_name=human_team_name,
    )
    if not is_valid:
        raise ValueError(msg)

    # 1. Remove do vendedor
    seller_team.remove_player(player.name)

    # 2. Firma novo contrato e recalcula cláusula de rescisão no clube comprador
    from garfoot.domain.economy import calculate_release_clause
    mkt_val = player.market_value
    new_salary = calculate_initial_salary(mkt_val)

    new_clause = calculate_release_clause(
        market_value=mkt_val,
        overall=player.overall,
        age=player.age,
        years_remaining=3,
        is_protected=True,
    )

    new_contract = Contract(
        years_remaining=3,
        is_protected=True,
        protection_years=1,
        release_clause=new_clause,
    )

    transferred_player = replace(
        player,
        contract=new_contract,
        salary=new_salary,
        value=mkt_val,
    )

    # 3. Adiciona ao comprador
    buyer_team.add_player(transferred_player)

    # 4. Ajusta orçamentos
    buyer_team.budget -= clause_amount
    seller_team.budget += clause_amount

    return buyer_team, seller_team
