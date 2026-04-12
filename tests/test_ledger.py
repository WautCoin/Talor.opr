"""Tests for rto.Ledger."""

from decimal import Decimal

import pytest

from rto import Ledger


def test_ledger_initial_balances():
    ledger = Ledger({"alice": Decimal("100"), "bob": Decimal("50")})
    assert ledger.balance("alice") == Decimal("100")
    assert ledger.balance("bob") == Decimal("50")


def test_ledger_unknown_address_returns_zero():
    ledger = Ledger()
    assert ledger.balance("unknown") == Decimal("0")


def test_ledger_credit():
    ledger = Ledger({"alice": Decimal("100")})
    ledger.credit("alice", Decimal("25"))
    assert ledger.balance("alice") == Decimal("125")


def test_ledger_credit_new_address():
    ledger = Ledger()
    ledger.credit("carol", Decimal("10"))
    assert ledger.balance("carol") == Decimal("10")


def test_ledger_debit():
    ledger = Ledger({"alice": Decimal("100")})
    ledger.debit("alice", Decimal("40"))
    assert ledger.balance("alice") == Decimal("60")


def test_ledger_debit_exact_balance():
    ledger = Ledger({"alice": Decimal("100")})
    ledger.debit("alice", Decimal("100"))
    assert ledger.balance("alice") == Decimal("0")


def test_ledger_debit_insufficient_funds():
    ledger = Ledger({"alice": Decimal("10")})
    with pytest.raises(ValueError, match="insufficient funds"):
        ledger.debit("alice", Decimal("20"))


def test_ledger_debit_unknown_address_insufficient():
    ledger = Ledger()
    with pytest.raises(ValueError, match="insufficient funds"):
        ledger.debit("ghost", Decimal("1"))


def test_ledger_all_balances_snapshot():
    ledger = Ledger({"alice": Decimal("100"), "bob": Decimal("50")})
    snapshot = ledger.all_balances()
    ledger.credit("alice", Decimal("999"))
    assert snapshot["alice"] == Decimal("100")  # snapshot not affected
