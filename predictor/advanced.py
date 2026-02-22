"""
Advanced Prediction Engine for Lotto 6 aus 45
With train/test split and strategy testing
"""
import sqlite3
import random
import os
from datetime import datetime
from collections import Counter
import math

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'lotto.db')


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_draws(complete_only=False, limit=None):
    """Get draws from database."""
    conn = get_connection()
    c = conn.cursor()

    query = 'SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, is_complete_year, day_of_week FROM draws ORDER BY draw_date ASC'

    c.execute(query)
    rows = c.fetchall()
    conn.close()

    draws = []
    for row in rows:
        draws.append({
            'draw_date': row[0],
            'numbers': [row[1], row[2], row[3], row[4], row[5], row[6]],
            'zusatzzahl': row[7],
            'is_complete': row[8],
            'day_of_week': row[9]
        })

    if complete_only:
        draws = [d for d in draws if d['is_complete']]

    if limit:
        draws = draws[-limit:]

    return draws


def train_test_split(draws, test_size=0.3):
    """Split data into train and test sets (chronological)."""
    split_idx = int(len(draws) * (1 - test_size))
    return draws[:split_idx], draws[split_idx:]


# ============================================================
# STRATEGIES
# ============================================================

class FrequencyStrategy:
    """Based on number frequency - hot numbers."""

    def __init__(self, draws):
        self.draws = draws
        self.freq = self._calc_freq()

    def _calc_freq(self):
        freq = Counter()
        for draw in self.draws:
            for n in draw['numbers']:
                freq[n] += 1
        return freq

    def predict(self):
        # Pick from top 20 most frequent
        top = sorted(self.freq.keys(), key=lambda x: self.freq[x], reverse=True)[:20]
        weights = [self.freq[n] for n in top]
        nums = random.choices(top, weights=weights, k=6)
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))
        return sorted(nums)[:6]


class ColdStrategy:
    """Based on least frequent numbers."""

    def __init__(self, draws):
        self.draws = draws
        self.freq = self._calc_freq()

    def _calc_freq(self):
        freq = Counter()
        for draw in self.draws:
            for n in draw['numbers']:
                freq[n] += 1
        return freq

    def predict(self):
        # Pick from bottom 20 least frequent
        bottom = sorted(self.freq.keys(), key=lambda x: self.freq[x])[:20]
        weights = [46 - self.freq[n] for n in bottom]
        nums = random.choices(bottom, weights=weights, k=6)
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))
        return sorted(nums)[:6]


class GapStrategy:
    """Based on gap analysis - pick numbers that are due."""

    def __init__(self, draws):
        self.draws = draws
        self.gaps = self._calc_gaps()

    def _calc_gaps(self):
        # Calculate draws since each number last appeared
        gaps = {n: 0 for n in range(1, 46)}
        last_seen = {n: -1 for n in range(1, 46)}

        for idx, draw in enumerate(self.draws):
            for n in draw['numbers']:
                gaps[n] = idx - last_seen[n]
                last_seen[n] = idx

        return gaps

    def predict(self):
        # Pick numbers with largest gaps (most overdue)
        sorted_nums = sorted(self.gaps.keys(), key=lambda x: self.gaps[x], reverse=True)
        top_due = sorted_nums[:20]
        weights = [self.gaps[n] + 1 for n in top_due]
        nums = random.choices(top_due, weights=weights, k=6)
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))
        return sorted(nums)[:6]


class PairStrategy:
    """Based on common pairs."""

    def __init__(self, draws):
        self.draws = draws
        self.pairs = self._calc_pairs()

    def _calc_pairs(self):
        pairs = Counter()
        for draw in self.draws:
            nums = sorted(draw['numbers'])
            for i in range(6):
                for j in range(i+1, 6):
                    pairs[(nums[i], nums[j])] += 1
        return pairs

    def predict(self):
        # Start with most common pairs
        selected = []
        for pair, _ in self.pairs.most_common(15):
            selected.extend(pair)
        selected = list(set(selected))

        while len(selected) < 6:
            remaining = [n for n in range(1, 46) if n not in selected]
            selected.append(random.choice(remaining))

        return sorted(random.sample(selected, 6))


