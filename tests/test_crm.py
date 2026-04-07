"""Unit tests for crm.crm (CRM registry)."""

import pytest

from crm import CRM, CRMError
from crm.interaction import InteractionType


@pytest.fixture()
def crm() -> CRM:
    return CRM()


@pytest.fixture()
def customer_id(crm: CRM) -> str:
    return crm.add_customer("Alice", "alice@example.com", company="Acme")


class TestAddCustomer:
    def test_returns_id(self, crm):
        cid = crm.add_customer("Alice", "alice@example.com")
        assert isinstance(cid, str) and len(cid) == 36

    def test_duplicate_email_raises(self, crm, customer_id):
        with pytest.raises(CRMError, match="already exists"):
            crm.add_customer("Alice2", "alice@example.com")

    def test_invalid_email_raises(self, crm):
        with pytest.raises(ValueError):
            crm.add_customer("Bob", "not-an-email")


class TestGetCustomer:
    def test_get_existing(self, crm, customer_id):
        c = crm.get_customer(customer_id)
        assert c.name == "Alice"
        assert c.email == "alice@example.com"

    def test_get_missing_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.get_customer("nonexistent")


class TestUpdateCustomer:
    def test_update_name(self, crm, customer_id):
        crm.update_customer(customer_id, name="Alicia")
        assert crm.get_customer(customer_id).name == "Alicia"

    def test_update_email(self, crm, customer_id):
        crm.update_customer(customer_id, email="alicia@example.com")
        assert crm.get_customer(customer_id).email == "alicia@example.com"

    def test_update_to_duplicate_email_raises(self, crm, customer_id):
        crm.add_customer("Bob", "bob@example.com")
        with pytest.raises(CRMError, match="already exists"):
            crm.update_customer(customer_id, email="bob@example.com")

    def test_update_same_email_ok(self, crm, customer_id):
        crm.update_customer(customer_id, email="alice@example.com")  # no change
        assert crm.get_customer(customer_id).email == "alice@example.com"

    def test_update_missing_customer_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.update_customer("nonexistent", name="X")


class TestDeleteCustomer:
    def test_delete_removes_customer(self, crm, customer_id):
        crm.delete_customer(customer_id)
        with pytest.raises(CRMError):
            crm.get_customer(customer_id)

    def test_delete_cascades_interactions(self, crm, customer_id):
        iid = crm.add_interaction(customer_id, InteractionType.CALL, "call")
        crm.delete_customer(customer_id)
        # Interaction should be gone
        assert iid not in crm._interactions  # noqa: SLF001

    def test_delete_missing_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.delete_customer("nonexistent")


class TestListCustomers:
    def test_empty(self, crm):
        assert crm.list_customers() == []

    def test_returns_all(self, crm):
        crm.add_customer("A", "a@x.com")
        crm.add_customer("B", "b@x.com")
        assert len(crm.list_customers()) == 2

    def test_filter_by_company(self, crm):
        crm.add_customer("A", "a@x.com", company="Foo")
        crm.add_customer("B", "b@x.com", company="Bar")
        result = crm.list_customers(company="Foo")
        assert len(result) == 1
        assert result[0].name == "A"

    def test_filter_by_company_no_match(self, crm):
        crm.add_customer("A", "a@x.com", company="Foo")
        assert crm.list_customers(company="Baz") == []


class TestFindByEmail:
    def test_found(self, crm, customer_id):
        c = crm.find_customer_by_email("alice@example.com")
        assert c is not None
        assert c.id == customer_id

    def test_not_found(self, crm):
        assert crm.find_customer_by_email("nobody@example.com") is None


class TestAddInteraction:
    def test_returns_id(self, crm, customer_id):
        iid = crm.add_interaction(customer_id, InteractionType.CALL, "hi")
        assert isinstance(iid, str) and len(iid) == 36

    def test_unknown_customer_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.add_interaction("bad", InteractionType.CALL, "hi")


class TestGetInteractions:
    def test_empty(self, crm, customer_id):
        assert crm.get_interactions(customer_id) == []

    def test_returns_for_customer(self, crm, customer_id):
        crm.add_interaction(customer_id, InteractionType.CALL, "call 1")
        crm.add_interaction(customer_id, InteractionType.EMAIL, "email 1")
        result = crm.get_interactions(customer_id)
        assert len(result) == 2

    def test_does_not_return_other_customer(self, crm, customer_id):
        cid2 = crm.add_customer("Bob", "bob@x.com")
        crm.add_interaction(cid2, InteractionType.CALL, "Bob's call")
        assert crm.get_interactions(customer_id) == []

    def test_filter_by_kind(self, crm, customer_id):
        crm.add_interaction(customer_id, InteractionType.CALL, "call")
        crm.add_interaction(customer_id, InteractionType.EMAIL, "email")
        calls = crm.get_interactions(customer_id, kind=InteractionType.CALL)
        assert len(calls) == 1
        assert calls[0].summary == "call"

    def test_sorted_newest_first(self, crm, customer_id):
        from datetime import datetime, timezone, timedelta
        from crm.interaction import Interaction

        old = Interaction(
            customer_id=customer_id,
            kind=InteractionType.NOTE,
            summary="old",
            occurred_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        )
        new = Interaction(
            customer_id=customer_id,
            kind=InteractionType.NOTE,
            summary="new",
            occurred_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        )
        crm._interactions[old.id] = old  # noqa: SLF001
        crm._interactions[new.id] = new  # noqa: SLF001
        result = crm.get_interactions(customer_id)
        assert result[0].summary == "new"
        assert result[1].summary == "old"

    def test_unknown_customer_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.get_interactions("bad")


class TestDeleteInteraction:
    def test_delete_interaction(self, crm, customer_id):
        iid = crm.add_interaction(customer_id, InteractionType.CALL, "call")
        crm.delete_interaction(iid)
        assert crm.get_interactions(customer_id) == []

    def test_delete_missing_raises(self, crm):
        with pytest.raises(CRMError, match="not found"):
            crm.delete_interaction("nonexistent")
