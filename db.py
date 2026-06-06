import sqlite3 
import os 
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "expenses.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            note        TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            category    TEXT DEFAULT 'overall',
            amount      REAL NOT NULL,
            UNIQUE(user_id, category)
        );
    """)
    conn.commit()
    conn.close()
 

def log_expense(user_id, amount, category, note=None):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO expenses (user_id, amount, category, note) VALUES (?, ?, ?, ?)",
        (user_id, amount, category.lower(), note)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id



def get_monthly_total(user_id, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = get_connection()
    row = conn.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM expenses
        WHERE user_id = ?
          AND strftime('%Y', created_at) = ?
          AND strftime('%m', created_at) = ?
    """, (user_id, str(year), f"{month:02d}")).fetchone()
    conn.close()
    return row["total"]


def get_category_breakdown(user_id, year=None, month=None):
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    conn = get_connection()
    rows = conn.execute("""
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ?
          AND strftime('%Y', created_at) = ?
          AND strftime('%m', created_at) = ?
        GROUP BY category
        ORDER BY total DESC
    """, (user_id, str(year), f"{month:02d}")).fetchall()
    conn.close()
    return rows


def get_last_expense(user_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    conn.close()
    return row



def delete_expense(expense_id):
    conn = get_connection()
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()



def set_budget(user_id, amount, category="overall"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO budgets (user_id, category, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, category) DO UPDATE SET amount = excluded.amount
    """, (user_id, category.lower(), amount))
    conn.commit()
    conn.close()


def get_budget(user_id, category="overall"):
    conn = get_connection()
    row = conn.execute(
        "SELECT amount FROM budgets WHERE user_id = ? AND category = ?",
        (user_id, category.lower())
    ).fetchone()
    conn.close()
    return row["amount"] if row else None


def get_recent_expenses(user_id, category=None, limit=10):
    conn = get_connection()
    if category:
        rows = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ? AND category = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, category.lower(), limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM expenses
            WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    conn.close()
    return rows