class BalancedStrategy:
    """Mix of hot, cold, and average numbers."""

    def __init__(self, draws):
        self.draws = draws
        self.freq = self._calc_freq()

    def _calc_freq(self):
        freq = Counter()
        for draw in self.draws:
            for n in draw['numbers']:
                freq[n] += 1
        return freq

    def predict(self):
        sorted_nums = sorted(self.freq.keys(), key=lambda x: self.freq[x])
        cold = sorted_nums[:10]
        hot = sorted_nums[-10:]
        mid = [n for n in range(1, 46) if n not in hot and n not in cold]

        nums = []
        nums.extend(random.sample(hot, min(3, len(hot))))
        nums.extend(random.sample(mid, min(2, len(mid))))
        nums.extend(random.sample(cold, min(1, len(cold))))

        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))

        return sorted(set(nums))[:6]


class PositionStrategy:
    """Based on position frequency - each position has favorite numbers."""

    def __init__(self, draws):
        self.draws = draws
        self.pos_freq = self._calc_pos_freq()

    def _calc_pos_freq(self):
        # Position 0-5 (sorted numbers)
        pos_freq = {i: Counter() for i in range(6)}
        for draw in self.draws:
            nums = sorted(draw['numbers'])
            for i, n in enumerate(nums):
                pos_freq[i][n] += 1
        return pos_freq

    def predict(self):
        nums = []
        for pos in range(6):
            # Pick from most frequent for this position
            top = self.pos_freq[pos].most_common(15)
            if top:
                choices = [n for n, _ in top]
                weights = [c for _, c in top]
                n = random.choices(choices, weights=weights)[0]
                nums.append(n)
            else:
                nums.append(random.randint(1, 45))

        # Ensure unique
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.randint(1, 45))

        return sorted(nums)[:6]


class DayOfWeekStrategy:
    """Analyze Wednesday vs Sunday draws separately."""

    def __init__(self, draws):
        self.draws = draws
        self.wed_freq = self._calc_day_freq('Wed')
        self.sun_freq = self._calc_day_freq('Sun')

    def _calc_day_freq(self, day):
        freq = Counter()
        for draw in self.draws:
            if draw['day_of_week'] == day:
                for n in draw['numbers']:
                    freq[n] += 1
        return freq

    def predict(self, day='Wed'):
        freq = self.wed_freq if day == 'Wed' else self.sun_freq
        if not freq:  # Fallback
            freq = Counter()
            for draw in self.draws:
                for n in draw['numbers']:
                    freq[n] += 1

        top = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)[:20]
        weights = [freq[n] + 1 for n in top]
        nums = random.choices(top, weights=weights, k=6)
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))
        return sorted(nums)[:6]


class SumRangeStrategy:
    """Target specific sum ranges."""

    def __init__(self, draws):
        self.draws = draws
        self.sums = self._calc_sums()

    def _calc_sums(self):
        return [sum(d['numbers']) for d in self.draws]

    def predict(self):
        # Target average sum (~140-150)
        avg_sum = sum(self.sums) / len(self.sums)

        for _ in range(100):
            nums = sorted(random.sample(range(1, 46), 6))
            if abs(sum(nums) - avg_sum) < 30:
                return nums

        return sorted(random.sample(range(1, 46), 6))


class RecencyWeightedStrategy:
    """Weight frequency by recency - recent draws matter more."""

    def __init__(self, draws, decay=0.99):
        self.draws = draws
        self.decay = decay
        self.weights = self._calc_weights()

    def _calc_weights(self):
        weights = {n: 0 for n in range(1, 46)}
        multiplier = 1.0

        for draw in reversed(self.draws):
            for n in draw['numbers']:
                weights[n] += multiplier
            multiplier *= self.decay

        return weights

    def predict(self):
        sorted_nums = sorted(self.weights.keys(), key=lambda x: self.weights[x], reverse=True)
        top = sorted_nums[:25]
        weights = [self.weights[n] + 1 for n in top]
        nums = random.choices(top, weights=weights, k=6)
        nums = list(set(nums))
        while len(nums) < 6:
            nums.append(random.choice(range(1, 46)))
        return sorted(nums)[:6]


class RandomStrategy:
    """Pure random baseline."""

    def __init__(self, draws=None):
        pass

    def predict(self):
        return sorted(random.sample(range(1, 46), 6))


