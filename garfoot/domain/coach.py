"""Modelo e regras puras de treinadores, pressão, demissão, contratação e chicotada psicológica."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from random import Random
from typing import Any

from garfoot.domain.player import MAX_ATTRIBUTE, MIN_ATTRIBUTE
from garfoot.domain.stable_random import stable_int_seed


class CoachStatus(StrEnum):
    """Status atual do treinador no mercado."""

    EMPLOYED = "employed"
    FREE_AGENT = "free_agent"


class CoachStyle(StrEnum):
    """Estilo tático preferido do treinador."""

    BALANCED = "equilibrado"
    DEFENSIVE = "defensivo"
    OFFENSIVE = "ofensivo"
    YOUTH_FOCUSED = "base"
    DISCIPLINARIAN = "disciplinador"


@dataclass(slots=True)
class Coach:
    """Representa um treinador de futebol no domínio."""

    name: str
    reputation: int  # 1 a 100
    tactical_skill: int  # 1 a 100
    morale_management: int  # 1 a 100
    pressure_resistance: int  # 1 a 100
    style: CoachStyle = CoachStyle.BALANCED
    salary: int = 0
    current_team_name: str | None = None
    status: CoachStatus = CoachStatus.FREE_AGENT
    wins: int = 0
    draws: int = 0
    losses: int = 0
    titles: int = 0
    sackings: int = 0

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("O treinador precisa ter um nome.")

        for attr_name in ("reputation", "tactical_skill", "morale_management", "pressure_resistance"):
            val = getattr(self, attr_name)
            if val < MIN_ATTRIBUTE or val > MAX_ATTRIBUTE:
                raise ValueError(f"{attr_name} deve ficar entre {MIN_ATTRIBUTE} e {MAX_ATTRIBUTE}.")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["style"] = self.style.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> Coach | None:
        if not data or not isinstance(data, dict):
            return None

        payload = dict(data)
        payload["status"] = CoachStatus(payload.get("status", CoachStatus.FREE_AGENT.value))
        payload["style"] = CoachStyle(payload.get("style", CoachStyle.BALANCED.value))
        return cls(**payload)


@dataclass(frozen=True, slots=True)
class CoachBounceEffect:
    """Efeito temporário de 'chicotada psicológica' gerado por nova contratação de técnico."""

    rounds_remaining: int
    morale_bonus: float
    rating_bonus: float
    source_coach_name: str

    @property
    def is_active(self) -> bool:
        return self.rounds_remaining > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rounds_remaining": self.rounds_remaining,
            "morale_bonus": self.morale_bonus,
            "rating_bonus": self.rating_bonus,
            "source_coach_name": self.source_coach_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CoachBounceEffect | None:
        if not data or not isinstance(data, dict):
            return None

        return cls(
            rounds_remaining=int(data.get("rounds_remaining", 0)),
            morale_bonus=float(data.get("morale_bonus", 0.0)),
            rating_bonus=float(data.get("rating_bonus", 0.0)),
            source_coach_name=str(data.get("source_coach_name", "")),
        )


def calculate_coach_pressure(
    team_squad_strength: int,
    standing_position: int,
    total_teams: int,
    recent_results: list[str],
    coach_pressure_resistance: int = 50,
) -> int:
    """Calcula o risco/pressão do cargo de treinador de 0 a 100."""

    pressure = 0

    # 1. Posição na tabela e zona de rebaixamento
    if total_teams > 0:
        if standing_position == total_teams:
            pressure += 45  # Lanterna
        elif standing_position > total_teams - 4:
            pressure += 30  # Zona de rebaixamento

    # 2. Sequência de resultados recentes ("W", "D", "L")
    losses_in_row = 0
    for r in reversed(recent_results):
        if r == "L":
            losses_in_row += 1
        else:
            break
    pressure += min(30, losses_in_row * 10)

    winless_streak = 0
    for r in reversed(recent_results):
        if r in ("L", "D"):
            winless_streak += 1
        else:
            break
    if winless_streak >= 5:
        pressure += 15

    # 3. Desempenho vs Força do elenco (se o time é forte mas está em posição ruim)
    if team_squad_strength >= 70 and standing_position > total_teams // 2:
        pressure += 15

    # 4. Redução por resistência à pressão do técnico (até 15 pontos)
    resistance_discount = int((coach_pressure_resistance / 100.0) * 15.0)
    pressure -= resistance_discount

    return max(0, min(100, pressure))


def should_sack_coach(pressure: int, rng: Random | None = None) -> bool:
    """Verifica se a CPU decide demitir o técnico com base no nível de pressão."""

    if pressure < 60:
        return False

    random_gen = rng if rng is not None else Random(42)
    roll = random_gen.random()

    if pressure >= 80:
        return roll < 0.75  # 75% de chance no risco crítico
    else:  # 60 a 79
        return roll < 0.25  # 25% de chance na pressão moderada/alta


def create_coach_bounce_effect(coach: Coach, rng: Random | None = None) -> CoachBounceEffect:
    """Gera o efeito temporário de 'chicotada psicológica' para uma nova contratação."""

    random_gen = rng if rng is not None else Random(stable_int_seed(coach.name, namespace="coach"))
    rounds = random_gen.randint(3, 5)

    # Moral bonus entre 3 e 8 pontos
    morale_bonus = round(3.0 + (coach.morale_management / 100.0) * 5.0, 1)
    # Rating bonus entre 1% (0.01) e 4% (0.04)
    rating_bonus = round(0.01 + (coach.tactical_skill / 100.0) * 0.03, 3)

    return CoachBounceEffect(
        rounds_remaining=rounds,
        morale_bonus=morale_bonus,
        rating_bonus=rating_bonus,
        source_coach_name=coach.name,
    )


def select_best_coach_for_team(
    team_name: str,
    available_coaches: list[Coach],
    league_tier_name: str = "SERIE_D",
) -> Coach | None:
    """Seleciona o melhor técnico livre compatível com o clube e sua divisão."""

    free_coaches = [c for c in available_coaches if c.status == CoachStatus.FREE_AGENT]
    if not free_coaches:
        return None

    # Ordena por reputação e habilidade tática
    sorted_coaches = sorted(
        free_coaches,
        key=lambda c: (c.reputation, c.tactical_skill),
        reverse=True,
    )

    # Séries A/B buscam maiores reputações; Séries C/D aceitam técnicos emergentes
    return sorted_coaches[0]
