"""
Auto-Update System for Lotto 6 aus 45
Scrapes new draws from official PDF archives
"""
import sqlite3
import requests
import os
from datetime import datetime
from PyPDF2 import PdfReader
import re

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')
PDF_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs')

BASE_URL = "https://statics.win2day.at/media/NN_W2D_STAT_Lotto_{year}.pdf"


def get_latest_draw_date():
    """Get the most recent draw date in database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT MAX(draw_date) FROM draws')
    result = c.fetchone()[0]
    conn.close()
    return result


def check_for_updates():
    """Check if new PDF is available."""
    current_year = datetime.now().year
    url = BASE_URL.format(year=current_year)
    
    r = requests.head(url, timeout=10)
    return url if r.status_code == 200 else None


def download_latest_pdf():
    """Download the latest PDF."""
    url = check_for_updates()
    if not url:
        return None
    
    year = datetime.now().year
    filepath = os.path.join(PDF_DIR, f"lotto_{year}.pdf")
    
    r = requests.get(url, timeout=60)
    with open(filepath, 'wb') as f:
        f.write(r.content)
    
    return filepath


def parse_draws_from_pdf(filepath):
    """Parse draws from a single PDF file."""
    reader = PdfReader(filepath)
    draws = []
    year = int(os.path.basename(filepath).split('_')[1].split('.')[0])

    for page in reader.pages:
        text = page.extract_text()
        
        pattern = r'([SMF]o|[MW]i|[DF]o)\.\s*(\d{2})\.(\d{2})\.\s*aufsteigend\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+ZZ\s+(\d+)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            day_abbr, day, month, n1, n2, n3, n4, n5, n6, zz = match
            date_str = f"{year}-{month}-{day}"
            draws.append({
                'date': date_str,
                'numbers': [int(n1), int(n2), int(n3), int(n4), int(n5), int(n6)],
                'zz': int(zz)
            })
    
    return draws


def update_database():
    """Main update function."""
    print(f"[{datetime.now().isoformat()}] Checking for updates...")
    
    # Check if new PDF exists
    filepath = download_latest_pdf()
    if not filepath:
        print("  No new PDF available")
        return False
    
    # Parse new draws
    new_draws = parse_draws_from_pdf(filepath)
    print(f"  Found {len(new_draws)} draws in new PDF")
    
    if not new_draws:
        return False
    
    # Get last draw date in DB
    last_db_date = get_latest_draw_date()
    
    # Filter only new draws
    new_draws = [d for d in new_draws if d['date'] > last_db_date]
    print(f"  {len(new_draws)} new draws since {last_db_date}")
    
    if not new_draws:
        return False
    
    # Insert new draws
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    from datetime import datetime
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    for draw in new_draws:
        dt = datetime.strptime(draw['date'], '%Y-%m-%d')
        dow = days[dt.weekday()]
        
        try:
            c.execute('''
                INSERT INTO draws (draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl, source, is_complete_year, day_of_week)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'auto-update', 1, ?)
            ''', (draw['date'], 0, *draw['numbers'], draw['zz'], dow))
        except sqlite3.IntegrityError:
            pass  # Already exists
    
    conn.commit()
    new_count = c.rowcount
    conn.close()
    
    print(f"  Added {new_count} new draws")
    return True


def run_scheduled_update():
    """Run update and return status."""
    success = update_database()
    
    if success:
        last_date = get_latest_draw_date()
        return f"Updated! Latest draw: {last_date}"
    else:
        return "No updates available"


if __name__ == '__main__':
    print(run_scheduled_update())