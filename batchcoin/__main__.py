"""CLI entry point: ``python -m batchcoin``."""

from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal, InvalidOperation

from . import Batch, Ledger, Transaction, __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="batchcoin",
        description="Process a batch of coin transactions from a CSV file.",
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
    parser.add_argument(
        "--atomic",
        action="store_true",
        help="Roll back the entire batch if any transaction fails.",
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


def _load_transactions(path: str) -> list[Transaction]:
    transactions: list[Transaction] = []
    source = sys.stdin if path == "-" else open(path, newline="")
    try:
        reader = csv.DictReader(source)
        for i, row in enumerate(reader, start=2):  # row 1 = header
            try:
                transactions.append(
                    Transaction(
                        sender=row["sender"],
                        recipient=row["recipient"],
                        amount=Decimal(row["amount"]),
                    )
                )
            except (KeyError, ValueError, InvalidOperation) as exc:
                print(f"[warn] skipping row {i}: {exc}", file=sys.stderr)
    finally:
        if path != "-":
            source.close()
    return transactions


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    balances = _load_balances(args.balances) if args.balances else {}
    ledger = Ledger(balances)
    transactions = _load_transactions(args.transactions)

    batch = Batch()
    for tx in transactions:
        batch.add(tx)

    print(f"Processing {batch.size} transaction(s) …")

    try:
        result = batch.process(ledger, atomic=args.atomic)
    except Exception as exc:  # BatchError when atomic=True
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(f"  Applied : {result.success_count}")
    print(f"  Failed  : {result.failure_count}")

    if result.failed:
        print("\nFailed transactions:")
        for tx, reason in result.failed:
            print(f"  [{tx.tx_id[:8]}] {tx.sender} -> {tx.recipient} "
                  f"({tx.amount}): {reason}")

    print("\nFinal balances:")
    for address, balance in sorted(ledger.all_balances().items()):
        print(f"  {address}: {balance}")

    return 0 if result.failure_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
