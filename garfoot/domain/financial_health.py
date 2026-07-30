"""Módulo puro de saúde financeira, crise e fair play financeiro dos clubes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FinancialHealthStatus(StrEnum):
    """Classificação da saúde financeira geral do clube."""

    HEALTHY = "healthy"
    ATTENTION = "attention"
    PRESSURED = "pressured"
    CRISIS = "crisis"
    INSOLVENT = "insolvent"


class FinancialPenaltyType(StrEnum):
    """Tipos de penalidades aplicáveis por crise financeira."""

    WARNING = "warning"
    TRANSFER_RESTRICTION = "transfer_restriction"
    WAGE_RESTRICTION = "wage_restriction"
    MORALE_PENALTY = "morale_penalty"
    POINTS_DEDUCTION = "points_deduction"


# Limites financeiros para restrição de mercado em crise (por série)
CRISIS_TRANSFER_CAP: dict[str, int] = {
    "A": 3_000_000,
    "B": 1_000_000,
    "C": 400_000,
    "D": 150_000,
}


@dataclass(slots=True)
class ClubFinancialState:
    """Estado persistente dos contadores de crise financeira do clube."""

    consecutive_negative_rounds: int = 0
    consecutive_crisis_rounds: int = 0
    transfer_restriction_rounds: int = 0
    wage_restriction_rounds: int = 0
    points_deducted_this_season: int = 0
    last_health_status: FinancialHealthStatus = FinancialHealthStatus.HEALTHY

    def to_dict(self) -> dict[str, Any]:
        return {
            "consecutive_negative_rounds": self.consecutive_negative_rounds,
            "consecutive_crisis_rounds": self.consecutive_crisis_rounds,
            "transfer_restriction_rounds": self.transfer_restriction_rounds,
            "wage_restriction_rounds": self.wage_restriction_rounds,
            "points_deducted_this_season": self.points_deducted_this_season,
            "last_health_status": str(self.last_health_status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ClubFinancialState:
        """Desserialização retrocompatível com fallback saudável."""

        if not data or not isinstance(data, dict):
            return cls()
        try:
            status = FinancialHealthStatus(str(data.get("last_health_status", "healthy")))
        except ValueError:
            status = FinancialHealthStatus.HEALTHY
        return cls(
            consecutive_negative_rounds=int(data.get("consecutive_negative_rounds", 0)),
            consecutive_crisis_rounds=int(data.get("consecutive_crisis_rounds", 0)),
            transfer_restriction_rounds=int(data.get("transfer_restriction_rounds", 0)),
            wage_restriction_rounds=int(data.get("wage_restriction_rounds", 0)),
            points_deducted_this_season=int(data.get("points_deducted_this_season", 0)),
            last_health_status=status,
        )


@dataclass(frozen=True, slots=True)
class FinancialHealthReport:
    """Relatório diagnóstico de saúde financeira do clube (calculado sob demanda)."""

    team_name: str
    status: FinancialHealthStatus
    score: int
    budget: int
    wage_commitment: float
    operating_burn_rate: int
    projected_rounds_until_cashout: int | None
    warnings: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    active_penalties: tuple[FinancialPenaltyType, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "team_name": self.team_name,
            "status": str(self.status),
            "score": self.score,
            "budget": self.budget,
            "wage_commitment": self.wage_commitment,
            "operating_burn_rate": self.operating_burn_rate,
            "projected_rounds_until_cashout": self.projected_rounds_until_cashout,
            "warnings": list(self.warnings),
            "recommended_actions": list(self.recommended_actions),
            "active_penalties": [str(p) for p in self.active_penalties],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FinancialHealthReport:
        return cls(
            team_name=str(data["team_name"]),
            status=FinancialHealthStatus(str(data.get("status", "healthy"))),
            score=int(data.get("score", 100)),
            budget=int(data.get("budget", 0)),
            wage_commitment=float(data.get("wage_commitment", 0.0)),
            operating_burn_rate=int(data.get("operating_burn_rate", 0)),
            projected_rounds_until_cashout=data.get("projected_rounds_until_cashout"),
            warnings=tuple(data.get("warnings", [])),
            recommended_actions=tuple(data.get("recommended_actions", [])),
            active_penalties=tuple(
                FinancialPenaltyType(str(p)) for p in data.get("active_penalties", [])
            ),
        )


# ---------------------------------------------------------------------------
# Funções puras de classificação e cálculo
# ---------------------------------------------------------------------------


def classify_financial_health(score: int) -> FinancialHealthStatus:
    """Mapeia um score numérico (0–100) para a classificação de saúde financeira."""

    if score >= 80:
        return FinancialHealthStatus.HEALTHY
    elif score >= 60:
        return FinancialHealthStatus.ATTENTION
    elif score >= 40:
        return FinancialHealthStatus.PRESSURED
    elif score >= 20:
        return FinancialHealthStatus.CRISIS
    else:
        return FinancialHealthStatus.INSOLVENT


def calculate_financial_health_report(
    team: Any,
    wage_commitment: float,
    operating_burn_rate: int,
    recurring_income_per_round: int = 0,
    loan_installments_per_round: int = 0,
    financial_state: ClubFinancialState | None = None,
) -> FinancialHealthReport:
    """Calcula puramente o relatório de saúde financeira do clube."""

    from garfoot.domain.squad_rules import WageHealth, classify_wage_health

    budget: int = getattr(team, "budget", 0)
    state = financial_state or ClubFinancialState()
    score = 100
    warnings: list[str] = []
    actions: list[str] = []

    # --- Fator 1: Orçamento negativo ---
    if budget < -5_000_000:
        score -= 50
        warnings.append(f"Caixa extremamente negativo: R$ {budget:,}.")
        actions.append("Venda jogadores imediatamente para cobrir o déficit.")
    elif budget < -1_000_000:
        score -= 35
        warnings.append(f"Caixa muito negativo: R$ {budget:,}.")
        actions.append("Reduza despesas ou venda jogadores para equilibrar o caixa.")
    elif budget < 0:
        score -= 25
        warnings.append(f"Caixa negativo: R$ {budget:,}.")
        actions.append("Atenção ao orçamento: receitas abaixo das despesas.")

    # --- Fator 2: Folha salarial ---
    wage_health = classify_wage_health(wage_commitment)
    if wage_health == WageHealth.CRITICAL:
        score -= 35
        warnings.append("Folha salarial em estado CRÍTICO (>90% das receitas).")
        actions.append("Venda jogadores de alto salário para reduzir a folha.")
    elif wage_health == WageHealth.PRESSURED:
        score -= 20
        warnings.append("Folha salarial PRESSIONADA (>70% das receitas).")
        actions.append("Evite contratar jogadores com salários altos.")
    elif wage_health == WageHealth.ATTENTION:
        score -= 10
        warnings.append("Folha salarial em ATENÇÃO (>50% das receitas).")

    # --- Fator 3: Burn rate vs receitas recorrentes ---
    total_costs_per_round = operating_burn_rate + loan_installments_per_round
    if recurring_income_per_round > 0 and total_costs_per_round > recurring_income_per_round * 2:
        score -= 20
        warnings.append("Despesas por rodada muito acima das receitas recorrentes.")
        actions.append("Renegocie contratos de patrocínio ou reduza gastos operacionais.")
    elif recurring_income_per_round > 0 and total_costs_per_round > recurring_income_per_round:
        score -= 10
        warnings.append("Despesas por rodada superam receitas recorrentes.")

    # --- Fator 4: Rodadas consecutivas com orçamento negativo ---
    neg_rounds = state.consecutive_negative_rounds
    if neg_rounds >= 10:
        score -= 35
        warnings.append(f"Orçamento negativo por {neg_rounds} rodadas consecutivas.")
    elif neg_rounds >= 6:
        score -= 20
        warnings.append(f"Orçamento negativo por {neg_rounds} rodadas consecutivas.")
    elif neg_rounds >= 3:
        score -= 10
        warnings.append(f"Orçamento negativo por {neg_rounds} rodadas consecutivas.")

    # --- Fator 5: Inadimplência em parcelas de empréstimo ---
    if loan_installments_per_round > 0 and recurring_income_per_round > 0:
        loan_ratio = loan_installments_per_round / float(recurring_income_per_round)
        if loan_ratio > 0.40:
            score -= 10
            warnings.append("Parcelas de empréstimo consomem mais de 40% da receita recorrente.")

    score = max(0, min(100, score))
    status = classify_financial_health(score)

    # --- Projeção de rodadas até quebrar ---
    projected_cashout: int | None = None
    net_per_round = recurring_income_per_round - total_costs_per_round
    if net_per_round < 0 and budget > 0:
        projected_cashout = max(0, budget // abs(net_per_round))
    elif budget < 0:
        projected_cashout = 0

    # --- Penalidades ativas ---
    penalties: list[FinancialPenaltyType] = []
    if status in (FinancialHealthStatus.CRISIS, FinancialHealthStatus.INSOLVENT):
        penalties.append(FinancialPenaltyType.WARNING)
    if state.transfer_restriction_rounds > 0:
        penalties.append(FinancialPenaltyType.TRANSFER_RESTRICTION)
    if state.wage_restriction_rounds > 0:
        penalties.append(FinancialPenaltyType.WAGE_RESTRICTION)

    return FinancialHealthReport(
        team_name=getattr(team, "name", ""),
        status=status,
        score=score,
        budget=budget,
        wage_commitment=wage_commitment,
        operating_burn_rate=operating_burn_rate,
        projected_rounds_until_cashout=projected_cashout,
        warnings=tuple(warnings),
        recommended_actions=tuple(actions),
        active_penalties=tuple(penalties),
    )


def update_club_financial_state(
    previous_state: ClubFinancialState,
    report: FinancialHealthReport,
) -> ClubFinancialState:
    """Atualiza os contadores de crise com base no relatório da rodada atual."""

    # Contadores de caixa negativo
    if report.budget < 0:
        new_neg_rounds = previous_state.consecutive_negative_rounds + 1
    else:
        new_neg_rounds = 0  # Zera se voltou ao positivo

    # Contadores de crise/insolvência
    is_crisis_or_worse = report.status in (
        FinancialHealthStatus.CRISIS,
        FinancialHealthStatus.INSOLVENT,
    )
    if is_crisis_or_worse:
        new_crisis_rounds = previous_state.consecutive_crisis_rounds + 1
    else:
        new_crisis_rounds = max(0, previous_state.consecutive_crisis_rounds - 1)

    # Reduz contadores de restrição ativa
    new_transfer_restriction = max(0, previous_state.transfer_restriction_rounds - 1)
    new_wage_restriction = max(0, previous_state.wage_restriction_rounds - 1)

    # Reset de points_deducted ao mudar de temporada é responsabilidade do orquestrador
    return ClubFinancialState(
        consecutive_negative_rounds=new_neg_rounds,
        consecutive_crisis_rounds=new_crisis_rounds,
        transfer_restriction_rounds=new_transfer_restriction,
        wage_restriction_rounds=new_wage_restriction,
        points_deducted_this_season=previous_state.points_deducted_this_season,
        last_health_status=report.status,
    )


def determine_financial_penalties(
    report: FinancialHealthReport,
    state: ClubFinancialState,
) -> tuple[FinancialPenaltyType, ...]:
    """Determina quais penalidades devem ser aplicadas com base no status e contadores."""

    penalties: list[FinancialPenaltyType] = []

    # Aviso simples para atenção/pressão
    if report.status in (FinancialHealthStatus.ATTENTION, FinancialHealthStatus.PRESSURED):
        penalties.append(FinancialPenaltyType.WARNING)

    # Crise persistente: penalidade de moral
    if (
        report.status in (FinancialHealthStatus.CRISIS, FinancialHealthStatus.INSOLVENT)
        and state.consecutive_crisis_rounds >= 3
    ):
        penalties.append(FinancialPenaltyType.MORALE_PENALTY)

    # Insolvência persistente: restrição de mercado
    if report.status == FinancialHealthStatus.INSOLVENT and state.consecutive_crisis_rounds >= 3:
        penalties.append(FinancialPenaltyType.TRANSFER_RESTRICTION)

    # Insolvência prolongada: possível perda de pontos (no máximo uma vez por temporada)
    if (
        report.status == FinancialHealthStatus.INSOLVENT
        and state.consecutive_crisis_rounds >= 6
        and state.points_deducted_this_season == 0
    ):
        penalties.append(FinancialPenaltyType.POINTS_DEDUCTION)

    return tuple(penalties)


def apply_financial_morale_penalty(team: Any, penalty_points: int) -> None:
    """Aplica redução de moral a todos os jogadores do elenco (puro, sem I/O)."""

    for player in getattr(team, "players", []):
        if hasattr(player, "adjust_morale"):
            player.adjust_morale(-abs(penalty_points))
        elif hasattr(player, "morale"):
            player.morale = max(0, player.morale - abs(penalty_points))


def can_register_transfer_under_financial_rules(
    team: Any,
    transfer_cost: int,
    new_salary: int,
    report: FinancialHealthReport,
    series: str = "D",
) -> tuple[bool, str]:
    """Verifica se o clube pode registrar uma compra sob as regras de fair play financeiro."""

    # Restrição ativa bloqueia qualquer compra paga
    if FinancialPenaltyType.TRANSFER_RESTRICTION in report.active_penalties:
        return False, "Clube com restrição de mercado ativa por insolvência financeira."

    if report.status == FinancialHealthStatus.INSOLVENT:
        if transfer_cost > 0:
            return False, "Clube insolvente não pode realizar compras pagas. Apenas contratações gratuitas emergenciais."

    if report.status == FinancialHealthStatus.CRISIS:
        cap = CRISIS_TRANSFER_CAP.get(series.upper(), 150_000)
        if transfer_cost > cap:
            return (
                False,
                f"Clube em crise financeira: compras limitadas a R$ {cap:,} por transação.",
            )

    return True, "Elegível."


def can_start_stadium_upgrade_under_financial_rules(
    team: Any,
    upgrade_cost: int,
    report: FinancialHealthReport,
) -> tuple[bool, str]:
    """Verifica se o clube pode iniciar um upgrade de estádio sob as regras financeiras."""

    if report.status == FinancialHealthStatus.INSOLVENT:
        return False, "Clube insolvente não pode realizar expansões de estádio."

    if report.status == FinancialHealthStatus.CRISIS:
        budget = getattr(team, "budget", 0)
        # Bloqueia se upgrade consome mais de 50% do caixa restante
        if upgrade_cost > max(0, budget) * 0.50 or budget <= 0:
            return (
                False,
                "Clube em crise financeira: expansão de estádio bloqueada para preservar caixa.",
            )

    return True, "Elegível."


def can_take_loan_under_financial_rules(
    team: Any,
    report: FinancialHealthReport,
    existing_loan: Any | None = None,
) -> tuple[bool, str]:
    """Verifica se o clube pode contrair novo empréstimo dado o status financeiro."""

    if existing_loan is not None and not getattr(existing_loan, "is_fully_paid", True):
        return False, "Já existe um empréstimo ativo. Quite o débito antes de solicitar novo crédito."

    if report.status == FinancialHealthStatus.INSOLVENT:
        return False, "Clube insolvente não tem crédito disponível."

    return True, "Elegível para empréstimo."


def should_cpu_sell_under_financial_pressure(
    report: FinancialHealthReport,
) -> bool:
    """Retorna True se a CPU deve priorizar vendas em função do status financeiro."""

    return report.status in (FinancialHealthStatus.CRISIS, FinancialHealthStatus.INSOLVENT)


def should_cpu_avoid_purchases_under_financial_pressure(
    report: FinancialHealthReport,
) -> bool:
    """Retorna True se a CPU deve evitar compras em função do status financeiro."""

    return report.status in (
        FinancialHealthStatus.PRESSURED,
        FinancialHealthStatus.CRISIS,
        FinancialHealthStatus.INSOLVENT,
    )
