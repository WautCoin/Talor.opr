"""crm package — Customer Relationship Management for the WautCoin ecosystem."""

from .crm import CRM, CRMError
from .customer import Customer
from .interaction import Interaction, InteractionType

__all__ = [
    "CRM",
    "CRMError",
    "Customer",
    "Interaction",
    "InteractionType",
]
