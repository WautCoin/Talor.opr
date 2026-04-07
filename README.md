# Batchcoin

Batch coin transaction processor for the WautCoin ecosystem.

## Features

- **Batch processing** – queue multiple transfers and apply them in one shot
- **Best-effort mode** – valid transactions go through, invalid ones are collected and reported
- **Atomic mode** – the whole batch is rolled back if any transaction fails
- **In-memory ledger** – tracks balances for any set of addresses
- **CSV CLI** – process transactions from a CSV file

## Installation

```bash
pip install -e .
```

## Quick start

```python
from decimal import Decimal
from batchcoin import Batch, Ledger, Transaction

ledger = Ledger({"alice": Decimal("200"), "bob": Decimal("0")})

batch = Batch()
batch.add(Transaction("alice", "bob", Decimal("50")))
batch.add(Transaction("alice", "bob", Decimal("30")))

result = batch.process(ledger)
print(result.success_count)        # 2
print(ledger.balance("bob"))       # 80
```

## CLI

```
# transactions.csv
# sender,recipient,amount
# alice,bob,10
# alice,carol,20

batchcoin transactions.csv --balances balances.csv
batchcoin transactions.csv --balances balances.csv --atomic
```

## Running tests

```bash
pip install pytest
pytest
```
