"""
Scrape Lotto 6 aus 45 data from PDFs on win2day.at
"""
import requests
import re
import os
from PyPDF2 import PdfReader

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
PDF_DIR = os.path.join(DATA_DIR, 'pdfs')
DB_PATH = os.path.join(DATA_DIR, 'lotto.db')

os.makedirs(PDF_DIR, exist_ok=True)


def download_pdfs():
    """Download PDF archives from win2day."""
    base_url = "https://statics.win2day.at/media"
    
    pdfs = {
        2023: f"{base_url}/NN_W2D_STAT_Lotto_2023.pdf",
        2024: f"{base_url}/NN_W2D_STAT_Lotto_2024.pdf",
        2025: f"{base_url}/NN_W2D_STAT_Lotto_2025.pdf",
        2026: f"{base_url}/NN_W2D_STAT_Lotto_2026.pdf",
    }

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for year, url in pdfs.items():
        filepath = os.path.join(PDF_DIR, f"lotto_{year}.pdf")
        
        if os.path.exists(filepath):
            print(f"  {year}: Already downloaded")
            continue

        print(f"  Downloading {year}...")
        r = requests.get(url, headers=headers, timeout=60)
        
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(r.content)
            print(f"  {year}: Downloaded ({len(r.content)} bytes)")
        else:
            print(f"  {year}: Failed ({r.status_code})")


def parse_pdf_year(filepath, year):
    """Parse a single PDF file and extract draws."""
    reader = PdfReader(filepath)
    draws = []

    for page in reader.pages:
        text = page.extract_text()
        
        # Pattern: So. 01.01. or Mi. 04.01. + 6 numbers + ZZ
        # Example: So. 01.01. aufsteigend 1 3 24 33 39 40 ZZ 35
        pattern = r'([SMF]o|[MW]i|[DF]o)\.\s*(\d{2})\.(\d{2})\.\s*aufsteigend\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+ZZ\s+(\d+)'
        
        matches = re.findall(pattern, text)
        
        for match in matches:
            day_abbr, day, month, n1, n2, n3, n4, n5, n6, zz = match
            
            # Build date
            year_str = str(year)
            date_str = f"{year_str}-{month}-{day}"
            
            draw = {
                'draw_date': date_str,
                'n1': int(n1), 'n2': int(n2), 'n3': int(n3),
                'n4': int(n4), 'n5': int(n5), 'n6': int(n6),
                'zusatzzahl': int(zz),
            }
            draws.append(draw)

    return draws


def parse_all_pdfs():
    """Parse all downloaded PDFs and return draws."""
    all_draws = []

    for pdf_file in sorted(os.listdir(PDF_DIR)):
        if not pdf_file.endswith('.pdf'):
            continue

        year = int(pdf_file.split('_')[1].split('.')[0])
        filepath = os.path.join(PDF_DIR, pdf_file)

        print(f"Parsing {pdf_file}...")
        draws = parse_pdf_year(filepath, year)
        print(f"  Found {len(draws)} draws")
        all_draws.extend(draws)

    return all_draws


def save_to_db(draws):
    """Save draws to database."""
    import sqlite3
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure table exists
    c.execute('''
        CREATE TABLE IF NOT EXISTS draws (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            draw_date TEXT UNIQUE NOT NULL,
            draw_number INTEGER NOT NULL,
            n1 INTEGER, n2 INTEGER, n3 INTEGER,
            n4 INTEGER, n5 INTEGER, n6 INTEGER,
            zusatzzahl INTEGER,
            jackpot TEXT,
            source TEXT DEFAULT 'pdf',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    imported = 0
    for draw in draws:
        try:
            c.execute('''
                INSERT OR REPLACE INTO draws
                (draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pdf')
            ''', (draw['draw_date'], 0, draw['n1'], draw['n2'], draw['n3'],
                  draw['n4'], draw['n5'], draw['n6'], draw['zusatzzahl']))
            imported += 1
        except Exception as e:
            pass  # Skip duplicates

    conn.commit()

    # Get total
    c.execute('SELECT COUNT(*) FROM draws')
    total = c.fetchone()[0]

    conn.close()

    return imported, total


def scrape():
    """Main function."""
    print("📥 Downloading PDFs...")
    download_pdfs()

    print("\n📖 Parsing PDFs...")
    draws = parse_all_pdfs()

    print("\n💾 Saving to database...")
    imported, total = save_to_db(draws)

    print(f"\n✅ Done! Imported {imported} draws. Total in DB: {total}")


if __name__ == '__main__':
    scrape()