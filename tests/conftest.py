import pytest
from werkzeug.security import generate_password_hash
import database.db as db_module
from database.db import init_db, get_db


@pytest.fixture
def test_db(monkeypatch, tmp_path):
    """Isolated SQLite database for each test; patches DB_PATH globally."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    init_db()
    yield db_file


@pytest.fixture
def seed_user(test_db):
    """User with three expenses across three categories."""
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("Test User", "test@example.com", generate_password_hash("pass"), "2026-01-15 10:00:00"),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 100.00, "Food",      "2026-07-10", "Lunch"),
            (user_id, 200.00, "Bills",     "2026-07-05", "Electricity"),
            (user_id, 50.00,  "Transport", "2026-07-12", "Bus fare"),
        ],
    )
    conn.commit()
    conn.close()
    yield user_id


@pytest.fixture
def empty_user(test_db):
    """User with no expenses."""
    conn = get_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Empty User", "empty@example.com", generate_password_hash("pass")),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    yield user_id
