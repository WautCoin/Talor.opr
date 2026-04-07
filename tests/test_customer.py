"""Unit tests for crm.customer."""

import pytest

from crm.customer import Customer


class TestCustomerCreation:
    def test_basic_creation(self):
        c = Customer(name="Alice", email="alice@example.com")
        assert c.name == "Alice"
        assert c.email == "alice@example.com"
        assert c.phone is None
        assert c.company is None
        assert c.notes == ""
        assert len(c.id) == 36  # UUID4

    def test_full_creation(self):
        c = Customer(
            name="Bob",
            email="bob@example.com",
            phone="+1-555-0100",
            company="Acme",
            notes="VIP customer",
        )
        assert c.phone == "+1-555-0100"
        assert c.company == "Acme"
        assert c.notes == "VIP customer"

    def test_unique_ids(self):
        c1 = Customer(name="A", email="a@x.com")
        c2 = Customer(name="B", email="b@x.com")
        assert c1.id != c2.id

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            Customer(name="", email="a@x.com")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            Customer(name="   ", email="a@x.com")

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="e-mail"):
            Customer(name="Alice", email="not-an-email")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="e-mail"):
            Customer(name="Alice", email="")


class TestCustomerUpdate:
    def setup_method(self):
        self.customer = Customer(name="Alice", email="alice@example.com")

    def test_update_name(self):
        self.customer.update(name="Alicia")
        assert self.customer.name == "Alicia"

    def test_update_email(self):
        self.customer.update(email="alicia@example.com")
        assert self.customer.email == "alicia@example.com"

    def test_update_phone(self):
        self.customer.update(phone="+44 20 1234 5678")
        assert self.customer.phone == "+44 20 1234 5678"

    def test_update_company(self):
        self.customer.update(company="NewCo")
        assert self.customer.company == "NewCo"

    def test_update_notes(self):
        self.customer.update(notes="Updated notes.")
        assert self.customer.notes == "Updated notes."

    def test_update_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            self.customer.update(name="")

    def test_update_invalid_email_raises(self):
        with pytest.raises(ValueError, match="e-mail"):
            self.customer.update(email="bad")

    def test_partial_update_does_not_touch_other_fields(self):
        self.customer.update(notes="hi")
        assert self.customer.name == "Alice"
        assert self.customer.email == "alice@example.com"
