"""CLI entry point: ``python -m rto``."""

from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation

from . import Ledger, RealTimeProcessor, Transaction, __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rto",
        description="Process coin transactions in real time from a CSV file.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "transactions",
        metavar="FILE",
        help=(
            "CSV file with columns: sender,recipient,amount. "
            "Use '-' to read from stdin."
        ),
    )
    parser.add_argument(
        "--balances",
        metavar="FILE",
        help=(
            "Optional CSV file with initial balances (columns: address,balance). "
            "Addresses not listed start with 0."
        ),
    )
    return parser


def _load_balances(path: str) -> dict[str, Decimal]:
    balances: dict[str, Decimal] = {}
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                balances[row["address"]] = Decimal(row["balance"])
            except (KeyError, InvalidOperation) as exc:
                print(f"[warn] skipping bad balance row {row}: {exc}", file=sys.stderr)
    return balances


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    balances = _load_balances(args.balances) if args.balances else {}
    ledger = Ledger(balances)

    def on_success(tx: Transaction) -> None:
        print(f"  [ok]   [{tx.tx_id[:8]}] {tx.sender} -> {tx.recipient} ({tx.amount})")

    def on_failure(tx: Transaction, reason: str) -> None:
        print(
            f"  [fail] [{tx.tx_id[:8]}] {tx.sender} -> {tx.recipient} "
            f"({tx.amount}): {reason}",
            file=sys.stderr,
        )

    processor = RealTimeProcessor(ledger, on_success=on_success, on_failure=on_failure)

    source = sys.stdin if args.transactions == "-" else open(args.transactions, newline="")
    try:
        reader = csv.DictReader(source)
        for i, row in enumerate(reader, start=2):  # row 1 = header
            try:
                tx = Transaction(
                    sender=row["sender"],
                    recipient=row["recipient"],
                    amount=Decimal(row["amount"]),
                )
            except (KeyError, ValueError, InvalidOperation) as exc:
                print(f"[warn] skipping row {i}: {exc}", file=sys.stderr)
                continue
            processor.submit(tx)
    finally:
        if args.transactions != "-":
            source.close()

    print(f"\nApplied : {processor.success_count}")
    print(f"Failed  : {processor.failure_count}")

    print("\nFinal balances:")
    for address, balance in sorted(ledger.all_balances().items()):
        print(f"  {address}: {balance}")

    return 0 if processor.failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
