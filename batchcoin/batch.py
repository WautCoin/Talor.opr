"""Batch processing engine for Batchcoin."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Tuple

from .ledger import Ledger
from .transaction import Transaction


class BatchResult:
    """Result produced by :meth:`Batch.process`.

    Attributes:
        applied: Transactions that were successfully applied.
        failed: Pairs of (transaction, error message) that were rejected.
    """

    def __init__(
        self,
        applied: List[Transaction],
        failed: List[Tuple[Transaction, str]],
    ) -> None:
        self.applied = applied
        self.failed = failed

    @property
    def success_count(self) -> int:
        return len(self.applied)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"BatchResult(applied={self.success_count}, "
            f"failed={self.failure_count})"
        )


class Batch:
    """Collects transactions and applies them to a :class:`Ledger` in best-effort or atomic mode.

    Usage::

        from decimal import Decimal
        from batchcoin import Batch, Ledger, Transaction

        ledger = Ledger({"alice": Decimal("200"), "bob": Decimal("0")})
        batch = Batch()
        batch.add(Transaction("alice", "bob", Decimal("50")))
        batch.add(Transaction("alice", "bob", Decimal("30")))
        result = batch.process(ledger)
        print(result)          # BatchResult(applied=2, failed=0)
        print(ledger.balance("bob"))  # 80
    """

    def __init__(self) -> None:
        self._pending: List[Transaction] = []

    # ------------------------------------------------------------------
    # Building the batch
    # ------------------------------------------------------------------

    def add(self, tx: Transaction) -> "Batch":
        """Append a transaction to the batch and return *self* for chaining."""
        self._pending.append(tx)
        return self

    def clear(self) -> None:
        """Remove all pending transactions without processing them."""
        self._pending.clear()

    @property
    def pending(self) -> List[Transaction]:
        """Read-only view of queued transactions."""
        return list(self._pending)

    @property
    def size(self) -> int:
        """Number of transactions currently queued."""
        return len(self._pending)

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def process(self, ledger: Ledger, *, atomic: bool = False) -> BatchResult:
        """Apply all pending transactions to *ledger*.

        Args:
            ledger: The :class:`Ledger` to update.
            atomic: When ``True`` the entire batch is rolled back if *any*
                transaction fails.  When ``False`` (default) valid
                transactions are applied individually and invalid ones are
                collected in :attr:`BatchResult.failed`.

        Returns:
            A :class:`BatchResult` summarising what happened.

        Raises:
            BatchError: If *atomic* is ``True`` and at least one transaction
                fails (ledger is left unchanged).
        """
        if atomic:
            return self._process_atomic(ledger)
        return self._process_best_effort(ledger)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_best_effort(self, ledger: Ledger) -> BatchResult:
        applied: List[Transaction] = []
        failed: List[Tuple[Transaction, str]] = []

        for tx in self._pending:
            try:
                ledger.debit(tx.sender, tx.amount)
                ledger.credit(tx.recipient, tx.amount)
                applied.append(tx)
            except (ValueError, KeyError) as exc:
                failed.append((tx, str(exc)))

        self._pending.clear()
        return BatchResult(applied=applied, failed=failed)

    def _process_atomic(self, ledger: Ledger) -> BatchResult:
        # Validate all transactions against a scratch copy of the balances.
        scratch = Ledger(ledger.all_balances())
        applied: List[Transaction] = []
        failed: List[Tuple[Transaction, str]] = []

        for tx in self._pending:
            try:
                scratch.debit(tx.sender, tx.amount)
                scratch.credit(tx.recipient, tx.amount)
                applied.append(tx)
            except (ValueError, KeyError) as exc:
                failed.append((tx, str(exc)))

        if failed:
            raise BatchError(
                f"{len(failed)} transaction(s) failed; batch rolled back",
                failed=failed,
            )

        # All good — replay against the real ledger.
        for tx in applied:
            ledger.debit(tx.sender, tx.amount)
            ledger.credit(tx.recipient, tx.amount)

        self._pending.clear()
        return BatchResult(applied=applied, failed=[])


class BatchError(Exception):
    """Raised when an atomic batch cannot be fully applied.

    Attributes:
        failed: List of ``(Transaction, error_message)`` pairs.
    """

    def __init__(
        self,
        message: str,
        failed: List[Tuple[Transaction, str]],
    ) -> None:
        super().__init__(message)
        self.failed = failed
