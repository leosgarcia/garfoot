"""Módulo puro para controle de idempotência e prevenção de transações/eventos duplicados."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class IdempotencyLedger:
    """Ledger para armazenamento de chaves de operações financeiras e históricas já processadas."""

    processed_keys: set[str] = field(default_factory=set)

    def has(self, key: str) -> bool:
        """Verifica se a chave já foi processada."""
        return key in self.processed_keys

    def mark(self, key: str) -> None:
        """Marca a chave como processada."""
        self.processed_keys.add(key)

    def check_and_mark(self, key: str) -> bool:
        """Retorna True e marca se a chave ainda não existia. Retorna False se já foi processada."""
        if key in self.processed_keys:
            return False
        self.processed_keys.add(key)
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serializa o ledger para dicionário compatível com JSON."""
        return {"processed_keys": sorted(self.processed_keys)}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> IdempotencyLedger:
        """Desserializa o ledger a partir de um dicionário (com fallback seguro)."""
        if not data or not isinstance(data, dict):
            return cls()
        return cls(processed_keys=set(data.get("processed_keys", [])))


def make_idempotency_key(*parts: object) -> str:
    """Gera uma chave formatada e padronizada para o ledger."""
    return ":".join(str(part) for part in parts)
