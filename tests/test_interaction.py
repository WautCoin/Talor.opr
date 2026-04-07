"""Unit tests for crm.interaction."""

import pytest

from crm.interaction import Interaction, InteractionType


class TestInteractionCreation:
    def test_basic_creation(self):
        ix = Interaction(
            customer_id="cid-1",
            kind=InteractionType.CALL,
            summary="Initial call",
        )
        assert ix.customer_id == "cid-1"
        assert ix.kind == InteractionType.CALL
        assert ix.summary == "Initial call"
        assert ix.details == ""
        assert len(ix.id) == 36

    def test_kind_from_string(self):
        ix = Interaction(customer_id="c", kind="email", summary="hi")  # type: ignore[arg-type]
        assert ix.kind == InteractionType.EMAIL

    def test_all_kinds(self):
        for kind in InteractionType:
            ix = Interaction(customer_id="c", kind=kind, summary="s")
            assert ix.kind == kind

    def test_empty_customer_id_raises(self):
        with pytest.raises(ValueError, match="customer_id"):
            Interaction(customer_id="", kind=InteractionType.NOTE, summary="s")

    def test_empty_summary_raises(self):
        with pytest.raises(ValueError, match="summary"):
            Interaction(customer_id="c", kind=InteractionType.NOTE, summary="")

    def test_whitespace_summary_raises(self):
        with pytest.raises(ValueError, match="summary"):
            Interaction(customer_id="c", kind=InteractionType.NOTE, summary="  ")

    def test_invalid_kind_string_raises(self):
        with pytest.raises(ValueError):
            Interaction(customer_id="c", kind="unknown", summary="s")  # type: ignore[arg-type]

    def test_unique_ids(self):
        ix1 = Interaction(customer_id="c", kind=InteractionType.CALL, summary="a")
        ix2 = Interaction(customer_id="c", kind=InteractionType.CALL, summary="b")
        assert ix1.id != ix2.id
