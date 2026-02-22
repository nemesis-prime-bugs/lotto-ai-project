"""Analytics module for Lotto 6 aus 45 - Built-in Python only."""
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_PATH = os.path.join(DATA_DIR, 'lotto.db')


def get_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def get_all_draws(limit=None):
    """Fetch all draws from database."""
    conn = get_connection()
    c = conn.cursor()

    query = 'SELECT draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl FROM draws ORDER BY draw_date ASC'

    if limit:
        query += f' LIMIT {limit}'

    c.execute(query)
    rows = c.fetchall()
    conn.close()

    # Convert to list of dicts
    draws = []
    for row in rows:
        draws.append({
            'draw_date': row[0],
            'draw_number': row[1],
            'n1': row[2], 'n2': row[3], 'n3': row[4],
            'n4': row[5], 'n5': row[6], 'n6': row[7],
            'zusatzzahl': row[8]
        })

    return draws


def get_number_frequency(draws=None):
    """Get frequency of each number (1-45)."""
    if draws is None:
        draws = get_all_draws()

    all_numbers = []
    for draw in draws:
        for i in range(1, 7):
            all_numbers.append(draw[f'n{i}'])

    freq = Counter(all_numbers)

    # Ensure all numbers 1-45 are present
    full_freq = {n: freq.get(n, 0) for n in range(1, 46)}

    return full_freq


def get_pair_frequency(draws=None):
    """Get frequency of number pairs that appear together."""
    if draws is None:
        draws = get_all_draws()

    pair_counts = Counter()

    for draw in draws:
        numbers = sorted([draw[f'n{i}'] for i in range(1, 7)])

        # All pairs from the 6 numbers
        for i in range(6):
            for j in range(i + 1, 6):
                pair = (numbers[i], numbers[j])
                pair_counts[pair] += 1

    return pair_counts.most_common(20)


def get_statistics_summary(draws=None):
    """Get overall statistics for the dataset."""
    if draws is None:
        draws = get_all_draws()

    all_numbers = []
    for draw in draws:
        for i in range(1, 7):
            all_numbers.append(draw[f'n{i}'])

    if not all_numbers:
        return {}

    return {
        'total_draws': len(draws),
        'date_range': f"{draws[0]['draw_date']} to {draws[-1]['draw_date']}",
        'avg_sum': sum(all_numbers) / len(all_numbers) * 6,
        'min_sum': min(all_numbers) * 6,
        'max_sum': max(all_numbers) * 6,
    }


def print_dashboard():
    """Print a simple console dashboard."""
    draws = get_all_draws()
    freq = get_number_frequency(draws)

    print("\n" + "="*60)
    print("🎰 LOTTO 6 AUS 45 ANALYTICS")
    print("="*60)

    stats = get_statistics_summary(draws)
    print(f"\n📊 STATISTICS")
    print(f"   Total Draws: {stats.get('total_draws', 0)}")
    print(f"   Date Range: {stats.get('date_range', 'N/A')}")
    print(f"   Avg Sum: {stats.get('avg_sum', 0):.1f}")
    print(f"   Sum Range: {stats.get('min_sum', 0):.0f} - {stats.get('max_sum', 0):.0f}")

    # Top 10 hot numbers
    sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    print(f"\n🔥 TOP 10 HOT NUMBERS")
    for i, (num, count) in enumerate(sorted_freq[:10], 1):
        print(f"   {i:2d}. {num:2d} - {count} times")

    # Top 10 cold numbers
    print(f"\n❄️ TOP 10 COLD NUMBERS")
    for i, (num, count) in enumerate(sorted_freq[-10:], 1):
        print(f"   {i:2d}. {num:2d} - {count} times")

    # Recent draws
    print(f"\n📅 RECENT DRAWS (Last 5)")
    for draw in draws[-5:]:
        nums = [draw[f'n{i}'] for i in range(1, 7)]
        zusatz = draw['zusatzzahl']
        print(f"   {draw['draw_date']}: {' '.join(f'{n:02d}' for n in nums)} Z: {zusatz:02d}")

    print("\n" + "="*60)


if __name__ == '__main__':
    print_dashboard()