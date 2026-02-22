"""
Import and clean data from the old OCR project.
"""
import sqlite3
import os
import sys

# Paths
OLD_DB = '/home/madara-uchiha/.openclaw/workspace/lotto-ai-project/lottery_ocr_results.db'
NEW_DB = '/home/madara-uchiha/.openclaw/workspace/lotto-6aus45/data/lotto.db'

# Ensure data directory exists
os.makedirs(os.path.dirname(NEW_DB), exist_ok=True)


def init_new_db():
    """Initialize new database."""
    conn = sqlite3.connect(NEW_DB)
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
            source TEXT DEFAULT 'imported',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('CREATE INDEX IF NOT EXISTS idx_draw_date ON draws(draw_date)')
    conn.commit()
    return conn


def is_valid_date(date_str):
    """Check if date is valid (not in future, not corrupted)."""
    try:
        year = int(date_str[:4])
        # Valid range: 1986-2026
        return 1986 <= year <= 2026
    except:
        return False


def is_valid_number(n):
    """Check if number is valid (1-45)."""
    try:
        return 1 <= int(n) <= 45
    except:
        return False


def import_from_old_db():
    """Import and clean data from old database."""
    old_conn = sqlite3.connect(OLD_DB)
    old_c = old_conn.cursor()

    new_conn = init_new_db()
    new_c = new_conn.cursor()

    # Fetch all draws from old database
    old_c.execute('''
        SELECT d.dateDrawing, w.n1, w.n2, w.n3, w.n4, w.n5, w.n6, w.additional_number
        FROM winningCombination w
        JOIN date_of_drawing d ON w.date_id = d.id
        ORDER BY d.dateDrawing ASC
    ''')

    imported = 0
    skipped = 0
    cleaned_dates = 0

    for row in old_c.fetchall():
        date_str, n1, n2, n3, n4, n5, n6, zusatz = row

        # Skip invalid dates (like 2047)
        if not is_valid_date(date_str):
            skipped += 1
            continue

        # Try to fix some common OCR errors in dates
        # Some dates might have wrong year due to OCR
        # e.g., 2024 might be read as 2047, 2019 as 2049, etc.
        # We'll try to fix obvious cases
        if date_str.startswith('204'):
            # Likely 20XX misread - try to fix
            year = int(date_str[:4])
            if year > 2026:
                # Maybe it's 200X - try 20 + last 2 digits
                fixed = '20' + date_str[2:]
                if is_valid_date(fixed):
                    date_str = fixed
                    cleaned_dates += 1

        # Validate all numbers are in range 1-45
        numbers = [n1, n2, n3, n4, n5, n6]
        if zusatz:
            numbers.append(zusatz)

        valid_numbers = all(is_valid_number(n) for n in numbers)

        if not valid_numbers:
            skipped += 1
            continue

        # Insert into new database
        try:
            new_c.execute('''
                INSERT OR REPLACE INTO draws
                (draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date_str, 0, n1, n2, n3, n4, n5, n6, zusatz))
            imported += 1
        except sqlite3.Error as e:
            skipped += 1

    new_conn.commit()

    # Get final count
    new_c.execute('SELECT COUNT(*) FROM draws')
    total = new_c.fetchone()[0]

    print(f"Import complete!")
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")
    print(f"  Fixed dates: {cleaned_dates}")
    print(f"  Total in database: {total}")

    old_conn.close()
    new_conn.close()

    return total


if __name__ == '__main__':
    import_from_old_db()