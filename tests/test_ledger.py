"""Tests for batchcoin.Ledger."""

import pytest
from decimal import Decimal

from batchcoin import Ledger


def test_initial_balances():
    ledger = Ledger({"alice": Decimal("100"), "bob": Decimal("50")})
    assert ledger.balance("alice") == Decimal("100")
    assert ledger.balance("bob") == Decimal("50")


def test_unknown_address_returns_zero():
    ledger = Ledger()
    assert ledger.balance("unknown") == Decimal("0")


def test_credit():
    ledger = Ledger({"alice": Decimal("10")})
    ledger.credit("alice", Decimal("5"))
    assert ledger.balance("alice") == Decimal("15")


def test_credit_new_address():
    ledger = Ledger()
    ledger.credit("carol", Decimal("20"))
    assert ledger.balance("carol") == Decimal("20")


def test_debit():
    ledger = Ledger({"alice": Decimal("10")})
    ledger.debit("alice", Decimal("3"))
    assert ledger.balance("alice") == Decimal("7")


def test_debit_exact_balance():
    ledger = Ledger({"alice": Decimal("10")})
    ledger.debit("alice", Decimal("10"))
    assert ledger.balance("alice") == Decimal("0")


def test_debit_insufficient_funds_raises():
    ledger = Ledger({"alice": Decimal("5")})
    with pytest.raises(ValueError, match="insufficient funds"):
        ledger.debit("alice", Decimal("10"))


def test_all_balances_snapshot():
    ledger = Ledger({"alice": Decimal("1"), "bob": Decimal("2")})
    snap = ledger.all_balances()
    # Mutating the snapshot doesn't affect the ledger
    snap["alice"] = Decimal("999")
    assert ledger.balance("alice") == Decimal("1")
