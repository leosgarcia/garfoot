"""Modelo de contrato de jogador."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Contract:
    """Representa a situacao contractual de um jogador com o clube."""

    years_remaining: int = 2
    is_protected: bool = False
    protection_years: int = 0
    release_clause: int = 0

    def __post_init__(self) -> None:
        if self.years_remaining < 0:
            raise ValueError("Anos de contrato restantes nao podem ser negativos.")
        if self.protection_years < 0:
            raise ValueError("Anos de protecao de contrato nao podem ser negativos.")
        if self.release_clause < 0:
            raise ValueError("A cláusula de rescisão não pode ser negativa.")

    @property
    def can_be_transferred(self) -> bool:
        """Determina se o jogador pode ser negociado no mercado normalmente."""
        if self.years_remaining <= 0:
            return False  # Sem contrato vigente (livre no mercado)
        if self.is_protected or self.protection_years > 0:
            return False  # Bloqueado por cláusula contratual ou recém-contratado
        return True
