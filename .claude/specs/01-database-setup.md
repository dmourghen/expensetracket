# Step 1 — Database Setup

## 1. Overview

This step replaces the stub implementation in `database/db.py` with a working SQLite database layer. It is the foundational step of the Spendly application because every subsequent feature — user authentication, user profiles, and expense tracking — depends on a correctly configured and accessible database.

Without this step, no data can be persisted, queried, or validated. All future steps build directly on the functions defined here.

## 2. Depends on

This is the first development step. It has no prerequisites.

## 3. Routes

- No new routes are introduced.
- Existing placeholder routes in `app.py` remain unchanged.

## 4. Database Schema

### A. users

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| name | TEXT | Not null |
| email | TEXT | Not null, unique |
| password_hash | TEXT | Not null |
| created_at | TEXT | Default `datetime('now')` |

### B. expenses

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Not null, foreign key → users(id) |
| amount | REAL | Not null |
| category | TEXT | Not null |
| date | TEXT | Not null |
| description | TEXT | Nullable |
| created_at | TEXT | Default `datetime('now')` |

`expenses.date` must use the **YYYY-MM-DD** format consistently across all inserts and reads.

## 5. Functions to Implement (`database/db.py`)

### `get_db()`

- Open a connection to `spendly.db` located in the project root.
- Set `connection.row_factory = sqlite3.Row` so rows support dictionary-like column access.
- Execute `PRAGMA foreign_keys = ON` on every connection opened.
- Return the connection.

### `init_db()`

- Create the `users` and `expenses` tables using `CREATE TABLE IF NOT EXISTS`.
- Must be safe to call multiple times without error and without affecting existing data.
- Must ensure the database schema is fully available before the application serves any route.

### `seed_db()`

- Query whether the `users` table already contains any rows.
- If rows exist, return immediately without inserting anything.
- Otherwise, insert one demonstration user:
  - Name: `Demo User`
  - Email: `demo@spendly.com`
  - Password: `demo123` — must be hashed using Werkzeug before storage; never stored as plaintext.
- Insert eight sample expenses, all linked to the demonstration user.
- The eight expenses must collectively cover all seven valid categories.
- Expense dates must be spread across the current month in YYYY-MM-DD format.
- The function must be idempotent: calling it multiple times must not produce duplicate records.

## 6. Changes to `app.py`

`app.py` must be updated to:

- Import `get_db`, `init_db`, and `seed_db` from `database.db`.
- Call `init_db()` and `seed_db()` inside a `with app.app_context():` block during application startup.
- Ensure the database is fully initialised and seeded before any route is served.

## 7. Files to Change

- `database/db.py`
- `app.py`

## 8. Files to Create

None.

## 9. Dependencies

- No new pip packages are required.
- Use `sqlite3` from the Python standard library.
- Use `werkzeug.security` (already installed via `requirements.txt`) for password hashing.

## 10. Categories — Fixed List

These are the only valid expense category values:

- Food
- Transport
- Bills
- Health
- Entertainment
- Shopping
- Other

## 11. Rules for Implementation

- Do not use an ORM.
- Do not use SQLAlchemy.
- Use parameterised SQL queries only.
- Never build SQL statements using string formatting, concatenation, f-strings, or `.format()`.
- Enable `PRAGMA foreign_keys = ON` on every database connection.
- Store expense amounts as `REAL`, not `INTEGER`.
- Hash passwords using `generate_password_hash` from `werkzeug.security`.
- `seed_db()` must be idempotent and safe to call multiple times.
- All expense dates must use YYYY-MM-DD format.

## 12. Expected Behaviour

### `get_db()`

- Returns a working SQLite connection.
- Supports dictionary-like column access through `sqlite3.Row`.
- Has foreign key enforcement enabled on the returned connection.

### `init_db()`

- Creates the `users` and `expenses` tables.
- Can be called repeatedly without raising errors.
- Preserves any existing data in the database.

### `seed_db()`

- Creates the demonstration user only when no seed data already exists.
- Stores the demonstration password as a hash, never as plaintext.
- Creates eight sample expenses linked to the demonstration user.
- Covers all seven valid expense categories across those eight records.
- Does not duplicate any records when called more than once.

The database itself must enforce:

- Unique email addresses in the `users` table.
- Valid foreign key relationships between `expenses.user_id` and `users.id`.
- `NOT NULL` constraints on all required fields.
- Correct primary key and autoincrement behaviour for both tables.

## 13. Error Handling Expectations

- Attempting to insert a duplicate email must fail due to the `UNIQUE` constraint.
- Attempting to insert an expense with an invalid `user_id` must fail due to the foreign key constraint.
- Invalid SQL queries must raise clear errors that can be used for debugging.
- Database errors must not be silently ignored.

## 14. Definition of Done

- [ ] Database file is created during application startup.
- [ ] Both database tables exist with the correct schema and constraints.
- [ ] Demonstration user exists with a securely hashed password.
- [ ] Eight sample expenses exist across all seven categories.
- [ ] Repeated application runs do not create duplicate seed data.
- [ ] Application starts without database errors.
- [ ] Foreign key enforcement works.
- [ ] All SQL queries use parameterised statements.
