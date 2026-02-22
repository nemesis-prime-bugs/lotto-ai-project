"""Prediction algorithms for Lotto 6 aus 45.

DISCLAIMER: Lotto draws are random. These are for entertainment only.
"""
import random
import pandas as pd
import numpy as np
from collections import Counter
from analytics import (
    get_all_draws, get_number_frequency, get_number_gaps, get_pair_frequency
)


def predict_random():
    """Pure random prediction."""
    numbers = random.sample(range(1, 46), 6)
    return sorted(numbers)


def predict_frequency_based(top_n=15):
    """Predict using most frequent numbers (hot numbers)."""
    freq = get_number_frequency()
    hot_numbers = freq.head(top_n).index.tolist()

    # Weight random selection towards hot numbers
    weights = [freq[n] + 1 for n in hot_numbers]
    numbers = random.choices(hot_numbers, weights=weights, k=6)

    return sorted(set(numbers))[:6]


def predict_cold_numbers():
    """Predict using least frequent numbers (cold numbers)."""
    freq = get_number_frequency()
    cold_numbers = freq.nsmallest(15).index.tolist()

    weights = [46 - freq[n] for n in cold_numbers]  # Inverse weights
    numbers = random.choices(cold_numbers, weights=weights, k=6)

    return sorted(set(numbers))[:6]


def predict_gap_based():
    """Predict numbers that are "due" (haven't appeared in a while)."""
    gaps = get_number_gaps()

    # Sort by gap (largest gap = more "due")
    due_numbers = sorted(gaps.keys(), key=lambda n: gaps[n], reverse=True)

    # Weight towards numbers with larger gaps
    weights = [gaps[n] + 1 for n in due_numbers[:15]]
    numbers = random.choices(due_numbers[:15], weights=weights, k=6)

    return sorted(set(numbers))[:6]


def predict_balanced():
    """Balance between hot, cold, and random numbers."""
    freq = get_number_frequency()

    hot = freq.head(10).index.tolist()
    cold = freq.nsmallest(10).index.tolist()
    mid = list(set(range(1, 46)) - set(hot) - set(cold))

    # Mix: 3 from hot, 2 from mid, 1 from cold
    selected = []

    selected.extend(random.sample(hot, min(3, len(hot))))
    selected.extend(random.sample(mid, min(2, len(mid))))
    selected.extend(random.sample(cold, min(1, len(cold))))

    # Fill remaining if needed
    while len(selected) < 6:
        remaining = list(set(range(1, 46)) - set(selected))
        selected.append(random.choice(remaining))

    return sorted(selected)[:6]


def predict_pair_based():
    """Predict using most common pairs."""
    pairs = get_pair_frequency()

    if not pairs:
        return predict_random()

    # Start with most common pairs
    selected = []
    for pair, count in pairs[:10]:
        selected.extend(pair)

    # Remove duplicates and fill
    selected = list(set(selected))

    while len(selected) < 6:
        remaining = list(set(range(1, 46)) - set(selected))
        selected.append(random.choice(remaining))

    return sorted(random.sample(selected, 6))


def predict_monte_carlo(n_simulations=10000):
    """Use Monte Carlo simulation to find most likely combinations."""
    # Get historical statistics
    df = get_all_draws()
    number_cols = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']

    # Calculate average and std for each position
    position_stats = {}
    for i, col in enumerate(number_cols, 1):
        position_stats[i] = {
            'mean': df[col].mean(),
            'std': df[col].std()
        }

    # Simulate and track
    combinations = Counter()

    for _ in range(n_simulations):
        numbers = []
        for pos in range(1, 7):
            mean = position_stats[pos]['mean']
            std = position_stats[pos]['std']

            # Generate and ensure unique
            while True:
                num = int(np.random.normal(mean, std))
                num = max(1, min(45, num))  # Clamp to 1-45
                if num not in numbers:
                    numbers.append(num)
                    break

        combinations[tuple(sorted(numbers))] += 1

    # Return most common simulated combination
    most_common = combinations.most_common(1)[0][0]
    return list(most_common)


def predict_algorithm(algorithm='balanced'):
    """Main prediction function with algorithm selection."""
    algorithms = {
        'random': predict_random,
        'frequency': predict_frequency_based,
        'cold': predict_cold_numbers,
        'gap': predict_gap_based,
        'balanced': predict_balanced,
        'pairs': predict_pair_based,
        'monte_carlo': predict_monte_carlo
    }

    if algorithm not in algorithms:
        algorithm = 'balanced'

    return algorithms[algorithm]()


def generate_predictions(num_predictions=5, algorithm='balanced'):
    """Generate multiple predictions."""
    predictions = []

    for _ in range(num_predictions):
        pred = predict_algorithm(algorithm)
        while pred in predictions:  # Ensure uniqueness
            pred = predict_algorithm(algorithm)
        predictions.append(pred)

    return predictions


def get_algorithm_descriptions():
    """Get descriptions of available prediction algorithms."""
    return {
        'random': 'Pure random selection (baseline)',
        'frequency': 'Favors numbers that appear most often',
        'cold': 'Favors numbers that appear least often',
        'gap': 'Favors numbers that are "due" (haven\'t appeared recently)',
        'balanced': 'Mix of hot, cold, and average numbers',
        'pairs': 'Favors numbers that commonly appear together',
        'monte_carlo': 'Statistical simulation based on historical patterns'
    }