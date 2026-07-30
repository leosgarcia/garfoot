"""Módulo de gestão financeira, upgrade de estádio e empréstimo bancário."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto
from typing import Any

from garfoot.domain.enums import PlayerPosition
from garfoot.domain.stadium import Stadium
from garfoot.domain.team import Team

# Parâmetros padrão para Upgrade de Estádio
DEFAULT_SEAT_INCREMENT: int = 2_500
DEFAULT_BASE_COST_PER_SEAT: int = 300
DEFAULT_CONSTRUCTION_ROUNDS: int = 6

SERIES_MAX_CAPACITY: dict[str, int] = {
    "D": 25_000,
    "C": 40_000,
    "B": 60_000,
    "A": 90_000,
}

# Parâmetros padrão para Empréstimo Bancário
DEFAULT_LOAN_INTEREST_RATE: float = 0.15  # 15% de juros totais sobre o montante
DEFAULT_LOAN_INSTALLMENTS: int = 10       # 10 rodadas para quitar
DEFAULT_LATE_FEE_RATE: float = 0.05       # 5% de multa por parcela em atraso

SERIES_LOAN_FACTOR: dict[str, float] = {
    "D": 0.60,
    "C": 0.80,
    "B": 1.00,
    "A": 1.20,
}


@dataclass(frozen=True, slots=True)
class StadiumUpgradeProject:
    """Representa uma obra em andamento no estádio do clube."""

    additional_seats: int
    cost: int
    rounds_remaining: int

    def __post_init__(self) -> None:
        if self.additional_seats <= 0:
            raise ValueError("O número de assentos adicionais deve ser positivo.")
        if self.cost <= 0:
            raise ValueError("O custo da obra deve ser positivo.")
        if self.rounds_remaining < 0:
            raise ValueError("O número de rodadas restantes não pode ser negativo.")

    @property
    def is_completed(self) -> bool:
        return self.rounds_remaining == 0


@dataclass(frozen=True, slots=True)
class BankLoan:
    """Representa um empréstimo bancário ativo com parcelamento por rodada."""

    original_amount: int
    total_amount_with_interest: int
    installment_amount: int
    total_installments: int
    remaining_installments: int
    unpaid_installments: int = 0

    def __post_init__(self) -> None:
        if self.original_amount <= 0:
            raise ValueError("O valor do empréstimo deve ser positivo.")
        if self.installment_amount <= 0:
            raise ValueError("O valor da parcela deve ser positivo.")
        if self.total_installments <= 0 or self.remaining_installments < 0:
            raise ValueError("Número de parcelas inválido.")

    @property
    def is_fully_paid(self) -> bool:
        return self.remaining_installments == 0 and self.unpaid_installments == 0


# --- Fórmulas Puras de Upgrade de Estádio ---

def calculate_upgrade_cost(
    current_capacity: int,
    additional_seats: int = DEFAULT_SEAT_INCREMENT,
    base_cost_per_seat: int = DEFAULT_BASE_COST_PER_SEAT,
    economic_index: float = 1.0,
) -> int:
    """Calcula o custo total para expandir a capacidade do estádio ajustado pelo índice econômico.

    O custo por assento aumenta progressivamente conforme o estádio já é grande.
    """

    cost_multiplier = 1.0 + (current_capacity / 100_000.0)
    total_cost = round(base_cost_per_seat * additional_seats * cost_multiplier * economic_index)
    return total_cost


def can_upgrade_stadium(
    current_capacity: int,
    series: str,
    active_project: StadiumUpgradeProject | None = None,
) -> tuple[bool, str]:
    """Verifica se o estádio pode receber uma nova obra de ampliação.

    Se a capacidade inicial já for maior que o teto da divisão (direitos adquiridos),
    o clube preserva sua capacidade, mas não pode expandir mais até subir de série.
    """

    if active_project is not None and not active_project.is_completed:
        return False, "Já existe uma obra de ampliação em andamento no estádio."

    max_cap = SERIES_MAX_CAPACITY.get(series.upper(), 90_000)
    if current_capacity >= max_cap:
        return (
            False,
            f"A capacidade atual ({current_capacity:,}) já atingiu ou superou o teto da Série {series} ({max_cap:,}).",
        )

    return True, "Elegível para upgrade."


def start_stadium_upgrade(
    team: Team,
    series: str,
    additional_seats: int = DEFAULT_SEAT_INCREMENT,
    active_project: StadiumUpgradeProject | None = None,
    economic_index: float = 1.0,
) -> tuple[Team, StadiumUpgradeProject]:
    """Inicia o projeto de expansão do estádio e debita o custo do orçamento."""

    if team.stadium is None:
        raise ValueError("O time não possui estádio para realizar upgrade.")

    eligible, reason = can_upgrade_stadium(team.stadium.capacity, series, active_project)
    if not eligible:
        raise ValueError(reason)

    cost = calculate_upgrade_cost(team.stadium.capacity, additional_seats, economic_index=economic_index)
    if team.budget < cost:
        raise ValueError(f"Orçamento insuficiente. Custo: R$ {cost:,}, Caixa: R$ {team.budget:,}.")

    # Debita orçamento
    team.budget -= cost

    project = StadiumUpgradeProject(
        additional_seats=additional_seats,
        cost=cost,
        rounds_remaining=DEFAULT_CONSTRUCTION_ROUNDS,
    )
    return team, project


# --- Fórmulas Puras de Empréstimo Bancário ---

def calculate_max_loan_amount(team: Team, series: str) -> int:
    """Calcula o limite máximo de crédito que o time pode tomar emprestado."""

    annual_income = team.estimate_home_income() * 19  # 19 jogos de mando
    factor = SERIES_LOAN_FACTOR.get(series.upper(), 0.60)
    limit = round(annual_income * factor)
    return max(300_000, limit)


def take_bank_loan(
    team: Team,
    series: str,
    amount_requested: int,
    active_loan: BankLoan | None = None,
    interest_rate: float = DEFAULT_LOAN_INTEREST_RATE,
    installments: int = DEFAULT_LOAN_INSTALLMENTS,
) -> tuple[Team, BankLoan]:
    """Concede um empréstimo ao time, injetando caixa e criando a dívida parcelada."""

    if active_loan is not None and not active_loan.is_fully_paid:
        raise ValueError("O clube já possui um empréstimo bancário em andamento.")

    max_amount = calculate_max_loan_amount(team, series)
    if amount_requested > max_amount:
        raise ValueError(f"Valor solicitado (R$ {amount_requested:,}) excede o limite de crédito (R$ {max_amount:,}).")

    if amount_requested <= 0:
        raise ValueError("O valor do empréstimo deve ser positivo.")

    total_with_interest = round(amount_requested * (1.0 + interest_rate))
    installment_val = round(total_with_interest / installments)

    # Injeta caixa no time
    team.budget += amount_requested

    loan = BankLoan(
        original_amount=amount_requested,
        total_amount_with_interest=total_with_interest,
        installment_amount=installment_val,
        total_installments=installments,
        remaining_installments=installments,
        unpaid_installments=0,
    )
    return team, loan


# --- Processamento Financeiro Pós-Rodada ---

def process_round_finances(
    team: Team,
    upgrade_project: StadiumUpgradeProject | None = None,
    active_loan: BankLoan | None = None,
) -> tuple[Team, StadiumUpgradeProject | None, BankLoan | None, list[str]]:
    """Processa cobrança de parcelas de empréstimo e avanço de obras do estádio pós-rodada."""

    messages: list[str] = []

    # 1. Avanço de Obra do Estádio
    updated_project = upgrade_project
    if upgrade_project is not None and not upgrade_project.is_completed:
        rounds_left = upgrade_project.rounds_remaining - 1
        updated_project = StadiumUpgradeProject(
            additional_seats=upgrade_project.additional_seats,
            cost=upgrade_project.cost,
            rounds_remaining=rounds_left,
        )

        if rounds_left == 0 and team.stadium is not None:
            # Conclui a obra e expande a capacidade
            new_cap = team.stadium.capacity + upgrade_project.additional_seats
            team.stadium = Stadium(
                name=team.stadium.name,
                city=team.stadium.city,
                capacity=new_cap,
                average_ticket_price=team.stadium.average_ticket_price,
            )
            messages.append(f"Obras concluídas! A capacidade do {team.stadium.name} subiu para {new_cap:,} lugares.")
        else:
            messages.append(f"Obra do estádio em andamento: faltam {rounds_left} rodadas.")

    # 2. Desconto da Parcela do Empréstimo
    updated_loan = active_loan
    if active_loan is not None and not active_loan.is_fully_paid:
        due_amount = active_loan.installment_amount

        # Se houver parcelas em atraso anteriores, adiciona multa de 5%
        if active_loan.unpaid_installments > 0:
            due_amount = round(due_amount * (1.0 + DEFAULT_LATE_FEE_RATE))

        if team.budget >= due_amount:
            # Paga a parcela
            team.budget -= due_amount
            rem_installments = active_loan.remaining_installments - 1
            unpaid = max(0, active_loan.unpaid_installments - 1)

            updated_loan = BankLoan(
                original_amount=active_loan.original_amount,
                total_amount_with_interest=active_loan.total_amount_with_interest,
                installment_amount=active_loan.installment_amount,
                total_installments=active_loan.total_installments,
                remaining_installments=rem_installments,
                unpaid_installments=unpaid,
            )
            messages.append(f"Parcela de empréstimo paga: R$ {due_amount:,} debitados.")
        else:
            # Inadimplência
            unpaid = active_loan.unpaid_installments + 1
            updated_loan = BankLoan(
                original_amount=active_loan.original_amount,
                total_amount_with_interest=active_loan.total_amount_with_interest,
                installment_amount=active_loan.installment_amount,
                total_installments=active_loan.total_installments,
                remaining_installments=active_loan.remaining_installments,
                unpaid_installments=unpaid,
            )
            # Reduz levemente a moral do elenco por instabilidade financeira
            for player in team.players:
                player.adjust_morale(-2)
            messages.append(f"ALERTA: Caixa insuficiente para pagar parcela de R$ {due_amount:,}. Mora aplicada!")

    return team, updated_project, updated_loan, messages
