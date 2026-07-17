"""Tests for Step 9: Delete Expense."""

import app as flask_app
from database.db import get_db
from database.queries import delete_expense, get_expense_by_id


# ------------------------------------------------------------------ #
# delete_expense (unit)                                               #
# ------------------------------------------------------------------ #

def test_delete_expense_removes_row(seed_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ? AND description = ?",
        (seed_user, "Lunch"),
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    delete_expense(expense_id, seed_user)

    assert get_expense_by_id(expense_id, seed_user) is None


def test_delete_expense_wrong_user_leaves_row(seed_user, empty_user):
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM expenses WHERE user_id = ?", (seed_user,)
    ).fetchone()
    conn.close()
    expense_id = row["id"]

    delete_expense(expense_id, empty_user)

    assert get_expense_by_id(expense_id, seed_user) is not None


def test_delete_expense_nonexistent_no_error(test_db):
    delete_expense(9999, 1)


# ------------------------------------------------------------------ #
# Route: POST /expenses/<id>/delete                                   #
# ------------------------------------------------------------------ #

def test_delete_post_unauthenticated_redirects_to_login():
    client = flask_app.app.test_client()
    r = client.post("/expenses/1/delete", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_delete_post_own_expense_redirects_to_profile():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES "
            "((SELECT id FROM users WHERE email = 'demo@spendly.com'), ?, ?, ?, ?)",
            (5.00, "Other", "2026-07-15", "delete-me-step9"),
        )
        exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        r = c.post(f"/expenses/{exp_id}/delete", follow_redirects=False)
        assert r.status_code == 302
        assert "/profile" in r.headers["Location"]


def test_delete_post_own_expense_removes_from_db():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES "
            "((SELECT id FROM users WHERE email = 'demo@spendly.com'), ?, ?, ?, ?)",
            (7.00, "Other", "2026-07-15", "delete-me-step9-check"),
        )
        exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        user_id = conn.execute(
            "SELECT id FROM users WHERE email = 'demo@spendly.com'"
        ).fetchone()["id"]
        conn.commit()
        conn.close()

        c.post(f"/expenses/{exp_id}/delete")

        assert get_expense_by_id(exp_id, user_id) is None


def test_delete_post_other_users_expense_returns_404():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Other Del", "other_del@example.com", "x"),
            )
            conn.commit()
            other_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("other_del@example.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (other_id, 10.00, "Food", "2026-07-01"),
            )
            exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        r = c.post(f"/expenses/{exp_id}/delete")
        assert r.status_code == 404


def test_delete_post_other_users_expense_row_remains():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        conn = get_db()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Other Del2", "other_del2@example.com", "x"),
            )
            conn.commit()
            other_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("other_del2@example.com",)
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
                (other_id, 15.00, "Food", "2026-07-01"),
            )
            exp_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        c.post(f"/expenses/{exp_id}/delete")

        assert get_expense_by_id(exp_id, other_id) is not None


def test_delete_post_nonexistent_returns_404():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = c.post("/expenses/999999/delete")
        assert r.status_code == 404


def test_delete_get_returns_405():
    with flask_app.app.test_client() as c:
        c.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
        r = c.get("/expenses/1/delete")
        assert r.status_code == 405
