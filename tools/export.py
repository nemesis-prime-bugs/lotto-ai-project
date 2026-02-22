"""
Data Export and Backup Utilities for Lotto 6 aus 45
"""
import sqlite3
import csv
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'exports')
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backups')

os.makedirs(EXPORT_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


def export_to_csv(filename=None):
    """Export all draws to CSV."""
    if not filename:
        filename = f"lotto_draws_{datetime.now().strftime('%Y%m%d')}.csv"
    
    filepath = os.path.join(EXPORT_DIR, filename)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, day_of_week
        FROM draws
        ORDER BY draw_date ASC
    ''')
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'n1', 'n2', 'n3', 'n4', 'n5', 'n6', 'zusatzzahl', 'day_of_week'])
        for row in c.fetchall():
            writer.writerow(row)
    
    conn.close()
    
    print(f"✅ Exported to: {filepath}")
    return filepath


def export_to_json(filename=None):
    """Export all draws to JSON."""
    if not filename:
        filename = f"lotto_draws_{datetime.now().strftime('%Y%m%d')}.json"
    
    filepath = os.path.join(EXPORT_DIR, filename)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, day_of_week
        FROM draws
        ORDER BY draw_date ASC
    ''')
    
    data = []
    for row in c.fetchall():
        data.append({
            'date': row[0],
            'numbers': [row[1], row[2], row[3], row[4], row[5], row[6]],
            'zusatzzahl': row[7],
            'day_of_week': row[8]
        })
    
    conn.close()
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported to: {filepath}")
    return filepath


def backup_database():
    """Create a timestamped backup of the database."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"lotto_backup_{timestamp}.db"
    filepath = os.path.join(BACKUP_DIR, filename)
    
    # Copy database
    conn = sqlite3.connect(DB_PATH)
    backup_conn = sqlite3.connect(filepath)
    
    c = conn.cursor()
    backup_c = backup_conn.cursor()
    
    # Copy tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in c.fetchall():
        table_name = row[0]
        if table_name != 'sqlite_sequence':
            backup_c.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
    
    backup_conn.commit()
    conn.close()
    backup_conn.close()
    
    print(f"✅ Backup created: {filepath}")
    return filepath


def get_stats():
    """Get database statistics."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    stats = {}
    
    # Total draws
    c.execute('SELECT COUNT(*) FROM draws')
    stats['total_draws'] = c.fetchone()[0]
    
    # Date range
    c.execute('SELECT MIN(draw_date), MAX(draw_date) FROM draws')
    date_range = c.fetchone()
    stats['date_range'] = f"{date_range[0]} to {date_range[1]}"
    
    # Complete years
    c.execute('''
        SELECT COUNT(*) FROM (
            SELECT strftime('%Y', draw_date) as year
            FROM draws
            GROUP BY year
            HAVING COUNT(*) >= 100
        )
    ''')
    stats['complete_years'] = c.fetchone()[0]
    
    # File sizes
    db_size = os.path.getsize(DB_PATH)
    stats['db_size'] = f"{db_size / 1024:.1f} KB"
    
    conn.close()
    
    return stats


def list_exports():
    """List available export files."""
    files = os.listdir(EXPORT_DIR)
    return sorted(files)


def list_backups():
    """List available backups."""
    files = os.listdir(BACKUP_DIR)
    return sorted(files)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'csv':
            export_to_csv()
        elif cmd == 'json':
            export_to_json()
        elif cmd == 'backup':
            backup_database()
        elif cmd == 'stats':
            stats = get_stats()
            for k, v in stats.items():
                print(f"  {k}: {v}")
        elif cmd == 'list-exports':
            for f in list_exports():
                print(f"  {f}")
        elif cmd == 'list-backups':
            for f in list_backups():
                print(f"  {f}")
    else:
        print("Usage: python export.py [csv|json|backup|stats|list-exports|list-backups]")
        print("\nStats:")
        stats = get_stats()
        for k, v in stats.items():
            print(f"  {k}: {v}")