"""Testes unitários para a geração de seeds determinísticas em garfoot.domain.stable_random."""

from __future__ import annotations

import subprocess
import sys
from garfoot.domain.stable_random import (
    combine_seed,
    stable_composite_seed,
    stable_int_seed,
)


def test_stable_int_seed_is_deterministic():
    val1 = stable_int_seed("Fortaleza")
    val2 = stable_int_seed("Fortaleza")
    assert val1 == val2
    assert 0 <= val1 < 2**32


def test_namespaces_produce_different_values():
    val_default = stable_int_seed("Fortaleza", namespace="garfoot")
    val_custom = stable_int_seed("Fortaleza", namespace="other-namespace")
    assert val_default != val_custom


def test_stable_composite_seed_is_deterministic():
    val1 = stable_composite_seed(("A", "B", 1))
    val2 = stable_composite_seed(("A", "B", 1))
    assert val1 == val2
    assert 0 <= val1 < 2**32


def test_combine_seed_is_deterministic():
    val1 = combine_seed(42, "Série D")
    val2 = combine_seed(42, "Série D")
    assert val1 == val2
    assert combine_seed(None, "Série D") != val1
    assert 0 <= val1 < 2**32


def test_stable_seed_is_equal_across_processes():
    code = (
        "from garfoot.domain.stable_random import stable_int_seed; "
        "print(stable_int_seed('Fortaleza', namespace='test'))"
    )
    res1 = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    res2 = subprocess.check_output([sys.executable, "-c", code], text=True).strip()
    assert res1 == res2
    assert res1.isdigit()
