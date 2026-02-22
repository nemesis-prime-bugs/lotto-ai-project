"""Database setup for Lotto 6 aus 45 data."""
import sqlite3
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'lotto.db')

os.makedirs(DATA_DIR, exist_ok=True)


def init_db():
    """Initialize the SQLite database with schema."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT UNIQUE NOT NULL,
            draw_number INTEGER NOT NULL,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER,
            zusatzzahl INTEGER,
            jackpot TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_draw_date ON draws(draw_date)
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_draw_number ON draws(draw_number)
    ''')

    conn.commit()
    return conn


def get_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


if __name__ == '__main__':
    conn = init_db()
    print(f"Database initialized at: {DB_PATH}")
    conn.close()