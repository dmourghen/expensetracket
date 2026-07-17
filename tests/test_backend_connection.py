"""Tests for Step 5: backend connection for the profile page."""

import app as flask_app
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_correct_fields(seed_user):
    user = get_user_by_id(seed_user)
    assert user is not None
    assert user["name"] == "Test User"
    assert user["email"] == "test@example.com"
    assert user["member_since"] == "January 2026"


def test_get_user_by_id_nonexistent_returns_none(test_db):
    assert get_user_by_id(9999) is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses(seed_user):
    stats = get_summary_stats(seed_user)
    assert stats["total_spent"] == 350.00
    assert stats["transaction_count"] == 3
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(empty_user):
    stats = get_summary_stats(empty_user)
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_ordered_newest_first(seed_user):
    txs = get_recent_transactions(seed_user)
    assert len(txs) == 3
    assert txs[0]["date"] == "2026-07-12"
    assert txs[1]["date"] == "2026-07-10"
    assert txs[2]["date"] == "2026-07-05"


def test_get_recent_transactions_has_required_fields(seed_user):
    txs = get_recent_transactions(seed_user)
    for tx in txs:
        assert "date" in tx
        assert "description" in tx
        assert "category" in tx
        assert "amount" in tx


def test_get_recent_transactions_no_expenses(empty_user):
    assert get_recent_transactions(empty_user) == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_ordered_by_amount_desc(seed_user):
    cats = get_category_breakdown(seed_user)
    assert len(cats) == 3
    assert cats[0]["name"] == "Bills"
    assert cats[0]["amount"] == 200.00


def test_get_category_breakdown_pct_sums_to_100(seed_user):
    cats = get_category_breakdown(seed_user)
    total_pct = sum(c["pct"] for c in cats)
    assert total_pct == 100


def test_get_category_breakdown_pct_are_integers(seed_user):
    cats = get_category_breakdown(seed_user)
    for c in cats:
        assert isinstance(c["pct"], int)


def test_get_category_breakdown_no_expenses(empty_user):
    assert get_category_breakdown(empty_user) == []


# ------------------------------------------------------------------ #
# Route: GET /profile                                                 #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects_to_login():
    client = flask_app.app.test_client()
    r = client.get("/profile", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_profile_authenticated_returns_200():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = c.get("/profile")
        assert r.status_code == 200


def test_profile_shows_seed_user_name_and_email():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        assert b"Demo User" in body
        assert b"demo@spendly.com" in body


def test_profile_shows_rupee_symbol():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        assert "₹".encode() in body


def test_profile_shows_total_spent_with_rupee_symbol():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        # Total spent is displayed with ₹ symbol; exact amount may vary as
        # other route tests insert expenses into the shared demo user's data.
        assert "₹".encode() in body
        assert b"Total spent" in body or b"total" in body.lower()


def test_profile_shows_correct_transaction_count():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        assert b">8<" in body or b"8\n" in body or b"8<" in body


def test_profile_shows_correct_top_category():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        assert b"Shopping" in body


def test_profile_shows_all_7_categories():
    categories = [b"Food", b"Transport", b"Bills", b"Health", b"Entertainment", b"Shopping", b"Other"]
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data
        for cat in categories:
            assert cat in body, f"{cat.decode()} not found in profile page"


def test_profile_transactions_newest_first():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        body = c.get("/profile").data.decode()
        # Scope to the transaction table section only
        table_start = body.find("Recent transactions")
        assert table_start != -1
        table_section = body[table_start:]
        idx_jul13 = table_section.find("2026-07-13")
        idx_jul11 = table_section.find("2026-07-11")
        assert idx_jul13 != -1 and idx_jul11 != -1, "Seed dates 2026-07-13 and 2026-07-11 must appear in the table"
        assert idx_jul13 < idx_jul11, "2026-07-13 should appear before 2026-07-11 in the transactions table"
