"""Tests for Step 7: Add Expense."""

import app as flask_app
from database.db import get_db
from database.queries import insert_expense


# ------------------------------------------------------------------ #
# Unit tests: insert_expense                                          #
# ------------------------------------------------------------------ #

def test_insert_expense_creates_row(seed_user):
    insert_expense(seed_user, 50.0, "Food", "2026-03-20", "Lunch-step7-unique")
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch-step7-unique"),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["amount"] == 50.0
    assert row["category"] == "Food"
    assert row["date"] == "2026-03-20"
    assert row["description"] == "Lunch-step7-unique"


def test_insert_expense_null_description(seed_user):
    insert_expense(seed_user, 30.0, "Transport", "2026-03-21", None)
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? AND date = ?",
        (seed_user, "2026-03-21"),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["description"] is None


# ------------------------------------------------------------------ #
# Route tests: GET /expenses/add                                      #
# ------------------------------------------------------------------ #

def test_get_add_expense_unauthenticated_redirects():
    client = flask_app.app.test_client()
    r = client.get("/expenses/add", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_get_add_expense_authenticated_returns_200():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = c.get("/expenses/add")
        assert r.status_code == 200


def test_get_add_expense_has_all_7_category_options():
    categories = [b"Food", b"Transport", b"Bills", b"Health",
                  b"Entertainment", b"Shopping", b"Other"]
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/expenses/add").data
        for cat in categories:
            assert cat in body, f"Category {cat.decode()} missing from form"


def test_get_add_expense_has_post_form():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/expenses/add").data
        assert b"<form" in body
        assert b'method="POST"' in body or b"method='POST'" in body or b"method=POST" in body


# ------------------------------------------------------------------ #
# Route tests: POST /expenses/add                                     #
# ------------------------------------------------------------------ #

def _login_post(c, data):
    return c.post(
        "/expenses/add",
        data=data,
        follow_redirects=False,
    )


def test_post_add_expense_unauthenticated_redirects():
    client = flask_app.app.test_client()
    r = client.post("/expenses/add",
                    data={"amount": "50", "category": "Food",
                          "date": "2026-03-20", "description": "x"},
                    follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_post_add_expense_valid_redirects_to_profile():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "50.0", "category": "Food",
                             "date": "2026-03-20", "description": "Lunch"})
        assert r.status_code == 302
        assert "/profile" in r.headers["Location"]


def test_post_add_expense_inserts_into_db():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        _login_post(c, {"amount": "77.50", "category": "Health",
                        "date": "2026-04-01", "description": "Step7-test"})
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE description = ?", ("Step7-test",)
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["amount"] == 77.50
        assert row["category"] == "Health"


def test_post_missing_amount_rerenders_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "", "category": "Food",
                             "date": "2026-03-20", "description": ""})
        assert r.status_code == 200
        assert b"Amount" in r.data or b"amount" in r.data.lower()


def test_post_zero_amount_rerenders_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "0", "category": "Food",
                             "date": "2026-03-20", "description": ""})
        assert r.status_code == 200
        assert b"Amount" in r.data or b"amount" in r.data.lower()


def test_post_nonnumeric_amount_rerenders_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "abc", "category": "Food",
                             "date": "2026-03-20", "description": ""})
        assert r.status_code == 200
        assert b"Amount" in r.data or b"amount" in r.data.lower()


def test_post_invalid_category_rerenders_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "50", "category": "Weapons",
                             "date": "2026-03-20", "description": ""})
        assert r.status_code == 200
        assert b"category" in r.data.lower()


def test_post_invalid_date_rerenders_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "50", "category": "Food",
                             "date": "not-a-date", "description": ""})
        assert r.status_code == 200
        assert b"date" in r.data.lower()


def test_post_no_description_inserts_null():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = _login_post(c, {"amount": "25.0", "category": "Other",
                             "date": "2026-05-01", "description": ""})
        assert r.status_code == 302
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM expenses WHERE amount = ? AND date = ? AND category = ?",
            (25.0, "2026-05-01", "Other"),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["description"] is None
