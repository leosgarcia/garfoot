"""Modelo de estadio e renda de bilheteria."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class Stadium:
    """Representa o estadio de um clube.

    A renda usa uma taxa de ocupacao estimada por moral do elenco e desempenho
    recente. A camada de temporada ainda nao existe, portanto ``performance``
    usa 0.5 como campanha neutra.
    """

    name: str
    city: str
    capacity: int
    average_ticket_price: int = 40

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.city = self.city.strip()
        if not self.name:
            raise ValueError("O estadio precisa ter nome.")
        if not self.city:
            raise ValueError("O estadio precisa ter cidade.")
        if self.capacity < 0:
            raise ValueError("A capacidade do estadio nao pode ser negativa.")
        if self.average_ticket_price < 0:
            raise ValueError("O preco medio do ingresso nao pode ser negativo.")

    def estimate_attendance_rate(
        self,
        morale: float,
        performance: float = 0.5,
    ) -> float:
        """Estima ocupacao do estadio entre 20% e 95%."""

        base_rate = 0.45
        morale_bonus = ((morale - 50) / 50) * 0.15
        performance_bonus = (performance - 0.5) * 0.30
        attendance_rate = base_rate + morale_bonus + performance_bonus
        return _clamp(attendance_rate, 0.20, 0.95)

    def estimate_attendance_rate_with_appeal(
        self,
        morale: float,
        performance: float = 0.5,
        appeal_context: Any | None = None,
    ) -> float:
        """Estima a ocupação do estádio considerando a atratividade e rivalidade do jogo."""

        base_rate = self.estimate_attendance_rate(morale, performance)
        if appeal_context is not None:
            from garfoot.domain.match_appeal import calculate_match_appeal_factor
            appeal_factor = calculate_match_appeal_factor(appeal_context)
            base_rate += appeal_factor

        return _clamp(base_rate, 0.20, 0.95)

    def estimate_match_income(
        self,
        morale: float,
        performance: float = 0.5,
        attendance_rate: float | None = None,
        appeal_context: Any | None = None,
    ) -> int:
        """Calcula renda aproximada de um jogo como mandante."""

        if attendance_rate is None:
            if appeal_context is not None:
                attendance_rate = self.estimate_attendance_rate_with_appeal(morale, performance, appeal_context)
            else:
                attendance_rate = self.estimate_attendance_rate(morale, performance)

        attendance_rate = _clamp(attendance_rate, 0.0, 1.0)
        return round(self.capacity * attendance_rate * self.average_ticket_price)

    def to_dict(self) -> dict[str, object]:
        """Representacao pronta para persistencia em JSON."""

        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Stadium":
        """Recria um estadio a partir de dados salvos."""

        return cls(**data)  # type: ignore[arg-type]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
