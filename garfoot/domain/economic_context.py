"""Modelo e regras puras do contexto econômico e inflação global da temporada."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

DEFAULT_INFLATION_RATE: float = 0.05
MIN_INFLATION_RATE: float = 0.0
MAX_NORMAL_INFLATION_RATE: float = 0.08


def apply_economic_index(base_value: int, economic_index: float) -> int:
    """Aplica o índice econômico sobre um valor base de forma previsível."""

    if base_value <= 0:
        return base_value
    if economic_index <= 0:
        raise ValueError("O índice econômico deve ser positivo.")
    return round(base_value * economic_index)


@dataclass(frozen=True, slots=True)
class EconomicContext:
    """Representa o contexto econômico global de uma temporada no Garfoot."""

    season_year: int = 2026
    economic_index: float = 1.0
    inflation_rate: float = DEFAULT_INFLATION_RATE

    def __post_init__(self) -> None:
        if self.season_year < 1900:
            raise ValueError("Ano da temporada inválido.")
        if self.economic_index <= 0:
            raise ValueError("O índice econômico deve ser positivo.")
        if self.inflation_rate < MIN_INFLATION_RATE or self.inflation_rate > MAX_NORMAL_INFLATION_RATE:
            raise ValueError(
                f"A taxa de inflação deve ficar entre {MIN_INFLATION_RATE} e {MAX_NORMAL_INFLATION_RATE}."
            )

    def adjusted_value(self, base_value: int) -> int:
        """Retorna o valor ajustado pela inflação acumulada até a temporada atual."""

        return apply_economic_index(base_value, self.economic_index)

    def advance_season(self) -> EconomicContext:
        """Avança uma temporada, incrementando o ano e acumulando a taxa de inflação no índice econômico."""

        next_index = round(self.economic_index * (1.0 + self.inflation_rate), 4)
        return EconomicContext(
            season_year=self.season_year + 1,
            economic_index=next_index,
            inflation_rate=self.inflation_rate,
        )

    def advance_season_idempotent(self, ledger: Any) -> EconomicContext:
        """Avança o contexto econômico de forma estritamente idempotente via ledger."""

        key = f"economic-context:advance:{self.season_year}"
        if ledger is not None and hasattr(ledger, "check_and_mark"):
            if not ledger.check_and_mark(key):
                return self

        return self.advance_season()

    def to_dict(self) -> dict[str, Any]:
        return {
            "season_year": self.season_year,
            "economic_index": self.economic_index,
            "inflation_rate": self.inflation_rate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EconomicContext:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            season_year=int(data.get("season_year", 2026)),
            economic_index=float(data.get("economic_index", 1.0)),
            inflation_rate=float(data.get("inflation_rate", DEFAULT_INFLATION_RATE)),
        )