# ============================================================
# TESTING FRAMEWORK
# ============================================================

def count_matches(prediction, actual):
    """Count how many numbers match."""
    return len(set(prediction) & set(actual))


def test_strategy(strategy_class, train_draws, test_draws, n_predictions=100):
    """Test a strategy against test data."""
    strategy = strategy_class(train_draws)

    matches = Counter()
    exact_matches = 0

    for test_draw in test_draws:
        actual = test_draw['numbers']

        for _ in range(n_predictions):
            pred = strategy.predict()
            m = count_matches(pred, actual)
            matches[m] += 1
            if m == 6:
                exact_matches += 1

    total = len(test_draws) * n_predictions

    return {
        'matches': dict(matches),
        'exact_matches': exact_matches,
        'total': total,
        'match_rate': {k: v/total*100 for k, v in matches.items()}
    }


def run_all_tests():
    """Run all strategies and compare."""
    print("="*70)
    print("LOTTO 6 AUS 45 - STRATEGY TESTING")
    print("="*70)

    # Get complete data only (2023-2025)
    draws = get_draws(complete_only=True)
    print(f"\nUsing {len(draws)} complete draws (2023-2025)")

    # Split 70/30
    train, test = train_test_split(draws, 0.3)
    print(f"Train: {len(train)}, Test: {len(test)}")

    # Strategies
    strategies = [
        ("Random (Baseline)", RandomStrategy),
        ("Frequency (Hot)", FrequencyStrategy),
        ("Cold Numbers", ColdStrategy),
        ("Gap/Due Numbers", GapStrategy),
        ("Common Pairs", PairStrategy),
        ("Balanced Mix", BalancedStrategy),
        ("Position Frequency", PositionStrategy),
        ("Recency Weighted", RecencyWeightedStrategy),
        ("Sum Range", SumRangeStrategy),
    ]

    results = []

    for name, strategy_class in strategies:
        result = test_strategy(strategy_class, train, test)
        results.append((name, result))

        # Calculate 3+ match rate
        rate_3plus = sum(result['match_rate'].get(i, 0) for i in [3, 4, 5, 6])

        print(f"\n{name}")
        print(f"  3+ matches: {rate_3plus:.2f}%")
        print(f"  4+ matches: {result['match_rate'].get(4, 0) + result['match_rate'].get(5, 0) + result['match_rate'].get(6, 0):.3f}%")
        print(f"  5 matches: {result['match_rate'].get(5, 0):.4f}%")
        print(f"  6 matches (JACKPOT): {result['match_rate'].get(6, 0):.6f}%")

    print("\n" + "="*70)
    print("THEORETICAL ODDS (for reference):")
    print("  3 matches: 1 in 57")
    print("  4 matches: 1 in 1,032")
    print("  5 matches: 1 in 55,491")
    print("  6 matches: 1 in 8,145,060")
    print("="*70)

    return results


def generate_predictions():
    """Generate predictions using best strategies."""
    print("\n" + "="*70)
    print("GENERATING PREDICTIONS")
    print("="*70)

    # Use all complete data
    draws = get_draws(complete_only=True)

    strategies = [
        ("Hot Numbers", FrequencyStrategy(draws)),
        ("Gap Strategy", GapStrategy(draws)),
        ("Balanced", BalancedStrategy(draws)),
        ("Pairs", PairStrategy(draws)),
        ("Recency Weighted", RecencyWeightedStrategy(draws)),
        ("Position Based", PositionStrategy(draws)),
    ]

    print("\nBest predictions from each strategy:\n")

    all_predictions = []

    for name, strategy in strategies:
        pred = strategy.predict()
        all_predictions.append(pred)
        print(f"  {name}: {' '.join(f'{n:02d}' for n in pred)}")

    # Consensus pick - numbers that appear most across strategies
    consensus = Counter()
    for pred in all_predictions:
        for n in pred:
            consensus[n] += 1

    common = [n for n, c in consensus.most_common(6)]
    print(f"\n🎯 CONSENSUS: {' '.join(f'{n:02d}' for n in common)}")

    return all_predictions


if __name__ == '__main__':
    run_all_tests()
    generate_predictions()