"""Tests for batchcoin.Batch."""

import pytest
from decimal import Decimal

from batchcoin import Batch, Ledger, Transaction
from batchcoin.batch import BatchError


def _make_ledger(**balances):
    return Ledger({k: Decimal(str(v)) for k, v in balances.items()})


# ---------------------------------------------------------------------------
# Best-effort mode (default)
# ---------------------------------------------------------------------------


def test_batch_applies_transactions():
    ledger = _make_ledger(alice=100, bob=0)
    batch = Batch()
    batch.add(Transaction("alice", "bob", Decimal("30")))
    batch.add(Transaction("alice", "bob", Decimal("20")))
    result = batch.process(ledger)
    assert result.success_count == 2
    assert result.failure_count == 0
    assert ledger.balance("alice") == Decimal("50")
    assert ledger.balance("bob") == Decimal("50")


def test_batch_skips_failed_transactions():
    ledger = _make_ledger(alice=10, bob=0)
    batch = Batch()
    batch.add(Transaction("alice", "bob", Decimal("5")))   # ok
    batch.add(Transaction("alice", "bob", Decimal("50")))  # insufficient
    result = batch.process(ledger)
    assert result.success_count == 1
    assert result.failure_count == 1
    assert ledger.balance("alice") == Decimal("5")
    assert ledger.balance("bob") == Decimal("5")


def test_batch_clears_after_process():
    ledger = _make_ledger(alice=100)
    batch = Batch()
    batch.add(Transaction("alice", "bob", Decimal("10")))
    batch.process(ledger)
    assert batch.size == 0


def test_batch_chaining():
    ledger = _make_ledger(alice=100, bob=0, carol=0)
    result = (
        Batch()
        .add(Transaction("alice", "bob", Decimal("40")))
        .add(Transaction("alice", "carol", Decimal("40")))
        .process(ledger)
    )
    assert result.success_count == 2
    assert ledger.balance("bob") == Decimal("40")
    assert ledger.balance("carol") == Decimal("40")


def test_empty_batch():
    ledger = _make_ledger(alice=100)
    result = Batch().process(ledger)
    assert result.success_count == 0
    assert result.failure_count == 0


def test_batch_clear():
    batch = Batch()
    batch.add(Transaction("a", "b", Decimal("1")))
    batch.add(Transaction("a", "b", Decimal("2")))
    assert batch.size == 2
    batch.clear()
    assert batch.size == 0


# ---------------------------------------------------------------------------
# Atomic mode
# ---------------------------------------------------------------------------


def test_atomic_batch_succeeds():
    ledger = _make_ledger(alice=100, bob=0)
    batch = Batch()
    batch.add(Transaction("alice", "bob", Decimal("30")))
    batch.add(Transaction("alice", "bob", Decimal("20")))
    result = batch.process(ledger, atomic=True)
    assert result.success_count == 2
    assert ledger.balance("alice") == Decimal("50")


def test_atomic_batch_rolls_back_on_failure():
    ledger = _make_ledger(alice=10, bob=0)
    batch = Batch()
    batch.add(Transaction("alice", "bob", Decimal("5")))    # ok on its own
    batch.add(Transaction("alice", "bob", Decimal("50")))   # will fail
    with pytest.raises(BatchError) as exc_info:
        batch.process(ledger, atomic=True)
    assert len(exc_info.value.failed) == 1
    # Ledger must be unchanged
    assert ledger.balance("alice") == Decimal("10")
    assert ledger.balance("bob") == Decimal("0")


def test_batch_result_repr():
    ledger = _make_ledger(alice=100)
    result = Batch().process(ledger)
    assert "BatchResult" in repr(result)
