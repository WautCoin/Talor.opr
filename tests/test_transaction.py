"""Tests for batchcoin.Transaction."""

import pytest
from decimal import Decimal

from batchcoin import Transaction


def test_basic_creation():
    tx = Transaction("alice", "bob", Decimal("10"))
    assert tx.sender == "alice"
    assert tx.recipient == "bob"
    assert tx.amount == Decimal("10")
    assert tx.tx_id  # auto-generated


def test_amount_coerced_to_decimal():
    tx = Transaction("alice", "bob", 5)
    assert isinstance(tx.amount, Decimal)
    assert tx.amount == Decimal("5")


def test_unique_tx_ids():
    tx1 = Transaction("a", "b", Decimal("1"))
    tx2 = Transaction("a", "b", Decimal("1"))
    assert tx1.tx_id != tx2.tx_id


def test_zero_amount_raises():
    with pytest.raises(ValueError, match="positive"):
        Transaction("a", "b", Decimal("0"))


def test_negative_amount_raises():
    with pytest.raises(ValueError, match="positive"):
        Transaction("a", "b", Decimal("-1"))


def test_empty_sender_raises():
    with pytest.raises(ValueError, match="sender"):
        Transaction("", "b", Decimal("1"))


def test_empty_recipient_raises():
    with pytest.raises(ValueError, match="recipient"):
        Transaction("a", "", Decimal("1"))
