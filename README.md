# Talor.opr — WautCoin CRM

A lightweight **Customer Relationship Management** library and CLI for the
WautCoin / Talor operator platform.

---

## Quick start

```bash
pip install -e .
```

### Add a customer

```bash
crm add --name "Alice Smith" --email alice@example.com --company "Acme Corp"
# Added customer: <uuid>
```

### List customers

```bash
crm list
crm list --company "Acme Corp"
```

### Log an interaction

```bash
crm interact --id <customer-id> --kind call --summary "Initial discovery call"
crm interact --id <customer-id> --kind email --summary "Sent proposal" --details "See attachment"
```

Interaction types: `call`, `email`, `meeting`, `note`, `other`.

### View interaction history

```bash
crm history --id <customer-id>
crm history --id <customer-id> --kind call
```

### Delete a customer

```bash
crm delete --id <customer-id>
```

Data is stored in `crm_data.json` (override with `--db path/to/file.json` or
the `CRM_DB` environment variable).

---

## Python API

```python
from crm import CRM, InteractionType

crm = CRM()
cid = crm.add_customer("Alice", "alice@example.com", company="Acme")
crm.add_interaction(cid, InteractionType.CALL, "Discovery call")

for ix in crm.get_interactions(cid):
    print(ix.occurred_at, ix.kind.value, ix.summary)
```

---

## Running tests

```bash
pip install pytest
pytest
```
