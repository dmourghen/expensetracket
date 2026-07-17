from datetime import datetime
from database.db import get_db


VALID_CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


def get_expense_by_id(expense_id, user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_expense(expense_id, user_id, amount, category, date, description):
    conn = get_db()
    conn.execute(
        "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? "
        "WHERE id = ? AND user_id = ?",
        (amount, category, date, description or None, expense_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_expense(expense_id, user_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    conn.commit()
    conn.close()


def insert_expense(user_id, amount, category, date, description):
    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description or None),
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    try:
        dt = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
        member_since = dt.strftime("%B %Y")
    except (ValueError, TypeError):
        member_since = row["created_at"]

    return {
        "name":         row["name"],
        "email":        row["email"],
        "member_since": member_since,
    }


def _date_filter(date_from, date_to):
    """Return (where_clause, params) for an optional date range."""
    if date_from and date_to:
        return "AND date BETWEEN ? AND ?", (date_from, date_to)
    return "", ()


def get_summary_stats(user_id, date_from=None, date_to=None):
    date_clause, date_params = _date_filter(date_from, date_to)
    conn = get_db()

    agg = conn.execute(
        f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt "
        f"FROM expenses WHERE user_id = ? {date_clause}",
        (user_id,) + date_params,
    ).fetchone()

    top = conn.execute(
        f"SELECT category, SUM(amount) AS cat_total "
        f"FROM expenses WHERE user_id = ? {date_clause} "
        f"GROUP BY category ORDER BY cat_total DESC LIMIT 1",
        (user_id,) + date_params,
    ).fetchone()

    conn.close()

    return {
        "total_spent":       agg["total"],
        "transaction_count": agg["cnt"],
        "top_category":      top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    date_clause, date_params = _date_filter(date_from, date_to)
    conn = get_db()
    rows = conn.execute(
        f"SELECT id, date, description, category, amount "
        f"FROM expenses WHERE user_id = ? {date_clause} "
        f"ORDER BY date DESC, id DESC LIMIT ?",
        (user_id,) + date_params + (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_category_breakdown(user_id, date_from=None, date_to=None):
    date_clause, date_params = _date_filter(date_from, date_to)
    conn = get_db()
    rows = conn.execute(
        f"SELECT category AS name, SUM(amount) AS amount "
        f"FROM expenses WHERE user_id = ? {date_clause} "
        f"GROUP BY category ORDER BY amount DESC",
        (user_id,) + date_params,
    ).fetchall()
    conn.close()

    if not rows:
        return []

    categories = [{"name": row["name"], "amount": row["amount"]} for row in rows]
    total = sum(c["amount"] for c in categories)

    # Compute rounded pcts for everything except the largest (index 0),
    # then assign the remainder to the largest to guarantee sum == 100.
    other_pcts = [round(c["amount"] / total * 100) for c in categories[1:]]
    pcts = [100 - sum(other_pcts)] + other_pcts

    for cat, pct in zip(categories, pcts):
        cat["pct"] = pct

    return categories
