"""Tests for rto.RealTimeProcessor."""

from decimal import Decimal

import pytest

from rto import Ledger, RealTimeProcessor, Transaction


def _ledger() -> Ledger:
    return Ledger({"alice": Decimal("200"), "bob": Decimal("0"), "carol": Decimal("50")})


# ------------------------------------------------------------------
# Basic submit behaviour
# ------------------------------------------------------------------


def test_submit_success():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)
    tx = Transaction("alice", "bob", Decimal("50"))
    result = proc.submit(tx)

    assert result.success is True
    assert result.error is None
    assert result.transaction is tx
    assert ledger.balance("alice") == Decimal("150")
    assert ledger.balance("bob") == Decimal("50")


def test_submit_failure_insufficient_funds():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)
    tx = Transaction("bob", "alice", Decimal("1"))
    result = proc.submit(tx)

    assert result.success is False
    assert result.error is not None
    assert "insufficient" in result.error
    # Ledger must be unchanged
    assert ledger.balance("bob") == Decimal("0")
    assert ledger.balance("alice") == Decimal("200")


def test_submit_multiple_transactions():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)

    proc.submit(Transaction("alice", "bob", Decimal("30")))
    proc.submit(Transaction("alice", "carol", Decimal("20")))
    proc.submit(Transaction("carol", "bob", Decimal("200")))  # fails — carol only has 70

    assert proc.success_count == 2
    assert proc.failure_count == 1
    assert ledger.balance("alice") == Decimal("150")
    assert ledger.balance("carol") == Decimal("70")  # unchanged after fail
    assert ledger.balance("bob") == Decimal("30")


# ------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------


def test_on_success_callback_invoked():
    events: list = []
    ledger = _ledger()
    proc = RealTimeProcessor(ledger, on_success=lambda tx: events.append(("ok", tx)))

    tx = Transaction("alice", "bob", Decimal("10"))
    proc.submit(tx)

    assert len(events) == 1
    assert events[0] == ("ok", tx)


def test_on_failure_callback_invoked():
    events: list = []
    ledger = _ledger()
    proc = RealTimeProcessor(
        ledger, on_failure=lambda tx, err: events.append(("fail", tx, err))
    )

    tx = Transaction("bob", "alice", Decimal("1"))
    proc.submit(tx)

    assert len(events) == 1
    kind, recorded_tx, err = events[0]
    assert kind == "fail"
    assert recorded_tx is tx
    assert "insufficient" in err


def test_callbacks_not_required():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)
    # Should not raise even without callbacks
    proc.submit(Transaction("alice", "bob", Decimal("1")))
    proc.submit(Transaction("bob", "alice", Decimal("999")))  # will fail


# ------------------------------------------------------------------
# History and introspection
# ------------------------------------------------------------------


def test_history_records_all_results():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)

    proc.submit(Transaction("alice", "bob", Decimal("10")))
    proc.submit(Transaction("bob", "alice", Decimal("999")))  # fail

    assert len(proc.history) == 2
    assert proc.history[0].success is True
    assert proc.history[1].success is False


def test_history_returns_copy():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)
    proc.submit(Transaction("alice", "bob", Decimal("1")))
    snapshot = proc.history
    proc.submit(Transaction("alice", "bob", Decimal("1")))
    assert len(snapshot) == 1  # original snapshot unchanged


def test_failed_property():
    ledger = _ledger()
    proc = RealTimeProcessor(ledger)

    good_tx = Transaction("alice", "bob", Decimal("10"))
    bad_tx = Transaction("bob", "alice", Decimal("999"))
    proc.submit(good_tx)
    proc.submit(bad_tx)

    assert len(proc.failed) == 1
    tx, err = proc.failed[0]
    assert tx is bad_tx
    assert "insufficient" in err


def test_counters_start_at_zero():
    proc = RealTimeProcessor(_ledger())
    assert proc.success_count == 0
    assert proc.failure_count == 0
