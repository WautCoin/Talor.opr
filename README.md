# RTO — Real-Time Operations

Real-time coin transaction processor for the WautCoin ecosystem.

## Features

- **Real-time processing** – each transaction is applied immediately on submission
- **Callbacks** – optional `on_success` / `on_failure` hooks for instant reactions
- **History** – full audit trail of all processed transactions
- **CLI** – CSV-driven command-line interface; also reads from stdin

## Quick start

```python
from decimal import Decimal
from rto import Ledger, RealTimeProcessor, Transaction

ledger = Ledger({"alice": Decimal("200"), "bob": Decimal("0")})
processor = RealTimeProcessor(ledger)

result = processor.submit(Transaction("alice", "bob", Decimal("50")))
print(result.success)           # True
print(ledger.balance("bob"))    # 50
```

### With callbacks

```python
processor = RealTimeProcessor(
    ledger,
    on_success=lambda tx: print(f"✓ {tx.tx_id[:8]}"),
    on_failure=lambda tx, err: print(f"✗ {err}"),
)
```

## CLI usage

```
rto transactions.csv [--balances balances.csv]
```

`transactions.csv` columns: `sender,recipient,amount`

`balances.csv` columns: `address,balance`

Use `-` as the file argument to read transactions from stdin.

## Development

```
pip install -e .
pytest
```
