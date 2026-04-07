"""Real-time transaction processor for RTO."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, List, Optional, Tuple

from .ledger import Ledger
from .transaction import Transaction


@dataclass
class TransactionResult:
    """Outcome of a single real-time transaction.

    Attributes:
        transaction: The transaction that was processed.
        success: Whether the transaction was applied.
        error: Error message if the transaction failed, ``None`` otherwise.
    """

    transaction: Transaction
    success: bool
    error: Optional[str] = None


OnSuccessCallback = Callable[[Transaction], None]
OnFailureCallback = Callable[[Transaction, str], None]


class RealTimeProcessor:
    """Processes coin transactions immediately as they are submitted.

    Unlike batch processing, each transaction is applied to the ledger
    the moment :meth:`submit` is called.  Optional callbacks allow
    callers to react to successes and failures without polling.

    Usage::

        from decimal import Decimal
        from rto import Ledger, RealTimeProcessor, Transaction

        ledger = Ledger({"alice": Decimal("200"), "bob": Decimal("0")})
        processor = RealTimeProcessor(ledger)
        result = processor.submit(Transaction("alice", "bob", Decimal("50")))
        print(result.success)          # True
        print(ledger.balance("bob"))   # 50
    """

    def __init__(
        self,
        ledger: Ledger,
        *,
        on_success: Optional[OnSuccessCallback] = None,
        on_failure: Optional[OnFailureCallback] = None,
    ) -> None:
        self._ledger = ledger
        self._on_success = on_success
        self._on_failure = on_failure
        self._history: List[TransactionResult] = []

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------

    def submit(self, tx: Transaction) -> TransactionResult:
        """Apply *tx* to the ledger immediately.

        If the transaction succeeds the ``on_success`` callback is invoked;
        on failure the ``on_failure`` callback is invoked.  The result is
        also appended to :attr:`history` in both cases.

        Args:
            tx: The transaction to apply.

        Returns:
            A :class:`TransactionResult` describing the outcome.
        """
        try:
            self._ledger.debit(tx.sender, tx.amount)
            self._ledger.credit(tx.recipient, tx.amount)
        except (ValueError, KeyError) as exc:
            result = TransactionResult(transaction=tx, success=False, error=str(exc))
            self._history.append(result)
            if self._on_failure is not None:
                self._on_failure(tx, str(exc))
            return result

        result = TransactionResult(transaction=tx, success=True)
        self._history.append(result)
        if self._on_success is not None:
            self._on_success(tx)
        return result

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def history(self) -> List[TransactionResult]:
        """Ordered list of all results since the processor was created."""
        return list(self._history)

    @property
    def success_count(self) -> int:
        """Number of transactions successfully applied so far."""
        return sum(1 for r in self._history if r.success)

    @property
    def failure_count(self) -> int:
        """Number of transactions that failed so far."""
        return sum(1 for r in self._history if not r.success)

    @property
    def failed(self) -> List[Tuple[Transaction, str]]:
        """List of ``(transaction, error_message)`` pairs for failed transactions."""
        return [
            (r.transaction, r.error or "")
            for r in self._history
            if not r.success
        ]
