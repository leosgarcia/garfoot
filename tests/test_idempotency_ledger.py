"""Testes unitários para o ledger de idempotência (IdempotencyLedger)."""

from __future__ import annotations

from garfoot.domain.idempotency import IdempotencyLedger, make_idempotency_key


def test_empty_ledger_does_not_contain_keys():
    ledger = IdempotencyLedger()
    assert not ledger.has("some:key")


def test_mark_registers_key():
    ledger = IdempotencyLedger()
    ledger.mark("some:key")
    assert ledger.has("some:key")


def test_check_and_mark_returns_true_first_time_and_false_second_time():
    ledger = IdempotencyLedger()
    key = make_idempotency_key("sponsorship", "round-income", 2026, 1, "Fortaleza")
    
    assert ledger.check_and_mark(key) is True
    assert ledger.has(key) is True
    assert ledger.check_and_mark(key) is False


def test_serialization_preserves_keys():
    ledger = IdempotencyLedger()
    ledger.mark("key:1")
    ledger.mark("key:2")

    data = ledger.to_dict()
    assert data["processed_keys"] == ["key:1", "key:2"]

    reconstructed = IdempotencyLedger.from_dict(data)
    assert reconstructed.has("key:1")
    assert reconstructed.has("key:2")


def test_from_dict_none_returns_empty_ledger():
    ledger = IdempotencyLedger.from_dict(None)
    assert isinstance(ledger, IdempotencyLedger)
    assert len(ledger.processed_keys) == 0
