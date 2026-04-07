"""Command-line interface for the CRM.

Usage examples
--------------
List customers from a JSON file::

    python -m crm list --db customers.json

Add a customer interactively::

    python -m crm add --name "Alice" --email alice@example.com --company Acme

Log an interaction::

    python -m crm interact --id <customer-id> --kind call --summary "Discovery call"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

from .crm import CRM, CRMError
from .interaction import InteractionType

_DEFAULT_DB = os.environ.get("CRM_DB", "crm_data.json")


# ---------------------------------------------------------------------------
# Persistence helpers (simple JSON file)
# ---------------------------------------------------------------------------

def _load(path: str) -> CRM:
    crm = CRM()
    if not os.path.exists(path):
        return crm
    with open(path, encoding="utf-8") as fh:
        data: Dict[str, Any] = json.load(fh)
    for c in data.get("customers", []):
        cid = crm.add_customer(
            c["name"],
            c["email"],
            phone=c.get("phone"),
            company=c.get("company"),
            notes=c.get("notes", ""),
        )
        # Restore original ID
        crm._customers[cid].id = c["id"]  # noqa: SLF001
        crm._customers[c["id"]] = crm._customers.pop(cid)
    for ix in data.get("interactions", []):
        from .interaction import Interaction, InteractionType  # local import
        from datetime import datetime, timezone
        interaction = Interaction(
            customer_id=ix["customer_id"],
            kind=InteractionType(ix["kind"]),
            summary=ix["summary"],
            details=ix.get("details", ""),
            occurred_at=datetime.fromisoformat(ix["occurred_at"]),
            id=ix["id"],
        )
        crm._interactions[interaction.id] = interaction  # noqa: SLF001
    return crm


def _save(crm: CRM, path: str) -> None:
    data: Dict[str, Any] = {
        "customers": [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "company": c.company,
                "notes": c.notes,
            }
            for c in crm.list_customers()
        ],
        "interactions": [
            {
                "id": ix.id,
                "customer_id": ix.customer_id,
                "kind": ix.kind.value,
                "summary": ix.summary,
                "details": ix.details,
                "occurred_at": ix.occurred_at.isoformat(),
            }
            for ix in crm._interactions.values()  # noqa: SLF001
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_add(args: argparse.Namespace, crm: CRM) -> None:
    cid = crm.add_customer(
        args.name,
        args.email,
        phone=args.phone,
        company=args.company,
        notes=args.notes or "",
    )
    print(f"Added customer: {cid}")


def cmd_list(args: argparse.Namespace, crm: CRM) -> None:
    customers = crm.list_customers(company=args.company)
    if not customers:
        print("No customers found.")
        return
    for c in customers:
        parts = [f"[{c.id}] {c.name} <{c.email}>"]
        if c.company:
            parts.append(f"({c.company})")
        print(" ".join(parts))


def cmd_interact(args: argparse.Namespace, crm: CRM) -> None:
    iid = crm.add_interaction(
        args.id,
        InteractionType(args.kind),
        args.summary,
        details=args.details or "",
    )
    print(f"Logged interaction: {iid}")


def cmd_history(args: argparse.Namespace, crm: CRM) -> None:
    kind = InteractionType(args.kind) if args.kind else None
    interactions = crm.get_interactions(args.id, kind=kind)
    if not interactions:
        print("No interactions found.")
        return
    for ix in interactions:
        print(f"[{ix.occurred_at:%Y-%m-%d %H:%M}] {ix.kind.value}: {ix.summary}")


def cmd_delete(args: argparse.Namespace, crm: CRM) -> None:
    crm.delete_customer(args.id)
    print(f"Deleted customer: {args.id}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crm",
        description="WautCoin CRM — manage customers and interactions.",
    )
    parser.add_argument(
        "--db",
        default=_DEFAULT_DB,
        metavar="PATH",
        help="Path to the JSON database file (default: crm_data.json or $CRM_DB).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Add a new customer.")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--email", required=True)
    p_add.add_argument("--phone")
    p_add.add_argument("--company")
    p_add.add_argument("--notes")

    # list
    p_list = sub.add_parser("list", help="List customers.")
    p_list.add_argument("--company", help="Filter by company name.")

    # interact
    p_interact = sub.add_parser("interact", help="Log an interaction.")
    p_interact.add_argument("--id", required=True, metavar="CUSTOMER_ID")
    p_interact.add_argument(
        "--kind",
        required=True,
        choices=[t.value for t in InteractionType],
    )
    p_interact.add_argument("--summary", required=True)
    p_interact.add_argument("--details", default="")

    # history
    p_history = sub.add_parser("history", help="Show interaction history.")
    p_history.add_argument("--id", required=True, metavar="CUSTOMER_ID")
    p_history.add_argument(
        "--kind",
        choices=[t.value for t in InteractionType],
        help="Filter by interaction type.",
    )

    # delete
    p_delete = sub.add_parser("delete", help="Delete a customer.")
    p_delete.add_argument("--id", required=True, metavar="CUSTOMER_ID")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    crm = _load(args.db)
    handlers = {
        "add": cmd_add,
        "list": cmd_list,
        "interact": cmd_interact,
        "history": cmd_history,
        "delete": cmd_delete,
    }
    try:
        handlers[args.command](args, crm)
        _save(crm, args.db)
    except CRMError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
