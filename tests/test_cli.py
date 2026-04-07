"""Integration tests for the CRM CLI (__main__)."""

import json
import os

import pytest

from crm.__main__ import main


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "test_crm.json")


def run(*args, db):
    main(["--db", db, *args])


class TestCLIAdd:
    def test_add_customer(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "alice@example.com", db=db_path)
        out = capsys.readouterr().out
        assert "Added customer" in out

    def test_add_persists(self, db_path):
        run("add", "--name", "Alice", "--email", "alice@example.com", db=db_path)
        assert os.path.exists(db_path)
        with open(db_path) as fh:
            data = json.load(fh)
        assert len(data["customers"]) == 1
        assert data["customers"][0]["email"] == "alice@example.com"

    def test_duplicate_email_exits(self, db_path):
        run("add", "--name", "Alice", "--email", "alice@example.com", db=db_path)
        with pytest.raises(SystemExit):
            run("add", "--name", "Alice2", "--email", "alice@example.com", db=db_path)


class TestCLIList:
    def test_list_empty(self, db_path, capsys):
        run("list", db=db_path)
        assert "No customers" in capsys.readouterr().out

    def test_list_shows_customers(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "alice@example.com", db=db_path)
        run("list", db=db_path)
        out = capsys.readouterr().out
        assert "Alice" in out

    def test_list_filter_by_company(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "a@x.com", "--company", "Foo", db=db_path)
        run("add", "--name", "Bob", "--email", "b@x.com", "--company", "Bar", db=db_path)
        run("list", "--company", "Foo", db=db_path)
        out = capsys.readouterr().out
        assert "Alice" in out
        assert "Bob" not in out


class TestCLIInteract:
    def setup_method(self):
        self._cid = None

    def _add_and_get_id(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "alice@example.com", db=db_path)
        capsys.readouterr()  # flush
        with open(db_path) as fh:
            data = json.load(fh)
        return data["customers"][0]["id"]

    def test_log_interaction(self, db_path, capsys):
        cid = self._add_and_get_id(db_path, capsys)
        run("interact", "--id", cid, "--kind", "call", "--summary", "hi", db=db_path)
        out = capsys.readouterr().out
        assert "Logged interaction" in out

    def test_interact_unknown_customer_exits(self, db_path):
        with pytest.raises(SystemExit):
            run("interact", "--id", "bad-id", "--kind", "call", "--summary", "hi", db=db_path)


class TestCLIHistory:
    def test_history_empty(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "a@x.com", db=db_path)
        capsys.readouterr()
        with open(db_path) as fh:
            cid = json.load(fh)["customers"][0]["id"]
        run("history", "--id", cid, db=db_path)
        assert "No interactions" in capsys.readouterr().out

    def test_history_shows_interactions(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "a@x.com", db=db_path)
        capsys.readouterr()
        with open(db_path) as fh:
            cid = json.load(fh)["customers"][0]["id"]
        run("interact", "--id", cid, "--kind", "email", "--summary", "welcome", db=db_path)
        capsys.readouterr()
        run("history", "--id", cid, db=db_path)
        assert "welcome" in capsys.readouterr().out


class TestCLIDelete:
    def test_delete_customer(self, db_path, capsys):
        run("add", "--name", "Alice", "--email", "a@x.com", db=db_path)
        capsys.readouterr()
        with open(db_path) as fh:
            cid = json.load(fh)["customers"][0]["id"]
        run("delete", "--id", cid, db=db_path)
        assert "Deleted" in capsys.readouterr().out

    def test_delete_missing_exits(self, db_path):
        with pytest.raises(SystemExit):
            run("delete", "--id", "no-such-id", db=db_path)
