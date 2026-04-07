"""Customer data model for the CRM."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Customer:
    """Represents a customer in the CRM.

    Attributes:
        name: Full name of the customer.
        email: Unique e-mail address.
        phone: Optional phone number.
        company: Optional company/organisation name.
        notes: Free-text notes about the customer.
        id: Auto-generated UUID (assigned on creation).
    """

    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    notes: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Customer name must not be empty.")
        if not self.email or "@" not in self.email:
            raise ValueError(f"Invalid e-mail address: {self.email!r}")

    def update(
        self,
        *,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> None:
        """Update one or more fields in place."""
        if name is not None:
            if not name.strip():
                raise ValueError("Customer name must not be empty.")
            self.name = name
        if email is not None:
            if "@" not in email:
                raise ValueError(f"Invalid e-mail address: {email!r}")
            self.email = email
        if phone is not None:
            self.phone = phone
        if company is not None:
            self.company = company
        if notes is not None:
            self.notes = notes

    def __repr__(self) -> str:  # pragma: no cover
        return f"Customer(id={self.id!r}, name={self.name!r}, email={self.email!r})"
