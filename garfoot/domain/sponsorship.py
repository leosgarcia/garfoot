"""Modelo e regras de patrocínios e receitas comerciais dos clubes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
from random import Random
from typing import Any

from garfoot.domain.club_finance import (
    FINANCIAL_PROFILE_MULTIPLIER,
    ClubFinancialProfile,
    infer_financial_profile,
)
from garfoot.domain.stable_random import combine_seed, stable_int_seed


class SponsorshipType(StrEnum):
    """Tipos de contratos comerciais e de patrocínio."""

    MASTER = "master"
    KIT_SUPPLIER = "kit_supplier"
    STADIUM_PARTNER = "stadium_partner"
    PERFORMANCE_BONUS = "performance_bonus"


SPONSOR_BASE_VALUES: dict[str, dict[SponsorshipType, int]] = {
    "A": {
        SponsorshipType.MASTER: 4_000_000,
        SponsorshipType.KIT_SUPPLIER: 1_500_000,
        SponsorshipType.STADIUM_PARTNER: 800_000,
    },
    "B": {
        SponsorshipType.MASTER: 1_500_000,
        SponsorshipType.KIT_SUPPLIER: 600_000,
        SponsorshipType.STADIUM_PARTNER: 300_000,
    },
    "C": {
        SponsorshipType.MASTER: 600_000,
        SponsorshipType.KIT_SUPPLIER: 250_000,
        SponsorshipType.STADIUM_PARTNER: 100_000,
    },
    "D": {
        SponsorshipType.MASTER: 250_000,
        SponsorshipType.KIT_SUPPLIER: 100_000,
        SponsorshipType.STADIUM_PARTNER: 40_000,
    },
}

SPONSOR_WIN_BONUS: dict[str, int] = {
    "A": 80_000,
    "B": 35_000,
    "C": 15_000,
    "D": 7_500,
}


@dataclass(frozen=True, slots=True)
class SponsorshipContract:
    """Contrato comercial de patrocínio com o clube."""

    sponsor_name: str
    sponsorship_type: SponsorshipType
    annual_value: int
    rounds_remaining: int
    bonus_per_win: int = 0
    bonus_for_title: int = 0
    bonus_for_promotion: int = 0
    bonus_for_top_half: int = 0
    is_active: bool = True

    def value_per_round(self, total_rounds: int = 38) -> int:
        """Calcula a parcela de receita comercial paga por rodada."""

        if total_rounds <= 0 or not self.is_active or self.rounds_remaining <= 0:
            return 0
        return round(self.annual_value / total_rounds)

    def to_dict(self) -> dict[str, Any]:
        """Serialização para persistência em JSON."""

        data = asdict(self)
        data["sponsorship_type"] = self.sponsorship_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SponsorshipContract:
        """Desserialização a partir de dados salvos."""

        payload = dict(data)
        payload["sponsorship_type"] = SponsorshipType(str(payload["sponsorship_type"]))
        return cls(**payload)


@dataclass(slots=True)
class ClubSponsorshipPortfolio:
    """Carteira de contratos de patrocínio ativos e históricos do clube."""

    contracts: list[SponsorshipContract] = field(default_factory=list)

    @property
    def annual_total(self) -> int:
        """Soma do valor anual de todos os contratos ativos."""

        return sum(c.annual_value for c in self.contracts if c.is_active)

    def active_contracts(self) -> list[SponsorshipContract]:
        """Retorna os contratos ativos com rodadas restantes."""

        return [c for c in self.contracts if c.is_active and c.rounds_remaining > 0]

    def to_dict(self) -> dict[str, Any]:
        """Serialização do portfólio para JSON."""

        return {"contracts": [c.to_dict() for c in self.contracts]}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ClubSponsorshipPortfolio:
        """Desserialização retrocompatível de portfólio salvos."""

        if not data or not isinstance(data, dict):
            return cls()
        contracts = [
            SponsorshipContract.from_dict(c)
            for c in data.get("contracts", [])
            if isinstance(c, dict)
        ]
        return cls(contracts=contracts)


def calculate_sponsorship_value(
    sponsorship_type: SponsorshipType,
    series: str = "D",
    profile: ClubFinancialProfile = ClubFinancialProfile.MEDIUM,
    economic_context: Any | None = None,
    performance_multiplier: float = 1.0,
) -> int:
    """Calcula o valor anual de um novo contrato comercial."""

    series_upper = series.upper()
    base = SPONSOR_BASE_VALUES.get(series_upper, SPONSOR_BASE_VALUES["D"]).get(sponsorship_type, 100_000)
    prof_mult = FINANCIAL_PROFILE_MULTIPLIER.get(profile, 1.00)

    econ_index = (
        economic_context.economic_index
        if economic_context and hasattr(economic_context, "economic_index")
        else 1.0
    )

    final_val = round(base * prof_mult * performance_multiplier * econ_index)
    return max(10_000, final_val)


def generate_default_sponsorships_for_team(
    team: Any,
    series: str = "D",
    profile: ClubFinancialProfile | None = None,
    economic_context: Any | None = None,
    seed: int | None = None,
    total_rounds: int = 38,
) -> ClubSponsorshipPortfolio:
    """Gera puramente os contratos comerciais iniciais do clube."""

    prof = profile or infer_financial_profile(team, series=series)
    series_upper = series.upper()

    team_name = str(getattr(team, "name", "Club"))
    if seed is not None:
        rng_seed = combine_seed(seed, team_name, namespace="sponsorship")
    else:
        rng_seed = stable_int_seed(team_name, namespace="sponsorship")
    rng = Random(rng_seed)

    master_names = ["Banco Garfoot", "Bet DOS", "MegaCorp", "Garfoot Pay", "SuperBet"]
    kit_names = ["Penal", "Raik", "Oly", "Adida", "Pum"]

    master_val = calculate_sponsorship_value(
        sponsorship_type=SponsorshipType.MASTER,
        series=series_upper,
        profile=prof,
        economic_context=economic_context,
    )
    win_bonus = SPONSOR_WIN_BONUS.get(series_upper, 7_500)

    master_contract = SponsorshipContract(
        sponsor_name=rng.choice(master_names),
        sponsorship_type=SponsorshipType.MASTER,
        annual_value=master_val,
        rounds_remaining=total_rounds,
        bonus_per_win=win_bonus,
    )

    kit_val = calculate_sponsorship_value(
        sponsorship_type=SponsorshipType.KIT_SUPPLIER,
        series=series_upper,
        profile=prof,
        economic_context=economic_context,
    )

    kit_contract = SponsorshipContract(
        sponsor_name=rng.choice(kit_names),
        sponsorship_type=SponsorshipType.KIT_SUPPLIER,
        annual_value=kit_val,
        rounds_remaining=total_rounds,
    )

    return ClubSponsorshipPortfolio(contracts=[master_contract, kit_contract])


def process_round_sponsorship_income(
    team: Any,
    portfolio: ClubSponsorshipPortfolio,
    total_rounds: int = 38,
) -> tuple[Any, int]:
    """Calcula e credita a receita comercial da rodada no orçamento do clube."""

    round_income = sum(c.value_per_round(total_rounds) for c in portfolio.active_contracts())
    if round_income > 0 and hasattr(team, "budget"):
        team.budget += round_income

    updated_portfolio = advance_sponsorship_rounds(portfolio)
    if hasattr(team, "sponsorships"):
        team.sponsorships = updated_portfolio

    return team, round_income


def process_round_sponsorship_income_idempotent(
    team: Any,
    portfolio: ClubSponsorshipPortfolio,
    season_year: int,
    round_number: int,
    ledger: Any,
    total_rounds: int = 38,
) -> tuple[Any, int]:
    """Credita a receita comercial de patrocínio de forma estritamente idempotente via ledger."""

    team_name = getattr(team, "name", "Club")
    key = f"sponsorship:round-income:{season_year}:{round_number}:{team_name}"
    if ledger is not None and hasattr(ledger, "check_and_mark"):
        if not ledger.check_and_mark(key):
            return team, 0

    return process_round_sponsorship_income(team=team, portfolio=portfolio, total_rounds=total_rounds)


def calculate_sponsorship_match_bonus(
    portfolio: ClubSponsorshipPortfolio,
    is_win: bool = False,
) -> int:
    """Calcula o bônus de vitória previsto nos contratos comerciais."""

    if not is_win:
        return 0
    return sum(c.bonus_per_win for c in portfolio.active_contracts())


def calculate_sponsorship_match_bonus_idempotent(
    portfolio: ClubSponsorshipPortfolio,
    team_name: str,
    match_id: str,
    season_year: int,
    ledger: Any,
    is_win: bool = False,
) -> int:
    """Calcula e aplica o bônus por vitória de patrocínio de forma idempotente via ledger."""

    if not is_win:
        return 0

    key = f"sponsorship:win-bonus:{season_year}:{match_id}:{team_name}"
    if ledger is not None and hasattr(ledger, "check_and_mark"):
        if not ledger.check_and_mark(key):
            return 0

    return calculate_sponsorship_match_bonus(portfolio=portfolio, is_win=True)


def advance_sponsorship_rounds(
    portfolio: ClubSponsorshipPortfolio,
) -> ClubSponsorshipPortfolio:
    """Avança em 1 rodada o tempo de vigência de todos os contratos ativos."""

    updated_contracts: list[SponsorshipContract] = []
    for c in portfolio.contracts:
        if c.is_active and c.rounds_remaining > 0:
            new_rounds = c.rounds_remaining - 1
            new_active = new_rounds > 0
            updated_contracts.append(replace(c, rounds_remaining=new_rounds, is_active=new_active))
        else:
            updated_contracts.append(c)

    return ClubSponsorshipPortfolio(contracts=updated_contracts)
