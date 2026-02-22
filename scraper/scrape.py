"""
Scraper for lotto 6 aus 45 data from 6richtige.at
No OCR needed - parse HTML tables directly.
"""
import requests
from html.parser import HTMLParser
import re
import sqlite3
from datetime import datetime
import time
import os

BASE_URL = "https://www.6richtige.at"
ARCHIVE_URL = BASE_URL + "/zahlenarchiv_at_{year}.html"

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'lotto.db')

os.makedirs(DATA_DIR, exist_ok=True)


def init_db():
    """Initialize the SQLite database."""
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
    c.execute('CREATE INDEX IF NOT EXISTS idx_draw_date ON draws(draw_date)')
    conn.commit()
    return conn


def fetch_page(year):
    """Fetch archive page for a given year."""
    url = ARCHIVE_URL.format(year=year)
    print(f"Fetching: {url}")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {year}: {e}")
        return None


def parse_draws(html, year):
    """Parse draw data from HTML using built-in parser."""
    from html.parser import HTMLParser

    class TableParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tables = []
            self.current_table = []
            self.current_row = []
            self.in_td = False
            self.current_data = ""

        def handle_starttag(self, tag, attrs):
            if tag == 'table':
                self.current_table = []
            elif tag == 'tr':
                self.current_row = []
            elif tag == 'td' or tag == 'th':
                self.in_td = True
                self.current_data = ""

        def handle_endtag(self, tag):
            if tag == 'table' and self.current_table:
                self.tables.append(self.current_table)
            elif tag == 'tr' and self.current_row:
                self.current_table.append(self.current_row)
            elif tag == 'td' or tag == 'th':
                self.in_td = False
                self.current_row.append(self.current_data.strip())

        def handle_data(self, data):
            if self.in_td:
                self.current_data += data

    parser = TableParser()
    parser.feed(html)

    draws = []

    # Pattern for date: "Mi 24.01.2024" or "So 05.05.2024"
    date_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')

    for table in parser.tables:
        for row in table:
            if len(row) < 3:
                continue

            # Find date in row
            date_text = ' '.join(row)
            date_match = date_pattern.search(date_text)

            if date_match:
                day, month, year_str = date_match.groups()
                draw_date = f"{year_str}-{month}-{day}"

                # Find all numbers in row
                numbers = []
                for cell in row:
                    # Extract numbers 1-45
                    nums = re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', cell)
                    for n in nums:
                        num = int(n)
                        if num not in numbers and 1 <= num <= 45:
                            numbers.append(num)

                if len(numbers) >= 6:
                    draw_data = {
                        'draw_date': draw_date,
                        'draw_number': 0,
                        'n1': numbers[0], 'n2': numbers[1], 'n3': numbers[2],
                        'n4': numbers[3], 'n5': numbers[4], 'n6': numbers[5],
                        'zusatzzahl': numbers[6] if len(numbers) > 6 else None,
                        'jackpot': None
                    }
                    draws.append(draw_data)

    return draws


def save_draws(conn, draws):
    """Save parsed draws to database."""
    c = conn.cursor()
    saved = 0

    for draw in draws:
        try:
            c.execute('''
                INSERT OR IGNORE INTO draws
                (draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl, jackpot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                draw['draw_date'], draw['draw_number'],
                draw['n1'], draw['n2'], draw['n3'],
                draw['n4'], draw['n5'], draw['n6'],
                draw['zusatzzahl'], draw['jackpot']
            ))
            if c.rowcount > 0:
                saved += 1
        except sqlite3.Error as e:
            print(f"Error saving {draw['draw_date']}: {e}")

    conn.commit()
    return saved


def scrape_year(year, conn):
    """Scrape data for a specific year."""
    html = fetch_page(year)

    if html:
        draws = parse_draws(html, year)
        print(f"  Found {len(draws)} draws for {year}")

        if draws:
            saved = save_draws(conn, draws)
            print(f"  Saved {saved} new draws")
            return draws

    return []


def scrape_all(start_year=1986, end_year=None):
    """Scrape all years from start_year to end_year (or current year)."""
    if end_year is None:
        end_year = datetime.now().year

    conn = init_db()

    total_draws = 0

    for year in range(start_year, end_year + 1):
        draws = scrape_year(year, conn)
        total_draws += len(draws)

        # Be polite to the server
        time.sleep(1)

    conn.close()

    print(f"\nTotal: {total_draws} draws scraped")
    return total_draws


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        conn = init_db()
        scrape_year(year, conn)
        conn.close()
    else:
        scrape_all()