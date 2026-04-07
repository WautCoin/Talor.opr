"""In-memory ledger for Batchcoin."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict


class Ledger:
    """Tracks coin balances for a set of addresses.

    Example::

        ledger = Ledger({"alice": Decimal("100"), "bob": Decimal("50")})
        ledger.credit("alice", Decimal("10"))
        ledger.debit("alice", Decimal("10"))
    """

    def __init__(self, balances: Dict[str, Decimal] | None = None) -> None:
        self._balances: Dict[str, Decimal] = {}
        if balances:
            for address, amount in balances.items():
                self._balances[address] = Decimal(str(amount))

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def balance(self, address: str) -> Decimal:
        """Return the current balance for *address* (0 if unknown)."""
        return self._balances.get(address, Decimal("0"))

    def all_balances(self) -> Dict[str, Decimal]:
        """Return a snapshot of all balances."""
        return dict(self._balances)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def credit(self, address: str, amount: Decimal) -> None:
        """Add *amount* coins to *address*."""
        amount = Decimal(str(amount))
        self._balances[address] = self.balance(address) + amount

    def debit(self, address: str, amount: Decimal) -> None:
        """Subtract *amount* coins from *address*.

        Raises:
            ValueError: If *address* has insufficient funds.
        """
        amount = Decimal(str(amount))
        current = self.balance(address)
        if current < amount:
            raise ValueError(
                f"insufficient funds for {address!r}: "
                f"balance={current}, requested={amount}"
            )
        self._balances[address] = current - amount
