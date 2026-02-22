"""Prediction algorithms for Lotto 6 aus 45 - Built-in Python only.

DISCLAIMER: Lotto draws are random. These are for entertainment only.
"""
import random
import sqlite3
from collections import Counter
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')


def get_all_draws():
    """Fetch all draws from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT draw_date, draw_number, n1, n2, n3, n4, n5, n6, zusatzzahl FROM draws ORDER BY draw_date ASC')
    rows = c.fetchall()
    conn.close()

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
    return {n: freq.get(n, 0) for n in range(1, 46)}


def predict_random():
    """Pure random prediction."""
    return sorted(random.sample(range(1, 46), 6))


def predict_frequency_based(top_n=15):
    """Predict using most frequent numbers (hot numbers)."""
    freq = get_number_frequency()
    hot_numbers = sorted(freq.keys(), key=lambda n: freq[n], reverse=True)[:top_n]
    weights = [freq[n] + 1 for n in hot_numbers]
    numbers = random.choices(hot_numbers, weights=weights, k=6)
    numbers = list(set(numbers))
    while len(numbers) < 6:
        remaining = list(set(range(1, 46)) - set(numbers))
        numbers.append(random.choice(remaining))
    return sorted(numbers)[:6]


def predict_cold_numbers():
    """Predict using least frequent numbers (cold numbers)."""
    freq = get_number_frequency()
    cold_numbers = sorted(freq.keys(), key=lambda n: freq[n])[:15]
    # Ensure positive weights
    weights = [max(1, 46 - freq[n]) for n in cold_numbers]
    numbers = random.choices(cold_numbers, weights=weights, k=6)
    numbers = list(set(numbers))
    while len(numbers) < 6:
        remaining = list(set(range(1, 46)) - set(numbers))
        numbers.append(random.choice(remaining))
    return sorted(numbers)[:6]


def predict_balanced():
    """Balance between hot, cold, and random numbers."""
    freq = get_number_frequency()
    sorted_by_freq = sorted(freq.keys(), key=lambda n: freq[n])
    hot = sorted_by_freq[-10:]
    cold = sorted_by_freq[:10]
    mid = list(set(range(1, 46)) - set(hot) - set(cold))

    selected = []
    selected.extend(random.sample(hot, min(3, len(hot))))
    selected.extend(random.sample(mid, min(2, len(mid))))
    selected.extend(random.sample(cold, min(1, len(cold))))

    while len(selected) < 6:
        remaining = list(set(range(1, 46)) - set(selected))
        selected.append(random.choice(remaining))

    return sorted(set(selected))[:6]


def predict_pair_based():
    """Predict using most common pairs."""
    draws = get_all_draws()
    if not draws:
        return predict_random()

    pair_counts = Counter()
    for draw in draws:
        numbers = sorted([draw[f'n{i}'] for i in range(1, 7)])
        for i in range(6):
            for j in range(i + 1, 6):
                pair_counts[(numbers[i], numbers[j])] += 1

    if not pair_counts:
        return predict_random()

    selected = []
    for pair, count in pair_counts.most_common(10):
        selected.extend(pair)

    selected = list(set(selected))
    while len(selected) < 6:
        remaining = list(set(range(1, 46)) - set(selected))
        selected.append(random.choice(remaining))

    return sorted(random.sample(selected, 6))


def get_algorithm_descriptions():
    return {
        'random': 'Pure random selection (baseline)',
        'frequency': 'Favors numbers that appear most often',
        'cold': 'Favors numbers that appear least often',
        'balanced': 'Mix of hot, cold, and average numbers',
        'pairs': 'Favors numbers that commonly appear together',
    }


def predict_algorithm(algorithm='balanced'):
    algorithms = {
        'random': predict_random,
        'frequency': predict_frequency_based,
        'cold': predict_cold_numbers,
        'balanced': predict_balanced,
        'pairs': predict_pair_based,
    }
    if algorithm not in algorithms:
        algorithm = 'balanced'
    return algorithms[algorithm]()


if __name__ == '__main__':
    print("\n🎯 PREDICTIONS")
    print("="*40)
    for algo_name, desc in get_algorithm_descriptions().items():
        numbers = predict_algorithm(algo_name)
        print(f"\n{algo_name.upper()}: {desc}")
        print(f"   Numbers: {' '.join(f'{n:02d}' for n in numbers)}")
    print("\n" + "="*40)