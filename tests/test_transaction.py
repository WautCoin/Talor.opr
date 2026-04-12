"""Tests for rto.Transaction."""

from decimal import Decimal

import pytest

from rto import Transaction


def test_transaction_basic():
    tx = Transaction("alice", "bob", Decimal("10"))
    assert tx.sender == "alice"
    assert tx.recipient == "bob"
    assert tx.amount == Decimal("10")
    assert tx.tx_id  # auto-generated


def test_transaction_string_amount_coerced():
    tx = Transaction("alice", "bob", "25.5")
    assert tx.amount == Decimal("25.5")


def test_transaction_rejects_empty_sender():
    with pytest.raises(ValueError, match="sender"):
        Transaction("", "bob", Decimal("1"))


def test_transaction_rejects_empty_recipient():
    with pytest.raises(ValueError, match="recipient"):
        Transaction("alice", "", Decimal("1"))


def test_transaction_rejects_zero_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        Transaction("alice", "bob", Decimal("0"))


def test_transaction_rejects_negative_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        Transaction("alice", "bob", Decimal("-5"))


def test_transaction_unique_ids():
    tx1 = Transaction("alice", "bob", Decimal("1"))
    tx2 = Transaction("alice", "bob", Decimal("1"))
    assert tx1.tx_id != tx2.tx_id
