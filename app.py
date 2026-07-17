import sqlite3
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id, get_summary_stats, get_recent_transactions,
    get_category_breakdown, insert_expense, get_expense_by_id,
    update_expense, delete_expense, VALID_CATEGORIES,
)

app = Flask(__name__)
app.secret_key = "spendly-dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        name             = request.form.get("name", "").strip()
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            flash("Email already registered.")
            return render_template("register.html")

        flash("Account created — please sign in.")
        return redirect(url_for("login"))

    abort(405)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"]   = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("landing"))

    abort(405)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


def _parse_date(value):
    """Return a date object if value is a valid YYYY-MM-DD string, else None."""
    try:
        from datetime import datetime
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _preset_ranges(today):
    """Return a dict of preset name → (date_from_str, date_to_str)."""
    first_of_month = today.replace(day=1)
    three_months   = (today - timedelta(days=90)).replace(day=1)
    six_months     = (today - timedelta(days=180)).replace(day=1)
    fmt = lambda d: d.isoformat()
    return {
        "this_month":   (fmt(first_of_month), fmt(today)),
        "last_3_months":(fmt(three_months),   fmt(today)),
        "last_6_months":(fmt(six_months),     fmt(today)),
    }


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]
    today   = date.today()

    raw_from = request.args.get("date_from", "").strip()
    raw_to   = request.args.get("date_to",   "").strip()

    date_from = _parse_date(raw_from)
    date_to   = _parse_date(raw_to)

    # Reject inverted ranges
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = date_to = None

    df_str = date_from.isoformat() if date_from else None
    dt_str = date_to.isoformat()   if date_to   else None

    presets = _preset_ranges(today)

    return render_template(
        "profile.html",
        user=get_user_by_id(user_id),
        stats=get_summary_stats(user_id, df_str, dt_str),
        transactions=get_recent_transactions(user_id, date_from=df_str, date_to=dt_str),
        categories=get_category_breakdown(user_id, df_str, dt_str),
        date_from=df_str,
        date_to=dt_str,
        presets=presets,
        today=today.isoformat(),
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("add_expense.html", today=date.today().isoformat())

    # POST — validate and insert
    raw_amount      = request.form.get("amount", "").strip()
    category        = request.form.get("category", "").strip()
    raw_date        = request.form.get("date", "").strip()
    description     = request.form.get("description", "").strip() or None
    form_values     = {"amount": raw_amount, "category": category,
                       "date": raw_date, "description": description or ""}

    # Validate amount
    try:
        amount = float(raw_amount)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Amount must be a number greater than 0.")
        return render_template("add_expense.html", today=date.today().isoformat(), **form_values)

    # Validate category
    if category not in VALID_CATEGORIES:
        flash("Please select a valid category.")
        return render_template("add_expense.html", today=date.today().isoformat(), **form_values)

    # Validate date
    expense_date = _parse_date(raw_date)
    if expense_date is None:
        flash("Please enter a valid date.")
        return render_template("add_expense.html", today=date.today().isoformat(), **form_values)

    insert_expense(session["user_id"], amount, category, raw_date, description)
    flash("Expense saved.")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "GET":
        return render_template("edit_expense.html", expense=expense,
                               categories=sorted(VALID_CATEGORIES))

    # POST — validate and update
    raw_amount  = request.form.get("amount", "").strip()
    category    = request.form.get("category", "").strip()
    raw_date    = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip() or None
    form_values = {"amount": raw_amount, "category": category,
                   "date": raw_date, "description": description or ""}

    try:
        amount = float(raw_amount)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Amount must be a number greater than 0.")
        return render_template("edit_expense.html",
                               expense={**expense, **form_values},
                               categories=sorted(VALID_CATEGORIES))

    if category not in VALID_CATEGORIES:
        flash("Please select a valid category.")
        return render_template("edit_expense.html",
                               expense={**expense, **form_values},
                               categories=sorted(VALID_CATEGORIES))

    if _parse_date(raw_date) is None:
        flash("Please enter a valid date.")
        return render_template("edit_expense.html",
                               expense={**expense, **form_values},
                               categories=sorted(VALID_CATEGORIES))

    update_expense(id, session["user_id"], amount, category, raw_date, description)
    flash("Expense updated.")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense_route(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    delete_expense(id, session["user_id"])
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
