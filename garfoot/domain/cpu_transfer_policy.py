"""Política de compras, vendas e reposição de elenco dos clubes da CPU."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from random import Random
from typing import Any

from garfoot.domain.contract import Contract
from garfoot.domain.enums import PlayerPosition
from garfoot.domain.player import Player
from garfoot.domain.stable_random import combine_seed, stable_composite_seed
from garfoot.domain.team import Team
from garfoot.domain.transfer_market import (
    TransferListing,
    execute_player_purchase,
    execute_release_clause_purchase,
)

# Médias esperadas de overall por Série no modo Brasil
SERIES_EXPECTED_OVERALL: dict[str, int] = {
    "A": 72,
    "B": 64,
    "C": 56,
    "D": 48,
}

# Teto de gasto da janela por perfil (% do orçamento livre)
PROFILE_SPENDING_CAP_RATIO: dict[str, float] = {
    "rich": 0.60,
    "win_now": 0.55,
    "balanced": 0.40,
    "youth_focused": 0.35,
    "small_club": 0.30,
    "selling_club": 0.25,
    "debt_pressured": 0.15,
}


class ClubTransferProfile(StrEnum):
    """Perfis estratégicos de transferência dos clubes."""

    RICH = "rich"
    BALANCED = "balanced"
    SELLING_CLUB = "selling_club"
    DEBT_PRESSURED = "debt_pressured"
    SMALL_CLUB = "small_club"
    YOUTH_FOCUSED = "youth_focused"
    WIN_NOW = "win_now"


@dataclass(frozen=True, slots=True)
class TransferNeed:
    """Carência identificada no elenco de um clube."""

    position: PlayerPosition
    priority: int  # 0 a 100
    target_min_overall: int
    max_price: int
    reason: str


@dataclass(frozen=True, slots=True)
class CpuTransferLog:
    """Registro de uma transferência executada entre clubes da CPU."""

    buyer_team_name: str
    seller_team_name: str
    player_name: str
    amount: int
    transfer_type: str  # "negotiated" | "release_clause"


@dataclass(slots=True)
class CpuTransferPlan:
    """Plano e relatório de execução da janela de transferências da CPU."""

    executed_transfers: list[CpuTransferLog] = field(default_factory=list)
    rejected_offers_count: int = 0
    messages: list[str] = field(default_factory=list)


def calculate_wage_bill(team: Team) -> int:
    """Calcula a folha salarial anual total do elenco."""

    return sum(p.salary for p in team.players)


def infer_club_transfer_profile(team: Team, series: str = "D") -> ClubTransferProfile:
    """Infere o perfil de transferência do clube caso não esteja configurado."""

    series_upper = series.upper()
    wage_bill = calculate_wage_bill(team)

    # 1. Dívida ou caixa muito baixo para os salários
    if team.budget < wage_bill * 0.2:
        return ClubTransferProfile.DEBT_PRESSURED

    # 2. Clube muito rico da Série A
    if series_upper == "A" and team.budget >= 15_000_000:
        return ClubTransferProfile.RICH

    # 3. Clube pequeno de Série D
    if series_upper == "D" and team.budget < 1_000_000:
        return ClubTransferProfile.SMALL_CLUB

    return ClubTransferProfile.BALANCED


def evaluate_player_sale_priority(
    team: Team,
    player: Player,
    profile: ClubTransferProfile = ClubTransferProfile.BALANCED,
) -> int:
    """Calcula score de 0 a 100 indicando a prioridade do clube em vender o jogador."""

    starters = set(team.starting_player_names)
    is_starter = player.name in starters
    score = 50

    # Titularidade
    if is_starter:
        score -= 30
    else:
        score += 25

    # Idade
    if player.age >= 31:
        score += 15
    elif player.age <= 21:
        score -= 20

    # Salário e caixa
    wage_bill = calculate_wage_bill(team)
    if wage_bill > 0 and (player.salary / wage_bill) > 0.15:
        score += 15

    if profile == ClubTransferProfile.DEBT_PRESSURED:
        score += 25
    elif profile == ClubTransferProfile.RICH:
        score -= 20
    elif profile == ClubTransferProfile.SELLING_CLUB and player.age <= 23:
        score += 15

    return max(0, min(100, score))


def calculate_cpu_asking_price(
    team: Team,
    player: Player,
    profile: ClubTransferProfile = ClubTransferProfile.BALANCED,
) -> int:
    """Calcula o preço mínimo que a CPU exige para vender um jogador."""

    mkt = player.market_value
    starters = set(team.starting_player_names)
    is_starter = player.name in starters

    # Multiplicador base por status
    if not is_starter:
        mult = 1.05
    elif player.age <= 21:
        mult = 3.00
    elif player.overall >= 78:
        mult = 2.50
    else:
        mult = 1.80

    # Ajuste por perfil
    if profile == ClubTransferProfile.DEBT_PRESSURED:
        mult *= 0.85
    elif profile == ClubTransferProfile.RICH:
        mult *= 1.30
    elif profile == ClubTransferProfile.SELLING_CLUB and player.age <= 22:
        mult *= 1.40

    return max(50_000, round(mkt * mult))


def should_accept_transfer_offer(
    team: Team,
    player: Player,
    offer_amount: int,
    profile: ClubTransferProfile = ClubTransferProfile.BALANCED,
    seed: int | None = None,
) -> bool:
    """Determina se a CPU aceita ou recusa uma oferta de transferência por um jogador."""

    # 1. Se oferta pagar a cláusula contratual e contrato ativo: aceita
    if player.contract.years_remaining > 0 and player.contract.release_clause > 0:
        if offer_amount >= player.contract.release_clause:
            return True

    # 2. Se jogador bloqueado para venda comum e oferta < cláusula: recusa
    if not player.contract.can_be_transferred:
        return False

    asking = calculate_cpu_asking_price(team, player, profile)

    if offer_amount < asking:
        return False

    if offer_amount >= asking * 1.3:
        return True

    # Faixa intermediária: RNG determinístico com alta probabilidade
    if seed is not None:
        rng_seed = combine_seed(seed, team.name, player.name, namespace="cpu-transfer-accept")
    else:
        rng_seed = stable_composite_seed((team.name, player.name), namespace="cpu-transfer-accept")
    rng = Random(rng_seed)
    return rng.random() <= 0.80


def evaluate_team_needs(team: Team, series: str = "D") -> list[TransferNeed]:
    """Identifica posições carentes no elenco de um clube da CPU."""

    needs: list[TransferNeed] = []
    expected_ovr = SERIES_EXPECTED_OVERALL.get(series.upper(), 50)
    max_price = round(team.budget * 0.40)

    # 1. Checa goleiros (mínimo de 2 goleiros)
    gks = [p for p in team.players if p.position == PlayerPosition.GOALKEEPER]
    if len(gks) < 2:
        needs.append(
            TransferNeed(
                position=PlayerPosition.GOALKEEPER,
                priority=90,
                target_min_overall=expected_ovr - 5,
                max_price=max_price,
                reason="Carência de goleiros reserva no elenco.",
            )
        )

    # 2. Checa média por posição
    for pos in (PlayerPosition.DEFENDER, PlayerPosition.MIDFIELDER, PlayerPosition.FORWARD):
        pos_players = [p for p in team.players if p.position == pos]
        if not pos_players:
            avg_ovr = 0
        else:
            avg_ovr = sum(p.overall for p in pos_players) / len(pos_players)

        if avg_ovr < expected_ovr - 3:
            needs.append(
                TransferNeed(
                    position=pos,
                    priority=70,
                    target_min_overall=expected_ovr,
                    max_price=max_price,
                    reason=f"Nível da posição {pos.value} abaixo da média da Série {series}.",
                )
            )

    return needs


def select_cpu_purchase_targets(
    buying_team: Team,
    candidate_listings: list[TransferListing],
    profile: ClubTransferProfile,
    needs: list[TransferNeed],
    max_targets: int = 2,
    seed: int | None = None,
) -> list[TransferListing]:
    """Seleciona alvos compatíveis no mercado para suprir as necessidades da CPU."""

    if not needs or buying_team.budget <= 0:
        return []

    spending_ratio = PROFILE_SPENDING_CAP_RATIO.get(profile.value, 0.40)
    available_spending = round(buying_team.budget * spending_ratio)

    selected: list[TransferListing] = []
    current_spent = 0

    sorted_needs = sorted(needs, key=lambda n: n.priority, reverse=True)

    for need in sorted_needs:
        if len(selected) >= max_targets:
            break

        matching = [
            l
            for l in candidate_listings
            if l.player.position == need.position
            and l.seller_team_name != buying_team.name
            and l.asking_price <= (available_spending - current_spent)
            and l.player.overall >= need.target_min_overall - 4
        ]

        if not matching:
            continue

        # Ordena candidatos conforme perfil
        if profile == ClubTransferProfile.YOUTH_FOCUSED:
            matching.sort(key=lambda l: (l.player.age, -l.player.overall))
        elif profile == ClubTransferProfile.WIN_NOW:
            matching.sort(key=lambda l: -l.player.overall)
        elif profile == ClubTransferProfile.SMALL_CLUB:
            matching.sort(key=lambda l: l.asking_price)
        else:
            matching.sort(key=lambda l: -l.player.overall)

        chosen = matching[0]
        selected.append(chosen)
        current_spent += chosen.asking_price

    return selected


def execute_cpu_transfer_window(
    teams: list[Team],
    human_team_name: str,
    league_tiers_by_team: dict[str, str],
    seed: int | None = None,
) -> CpuTransferPlan:
    """Executa a janela de transferências puramente entre os clubes da CPU."""

    plan = CpuTransferPlan()
    rng = Random(seed if seed is not None else 42)

    teams_map = {t.name: t for t in teams}
    cpu_teams = [t for t in teams if t.name != human_team_name]

    if len(cpu_teams) < 2:
        return plan

    recently_transferred: set[str] = set()

    for buyer in cpu_teams:
        # Se elenco da CPU já estiver cheio (>=30) ou saúde salarial for CRITICAL, ignora compras
        from garfoot.domain.squad_rules import calculate_wage_commitment, classify_wage_health, WageHealth
        if len(buyer.players) >= 30 or classify_wage_health(calculate_wage_commitment(buyer)) == WageHealth.CRITICAL:
            continue

        series = league_tiers_by_team.get(buyer.name, "D")
        profile = infer_club_transfer_profile(buyer, series=series)
        needs = evaluate_team_needs(buyer, series=series)

        if not needs:
            continue

        # Gera mercado disponível no momento
        seller_candidates: list[TransferListing] = []
        for seller in cpu_teams:
            if seller.name == buyer.name:
                continue
            seller_series = league_tiers_by_team.get(seller.name, "D")
            seller_prof = infer_club_transfer_profile(seller, series=seller_series)

            starters = set(seller.starting_player_names)
            for p in seller.players:
                if p.name in starters or p.name in recently_transferred:
                    continue
                if not p.contract.can_be_transferred:
                    continue

                asking = calculate_cpu_asking_price(seller, p, seller_prof)
                seller_candidates.append(
                    TransferListing(player=p, seller_team_name=seller.name, asking_price=asking)
                )

        targets = select_cpu_purchase_targets(
            buying_team=buyer,
            candidate_listings=seller_candidates,
            profile=profile,
            needs=needs,
            max_targets=1,
            seed=rng.randint(1, 100_000),
        )

        for target in targets:
            seller = teams_map.get(target.seller_team_name)
            if not seller:
                continue

            seller_prof = infer_club_transfer_profile(seller, series=league_tiers_by_team.get(seller.name, "D"))

            # Valida aceite do vendedor
            if should_accept_transfer_offer(
                team=seller,
                player=target.player,
                offer_amount=target.asking_price,
                profile=seller_prof,
                seed=rng.randint(1, 100_000),
            ):
                try:
                    execute_player_purchase(buyer, seller, target, is_cpu_auto=True, human_team_name=human_team_name)
                    recently_transferred.add(target.player.name)

                    log = CpuTransferLog(
                        buyer_team_name=buyer.name,
                        seller_team_name=seller.name,
                        player_name=target.player.name,
                        amount=target.asking_price,
                        transfer_type="negotiated",
                    )
                    plan.executed_transfers.append(log)
                    plan.messages.append(
                        f"{buyer.name} contratou {target.player.name} de {seller.name} por R$ {target.asking_price:,}."
                    )
                except ValueError:
                    plan.rejected_offers_count += 1
            else:
                plan.rejected_offers_count += 1

    return plan
