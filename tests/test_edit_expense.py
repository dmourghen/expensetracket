"""Tests for Step 8: Edit Expense."""

import app as flask_app
from database.db import get_db
from database.queries import get_expense_by_id, update_expense


# ------------------------------------------------------------------ #
# get_expense_by_id                                                   #
# ------------------------------------------------------------------ #

def test_get_expense_by_id_returns_correct_row(seed_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch"),
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    expense = get_expense_by_id(expense_id, seed_user)
    assert expense is not None
    assert expense["amount"] == 100.00
    assert expense["category"] == "Food"
    assert expense["description"] == "Lunch"


def test_get_expense_by_id_wrong_user_returns_none(seed_user, empty_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ?", (seed_user,)
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    assert get_expense_by_id(expense_id, empty_user) is None


def test_get_expense_by_id_nonexistent_returns_none(test_db):
    assert get_expense_by_id(9999, 1) is None


def test_get_expense_by_id_returns_dict(seed_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ?", (seed_user,)
    ).fetchone()
    conn.close()

    result = get_expense_by_id(row["id"], seed_user)
    assert isinstance(result, dict)


# ------------------------------------------------------------------ #
# update_expense                                                      #
# ------------------------------------------------------------------ #

def test_update_expense_changes_fields(seed_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch"),
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    update_expense(expense_id, seed_user, 250.00, "Health", "2026-07-15", "Doctor visit")

    updated = get_expense_by_id(expense_id, seed_user)
    assert updated["amount"] == 250.00
    assert updated["category"] == "Health"
    assert updated["date"] == "2026-07-15"
    assert updated["description"] == "Doctor visit"


def test_update_expense_wrong_user_does_not_modify(seed_user, empty_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch"),
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    update_expense(expense_id, empty_user, 999.00, "Bills", "2026-01-01", "Hacked")

    original = get_expense_by_id(expense_id, seed_user)
    assert original["amount"] == 100.00


def test_update_expense_null_description(seed_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch"),
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    update_expense(expense_id, seed_user, 100.00, "Food", "2026-07-10", None)

    updated = get_expense_by_id(expense_id, seed_user)
    assert updated["description"] is None


# ------------------------------------------------------------------ #
# Route: GET /expenses/<id>/edit                                      #
# ------------------------------------------------------------------ #

def test_edit_get_unauthenticated_redirects_to_login():
    client = flask_app.app.test_client()
    r = client.get("/expenses/1/edit", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_edit_get_own_expense_returns_200():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.get(f"/expenses/{row['id']}/edit")
        assert r.status_code == 200


def test_edit_get_prefills_amount_and_category():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id, amount, category FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        body = c.get(f"/expenses/{row['id']}/edit").data.decode()
        assert str(row["amount"]) in body or f"{row['amount']:.2f}" in body
        assert row["category"] in body


def test_edit_get_nonexistent_returns_404():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = c.get("/expenses/999999/edit")
        assert r.status_code == 404


def test_edit_get_other_users_expense_returns_404():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Other User", "other_edit@example.com", "x"),
            )
            conn.commit()
            other_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("other_edit@example.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (other_id, 10.00, "Food", "2026-07-01"),
            )
            exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        r = c.get(f"/expenses/{exp_id}/edit")
        assert r.status_code == 404


# ------------------------------------------------------------------ #
# Route: POST /expenses/<id>/edit                                     #
# ------------------------------------------------------------------ #

def test_edit_post_unauthenticated_redirects_to_login():
    client = flask_app.app.test_client()
    r = client.post("/expenses/1/edit", data={
        "amount": "50", "category": "Food", "date": "2026-07-10",
    }, follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_edit_post_valid_redirects_to_profile():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.post(f"/expenses/{row['id']}/edit", data={
            "amount": "123.45",
            "category": "Health",
            "date": "2026-07-10",
            "description": "Updated",
        }, follow_redirects=False)
        assert r.status_code == 302
        assert "/profile" in r.headers["Location"]


def test_edit_post_invalid_amount_returns_200_with_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.post(f"/expenses/{row['id']}/edit", data={
            "amount": "not-a-number",
            "category": "Food",
            "date": "2026-07-10",
        })
        assert r.status_code == 200
        assert b"Amount must be a number" in r.data


def test_edit_post_zero_amount_returns_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.post(f"/expenses/{row['id']}/edit", data={
            "amount": "0",
            "category": "Food",
            "date": "2026-07-10",
        })
        assert r.status_code == 200
        assert b"Amount must be a number" in r.data


def test_edit_post_invalid_category_returns_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.post(f"/expenses/{row['id']}/edit", data={
            "amount": "50",
            "category": "InvalidCategory",
            "date": "2026-07-10",
        })
        assert r.status_code == 200
        assert b"valid category" in r.data


def test_edit_post_invalid_date_returns_error():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        row = conn.execute(
            "SELECT id FROM expenses WHERE user_id = "
            "(SELECT id FROM users WHERE email = 'demo@spendly.com') LIMIT 1"
        ).fetchone()
        conn.close()
        r = c.post(f"/expenses/{row['id']}/edit", data={
            "amount": "50",
            "category": "Food",
            "date": "not-a-date",
        })
        assert r.status_code == 200
        assert b"valid date" in r.data


def test_edit_post_other_users_expense_returns_404():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Other2", "other2_edit@example.com", "x"),
            )
            conn.commit()
            other_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("other2_edit@example.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (other_id, 10.00, "Food", "2026-07-01"),
            )
            exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
        finally:
            conn.close()
        r = c.post(f"/expenses/{exp_id}/edit", data={
            "amount": "99",
            "category": "Food",
            "date": "2026-07-01",
        })
        assert r.status_code == 404
