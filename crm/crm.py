"""Core CRM registry — manages customers and their interactions."""

from __future__ import annotations

from typing import Dict, List, Optional

from .customer import Customer
from .interaction import Interaction, InteractionType


class CRMError(Exception):
    """Raised when a CRM operation cannot be completed."""


class CRM:
    """In-memory Customer Relationship Management store.

    All data lives in plain Python dicts keyed by UUID strings so the store is
    trivially serialisable (e.g. with ``json.dumps``).

    Example::

        crm = CRM()
        cid = crm.add_customer("Alice", "alice@example.com")
        crm.add_interaction(cid, InteractionType.CALL, "Initial discovery call")
        for ix in crm.get_interactions(cid):
            print(ix.summary)
    """

    def __init__(self) -> None:
        self._customers: Dict[str, Customer] = {}
        self._interactions: Dict[str, Interaction] = {}

    # ------------------------------------------------------------------
    # Customer operations
    # ------------------------------------------------------------------

    def add_customer(
        self,
        name: str,
        email: str,
        *,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        notes: str = "",
    ) -> str:
        """Create a new customer and return its ID.

        Raises:
            CRMError: if a customer with the same e-mail already exists.
        """
        self._assert_email_unique(email)
        customer = Customer(
            name=name,
            email=email,
            phone=phone,
            company=company,
            notes=notes,
        )
        self._customers[customer.id] = customer
        return customer.id

    def get_customer(self, customer_id: str) -> Customer:
        """Return a customer by ID.

        Raises:
            CRMError: if the customer does not exist.
        """
        return self._require_customer(customer_id)

    def update_customer(self, customer_id: str, **kwargs: object) -> None:
        """Update fields on an existing customer.

        Keyword arguments are forwarded to :meth:`Customer.update`.

        Raises:
            CRMError: if the customer does not exist or the new e-mail is
                already taken by another customer.
        """
        customer = self._require_customer(customer_id)
        new_email = kwargs.get("email")
        if new_email and new_email != customer.email:
            self._assert_email_unique(str(new_email))
        customer.update(**kwargs)  # type: ignore[arg-type]

    def delete_customer(self, customer_id: str) -> None:
        """Remove a customer and all their interactions.

        Raises:
            CRMError: if the customer does not exist.
        """
        self._require_customer(customer_id)
        del self._customers[customer_id]
        # Cascade-delete interactions
        to_remove = [
            iid
            for iid, ix in self._interactions.items()
            if ix.customer_id == customer_id
        ]
        for iid in to_remove:
            del self._interactions[iid]

    def list_customers(self, *, company: Optional[str] = None) -> List[Customer]:
        """Return all customers, optionally filtered by company name."""
        customers = list(self._customers.values())
        if company is not None:
            customers = [c for c in customers if c.company == company]
        return customers

    def find_customer_by_email(self, email: str) -> Optional[Customer]:
        """Return the customer with *email*, or ``None`` if not found."""
        for customer in self._customers.values():
            if customer.email == email:
                return customer
        return None

    # ------------------------------------------------------------------
    # Interaction operations
    # ------------------------------------------------------------------

    def add_interaction(
        self,
        customer_id: str,
        kind: InteractionType,
        summary: str,
        *,
        details: str = "",
    ) -> str:
        """Record a new interaction for a customer and return its ID.

        Raises:
            CRMError: if the customer does not exist.
        """
        self._require_customer(customer_id)
        interaction = Interaction(
            customer_id=customer_id,
            kind=kind,
            summary=summary,
            details=details,
        )
        self._interactions[interaction.id] = interaction
        return interaction.id

    def get_interactions(
        self,
        customer_id: str,
        *,
        kind: Optional[InteractionType] = None,
    ) -> List[Interaction]:
        """Return interactions for a customer, newest first.

        Optionally filter by *kind*.

        Raises:
            CRMError: if the customer does not exist.
        """
        self._require_customer(customer_id)
        results = [
            ix
            for ix in self._interactions.values()
            if ix.customer_id == customer_id
        ]
        if kind is not None:
            results = [ix for ix in results if ix.kind == kind]
        results.sort(key=lambda ix: ix.occurred_at, reverse=True)
        return results

    def delete_interaction(self, interaction_id: str) -> None:
        """Remove an interaction by ID.

        Raises:
            CRMError: if the interaction does not exist.
        """
        if interaction_id not in self._interactions:
            raise CRMError(f"Interaction {interaction_id!r} not found.")
        del self._interactions[interaction_id]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_customer(self, customer_id: str) -> Customer:
        customer = self._customers.get(customer_id)
        if customer is None:
            raise CRMError(f"Customer {customer_id!r} not found.")
        return customer

    def _assert_email_unique(self, email: str) -> None:
        if self.find_customer_by_email(email) is not None:
            raise CRMError(f"A customer with e-mail {email!r} already exists.")
