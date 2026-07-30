"""Módulo puro para ciclo de vida dos contratos, renovações, expirações e jogadores livres."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from random import Random
from typing import Any

from garfoot.domain.contract import Contract
from garfoot.domain.economy import calculate_initial_salary, calculate_release_clause
from garfoot.domain.player import Player
from garfoot.domain.squad_rules import (
    can_add_player_to_squad,
    can_afford_new_salary,
)
from garfoot.domain.stable_random import combine_seed, stable_composite_seed
from garfoot.domain.team import Team


@dataclass(slots=True)
class ContractSeasonResult:
    """Relatório resumido dos eventos contratuais ao término da temporada."""

    renewed_players: list[tuple[str, str, int]] = field(default_factory=list)  # (team, player, years)
    expired_to_free_agents: list[tuple[str, str]] = field(default_factory=list)  # (team, player)
    human_team_expired_warnings: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FreeAgentPool:
    """Pool centralizado de jogadores sem contrato ativo (Free Agents)."""

    players: list[Player] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"players": [p.to_dict() for p in self.players]}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> FreeAgentPool:
        if not data or not isinstance(data, dict):
            return cls()
        players = [Player.from_dict(p) for p in data.get("players", []) if isinstance(p, dict)]
        return cls(players=players)


def advance_player_contract(player: Player) -> Player:
    """Reduz em 1 ano o contrato vigente do jogador ao final da temporada.

    Se os anos zerarem (years_remaining == 0), desativa cláusula e proteção.
    """

    curr_years = player.contract.years_remaining
    if curr_years <= 0:
        return player

    new_years = max(0, curr_years - 1)
    new_protected = player.contract.is_protected if new_years > 0 else False
    new_prot_years = max(0, player.contract.protection_years - 1) if new_years > 0 else 0
    new_clause = player.contract.release_clause if new_years > 0 else 0

    new_contract = Contract(
        years_remaining=new_years,
        is_protected=new_protected,
        protection_years=new_prot_years,
        release_clause=new_clause,
    )

    return replace(player, contract=new_contract)


def advance_team_contracts(team: Team) -> Team:
    """Aplica o avanço de 1 ano de contrato em todos os jogadores do clube."""

    updated_players = [advance_player_contract(p) for p in team.players]
    return replace(team, players=updated_players)


def renew_player_contract(
    player: Player,
    years: int,
    economic_context: Any | None = None,
    is_protected: bool = False,
    protection_years: int = 0,
) -> Player:
    """Recalcula e renova o contrato do jogador por 'years' anos.

    Recalcula valor de mercado, novo salário e nova cláusula de rescisão.
    """

    if years < 1 or years > 5:
        raise ValueError("A duração da renovação contratual deve ficar entre 1 e 5 anos.")

    econ_idx = (
        economic_context.economic_index
        if economic_context and hasattr(economic_context, "economic_index")
        else 1.0
    )

    from garfoot.domain.economy import calculate_player_market_value
    new_mkt = calculate_player_market_value(
        overall=player.overall,
        age=player.age,
        position=player.position,
        economic_index=econ_idx,
    )
    new_salary = calculate_initial_salary(new_mkt)

    new_clause = calculate_release_clause(
        market_value=new_mkt,
        overall=player.overall,
        age=player.age,
        years_remaining=years,
        is_protected=is_protected,
    )

    new_contract = Contract(
        years_remaining=years,
        is_protected=is_protected,
        protection_years=protection_years,
        release_clause=new_clause,
    )

    return replace(
        player,
        contract=new_contract,
        salary=new_salary,
        value=new_mkt,
    )


def should_cpu_renew_contract(
    team: Team,
    player: Player,
    seed: int | None = None,
) -> bool:
    """Avalia se um clube da CPU deve renovar o contrato de um jogador prestes a expirar."""

    # Se ainda restar mais de 1 ano de contrato, não precisa renovar agora
    if player.contract.years_remaining > 1:
        return True

    starters = set(team.starting_player_names)
    is_starter = player.name in starters

    # Fatores decisivos
    if is_starter:
        return True

    if player.age <= 22 and player.overall >= 60:
        return True

    if player.age >= 34 and not is_starter:
        return False

    if player.overall < team.squad_strength - 8:
        return False

    if seed is not None:
        rng_seed = combine_seed(seed, team.name, player.name, namespace="contract-lifecycle")
    else:
        rng_seed = stable_composite_seed((team.name, player.name), namespace="contract-lifecycle")
    rng = Random(rng_seed)
    return rng.random() <= 0.65


def sign_free_agent(
    team: Team,
    player: Player,
    years: int = 3,
    signing_bonus: int = 0,
    economic_context: Any | None = None,
) -> tuple[Team, Player]:
    """Assina contrato com um jogador livre do mercado de forma atômica e pré-validada."""

    from garfoot.domain.transfer_market import validate_transfer_preconditions
    is_valid, reason, msg = validate_transfer_preconditions(
        buyer_team=team,
        seller_team=None,
        player=player,
        amount=signing_bonus,
        is_release_clause=False,
        is_free_agent=True,
    )
    if not is_valid:
        raise ValueError(msg)

    signed_player = renew_player_contract(
        player=player,
        years=years,
        economic_context=economic_context,
        is_protected=True,
        protection_years=1,
    )

    if signing_bonus > 0:
        team.budget -= signing_bonus

    team.add_player(signed_player)
    return team, signed_player


def process_end_of_season_contracts(
    teams: list[Team],
    human_team_name: str,
    free_agents: list[Player],
    economic_context: Any | None = None,
    seed: int | None = None,
) -> tuple[list[Team], list[Player], ContractSeasonResult]:
    """Orquestra o fim de temporada contratual de todos os clubes e atualiza o pool de jogadores livres."""

    result = ContractSeasonResult()
    rng = Random(seed if seed is not None else 42)
    updated_free_agents = list(free_agents)

    updated_teams: list[Team] = []

    for team in teams:
        adv_team = advance_team_contracts(team)
        is_human = team.name == human_team_name

        remaining_players: list[Player] = []

        for p in adv_team.players:
            if p.contract.years_remaining == 0:
                if is_human:
                    # Time humano: mantém aviso e não remove sem autorização
                    result.human_team_expired_warnings.append(
                        f"ALERTA: O contrato de {p.name} expirou! Renove-o na tela de contratos para não perdê-lo."
                    )
                    remaining_players.append(p)
                else:
                    # Time da CPU: decide se renova ou libera para Free Agent
                    if should_cpu_renew_contract(adv_team, p, seed=rng.randint(1, 100_000)):
                        renewed_p = renew_player_contract(p, years=3, economic_context=economic_context)
                        remaining_players.append(renewed_p)
                        result.renewed_players.append((team.name, p.name, 3))
                    else:
                        # Libera para free agents
                        free_p = replace(p, contract=Contract(years_remaining=0, release_clause=0), salary=0)
                        updated_free_agents.append(free_p)
                        result.expired_to_free_agents.append((team.name, p.name))
            else:
                remaining_players.append(p)

        new_team = replace(adv_team, players=remaining_players)
        updated_teams.append(replace(adv_team, players=remaining_players))

    return updated_teams, updated_free_agents, result


def process_end_of_season_contracts_idempotent(
    teams: list[Team],
    human_team_name: str,
    free_agents: list[Player],
    season_year: int,
    ledger: Any,
    economic_context: Any | None = None,
    seed: int | None = None,
) -> tuple[list[Team], list[Player], ContractSeasonResult]:
    """Processa o encerramento anual de contratos de forma estritamente idempotente via ledger."""

    key = f"contracts:season-end:{season_year}"
    if ledger is not None and hasattr(ledger, "check_and_mark"):
        if not ledger.check_and_mark(key):
            return teams, free_agents, ContractSeasonResult(messages=["Contratos de fim de temporada já haviam sido processados."])

    return process_end_of_season_contracts(
        teams=teams,
        human_team_name=human_team_name,
        free_agents=free_agents,
        economic_context=economic_context,
        seed=seed,
    )
