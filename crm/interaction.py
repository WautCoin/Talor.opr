"""Interaction data model — records a single touchpoint with a customer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class InteractionType(str, Enum):
    """Category of a customer interaction."""

    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    NOTE = "note"
    OTHER = "other"


@dataclass
class Interaction:
    """A single interaction with a customer.

    Attributes:
        customer_id: ID of the customer this interaction belongs to.
        kind: Category of the interaction (call, email, meeting, etc.).
        summary: Short description / subject of the interaction.
        details: Optional longer body / notes.
        occurred_at: When the interaction took place (UTC).  Defaults to now.
        id: Auto-generated UUID.
    """

    customer_id: str
    kind: InteractionType
    summary: str
    details: str = ""
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        if not self.customer_id:
            raise ValueError("customer_id must not be empty.")
        if not self.summary or not self.summary.strip():
            raise ValueError("Interaction summary must not be empty.")
        if isinstance(self.kind, str):
            self.kind = InteractionType(self.kind)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Interaction(id={self.id!r}, customer_id={self.customer_id!r},"
            f" kind={self.kind.value!r}, summary={self.summary!r})"
        )
