"""Transaction model for Batchcoin."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Transaction:
    """A single coin transfer between two addresses.

    Attributes:
        sender: Address sending coins.
        recipient: Address receiving coins.
        amount: Non-negative amount of coins to transfer.
        tx_id: Unique transaction identifier (auto-generated).
    """

    sender: str
    recipient: str
    amount: Decimal
    tx_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.sender:
            raise ValueError("sender must not be empty")
        if not self.recipient:
            raise ValueError("recipient must not be empty")
        self.amount = Decimal(str(self.amount))
        if self.amount <= 0:
            raise ValueError(f"amount must be positive, got {self.amount}")
