"""
Re-parse the raw OCR text with better regex patterns.
Handles OCR errors and extracts clean data.
"""
import re
import sqlite3
import os
import sys

# Paths
OCR_DIR = '/home/madara-uchiha/.openclaw/workspace/lotto-ai-project/raw-ocr-reading'
NEW_DB = '/home/madara-uchiha/.openclaw/workspace/lotto-6aus45/data/lotto.db'


def get_year_from_filename(filename):
    """Extract year from filename like processed_image_2023_1.txt"""
    match = re.search(r'(\d{4})', filename)
    return int(match.group(1)) if match else None


def parse_ocr_text(text, year):
    """Parse OCR text and extract draws."""
    draws = []

    # Pattern for date: DD.MM.YYYY or similar
    # Also catch things like 04.06 which is DD.MM (day.month)
    date_pattern = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')

    lines = text.split('\n')

    current_date = None

    for line in lines:
        # Look for date pattern
        date_match = date_pattern.search(line)
        if date_match:
            day, month, year_str = date_match.groups()
            current_date = f"{year_str}-{month}-{day}"

        # Look for lottery numbers in line
        # Pattern: 6 numbers between 1-45, possibly with a 7th (Zusatzzahl)
        numbers = re.findall(r'\b([1-9]|[1-3][0-9]|4[0-5])\b', line)

        # Filter to get valid 6+ number combinations
        if len(numbers) >= 6 and current_date:
            # Take first 6 as main, 7th as zusatzzahl if exists
            unique_numbers = []
            seen = set()
            for n in numbers:
                num = int(n)
                if num not in seen and num <= 45:
                    unique_numbers.append(num)
                    seen.add(num)

            if len(unique_numbers) >= 6:
                draw = {
                    'draw_date': current_date,
                    'n1': unique_numbers[0],
                    'n2': unique_numbers[1],
                    'n3': unique_numbers[2],
                    'n4': unique_numbers[3],
                    'n5': unique_numbers[4],
                    'n6': unique_numbers[5],
                    'zusatzzahl': unique_numbers[6] if len(unique_numbers) > 6 else None,
                }
                draws.append(draw)

    return draws


def import_all_ocr():
    """Re-parse all OCR files and import to database."""
    conn = sqlite3.connect(NEW_DB)
    c = conn.cursor()

    # Clear existing imported data
    c.execute("DELETE FROM draws WHERE source = 'ocr_reparse'")
    conn.commit()

    imported = 0
    skipped = 0

    # Get all txt files
    txt_files = sorted([f for f in os.listdir(OCR_DIR) if f.endswith('.txt')])

    for filename in txt_files:
        year = get_year_from_filename(filename)
        if not year:
            continue

        filepath = os.path.join(OCR_DIR, filename)

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        draws = parse_ocr_text(text, year)

        for draw in draws:
            # Validate date
            try:
                draw_year = int(draw['draw_date'][:4])
                if draw_year < 1986 or draw_year > 2026:
                    skipped += 1
                    continue
            except:
                skipped += 1
                continue

            # Validate numbers
            numbers = [draw[f'n{i}'] for i in range(1, 7)]
            if not all(1 <= n <= 45 for n in numbers):
                skipped += 1
                continue

            try:
                c.execute('''
                    INSERT OR REPLACE INTO draws
                    (draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ocr_reparse')
                ''', (
                    draw['draw_date'], 0,
                    draw['n1'], draw['n2'], draw['n3'],
                    draw['n4'], draw['n5'], draw['n6'],
                    draw['zusatzzahl']
                ))
                imported += 1
            except sqlite3.Error as e:
                skipped += 1

    conn.commit()

    # Get total count
    c.execute("SELECT COUNT(*) FROM draws")
    total = c.fetchone()[0]

    print(f"Re-import complete!")
    print(f"  Imported: {imported}")
    print(f"  Skipped: {skipped}")
    print(f"  Total in database: {total}")

    # Show date range
    c.execute("SELECT MIN(draw_date), MAX(draw_date) FROM draws")
    date_range = c.fetchone()
    print(f"  Date range: {date_range[0]} to {date_range[1]}")

    conn.close()


if __name__ == '__main__':
    import_all_ocr()