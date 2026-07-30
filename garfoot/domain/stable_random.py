"""Módulo puro para geração de seeds e números determinísticos baseados em hash estável (SHA-256).

Este módulo substitui o uso do `hash()` nativo do Python em sementes de simulação,
garantindo que execuções em diferentes processos ou instâncias do Python produzam
exatamente os mesmos valores determinísticos para uma mesma entrada.
"""

from __future__ import annotations

import hashlib
from typing import Iterable


def stable_int_seed(value: str, *, namespace: str = "garfoot", modulo: int = 2**32) -> int:
    """Gera uma seed inteira determinística a partir de uma string e um namespace."""
    raw = f"{namespace}:{value}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") % modulo


def stable_composite_seed(parts: Iterable[object], *, namespace: str = "garfoot", modulo: int = 2**32) -> int:
    """Gera uma seed inteira determinística a partir de múltiplos componentes."""
    value = "|".join(str(part) for part in parts)
    return stable_int_seed(value, namespace=namespace, modulo=modulo)


def combine_seed(base_seed: int | None, *parts: object, namespace: str = "garfoot", modulo: int = 2**32) -> int:
    """Combina uma base_seed opcional com partes adicionais de forma determinística."""
    base = "none" if base_seed is None else str(base_seed)
    return stable_composite_seed((base, *parts), namespace=namespace, modulo=modulo)
