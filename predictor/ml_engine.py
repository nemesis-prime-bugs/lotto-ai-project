"""
Advanced Prediction Engine for Lotto 6 aus 45
Contains: Bayesian, Monte Carlo, and ML-based predictions
"""
import sqlite3
import random
from collections import Counter, defaultdict
from itertools import combinations
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')


def get_draws(complete_only=True):
    """Get draws from database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = 'SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, day_of_week FROM draws ORDER BY draw_date ASC'
    
    c.execute(query)
    rows = c.fetchall()
    conn.close()
    
    draws = []
    for r in rows:
        draws.append({
            'date': r[0],
            'numbers': [r[1], r[2], r[3], r[4], r[5], r[6]],
            'zz': r[7],
            'dow': r[8]
        })
    
    return draws


def extract_features(draw):
    """Extract features from a draw."""
    nums = sorted(draw['numbers'])
    
    return {
        'sum': sum(nums),
        'spread': nums[-1] - nums[0],
        'odd_count': sum(1 for n in nums if n % 2 == 1),
        'has_consecutive': any(nums[i+1] - nums[i] == 1 for i in range(5)),
        'consecutive_pairs': sum(1 for i in range(5) if nums[i+1] - nums[i] == 1),
    }


class BayesianPredictor:
    """Bayesian inference-based prediction."""
    
    def __init__(self, draws):
        self.draws = draws
        self.total_draws = len(draws)
        self._calc_probabilities()
    
    def _calc_probabilities(self):
        # Prior (frequency based)
        freq = Counter()
        for d in self.draws:
            for n in d['numbers']:
                freq[n] += 1
        
        self.prior = {n: (freq[n] + 1) / (self.total_draws * 6 + 45) for n in range(1, 46)}
        
        # Posterior (considering recent draws)
        recent = self.draws[-50:]
        recent_freq = Counter()
        for d in recent:
            for n in d['numbers']:
                recent_freq[n] += 1
        
        self.posterior = {}
        for n in range(1, 46):
            likelihood = (recent_freq[n] + 1) / (50 * 6 + 45)
            self.posterior[n] = self.prior[n] * likelihood
        
        total = sum(self.posterior.values())
        self.posterior = {n: p/total for n, p in self.posterior.items()}
    
    def predict(self):
        numbers = list(range(1, 46))
        weights = [self.posterior[n] for n in numbers]
        pred = random.choices(numbers, weights=weights, k=6)
        pred = sorted(set(pred))
        
        while len(pred) < 6:
            remaining = [n for n in range(1, 46) if n not in pred]
            pred.append(random.choice(remaining))
        
        return sorted(pred)[:6]


class MonteCarloPredictor:
    """Monte Carlo simulation-based prediction."""
    
    def __init__(self, draws):
        self.draws = draws
        self.all_numbers = []
        for d in draws:
            self.all_numbers.extend(d['numbers'])
        
        self.mean = sum(self.all_numbers) / len(self.all_numbers)
        self.spreads = [extract_features(d)['spread'] for d in draws]
        self.avg_spread = sum(self.spreads) / len(self.spreads)
    
    def predict(self, method='constrained', n_sims=1000):
        """Generate prediction using Monte Carlo."""
        predictions = Counter()
        
        for _ in range(n_sims):
            if method == 'constrained':
                # Random with sum constraint
                pred = sorted(random.sample(range(1, 46), 6))
                while abs(sum(pred) - self.mean * 6) > 30:
                    pred = sorted(random.sample(range(1, 46), 6))
            elif method == 'historical':
                # Vary around historical draw
                template = random.choice(self.draws)
                pred = list(template['numbers'])
                for i in range(3):
                    idx = random.randint(0, 5)
                    pred[idx] = random.randint(1, 45)
                pred = sorted(set(pred))
            else:
                pred = sorted(random.sample(range(1, 46), 6))
            
            predictions[tuple(pred)] += 1
        
        return predictions.most_common(1)[0][0]
    
    def predict_diverse(self, n=5):
        """Generate n diverse predictions."""
        results = set()
        while len(results) < n:
            results.add(tuple(self.predict('constrained')))
        return [list(r) for r in results]


class MLPredictor:
    """Machine learning-based prediction using feature rules."""
    
    def __init__(self, draws):
        self.draws = draws
        self.freq = Counter()
        for d in draws:
            for n in d['numbers']:
                self.freq[n] += 1
        
        self.features = [extract_features(d) for d in draws]
    
    def score_prediction(self, pred):
        """Score a prediction based on historical patterns."""
        nums = sorted(pred)
        score = 100
        
        # Sum score
        s = sum(nums)
        if 130 <= s <= 160:
            score += 20
        elif 120 <= s <= 170:
            score += 10
        
        # Odd/even score
        odd = sum(1 for n in nums if n % 2 == 1)
        if odd in [2, 3, 4]:
            score += 15
        
        # Spread score
        spread = nums[-1] - nums[0]
        if 25 <= spread <= 40:
            score += 15
        
        # Consecutive score
        has_cons = any(nums[i+1] - nums[i] == 1 for i in range(5))
        if has_cons:
            score += 10
        
        return score
    
    def predict(self):
        """Generate ML-based prediction."""
        hot = sorted(self.freq.keys(), key=lambda x: self.freq[x], reverse=True)[:20]
        weights = [self.freq[n] for n in hot]
        
        for _ in range(1000):
            pred = random.choices(hot, weights=weights, k=8)
            pred = sorted(set(pred))
            
            # Check constraints
            s = sum(pred)
            if not (130 <= s <= 160):
                continue
            
            odd = sum(1 for n in pred if n % 2 == 1)
            if odd not in [2, 3, 4]:
                continue
            
            spread = pred[-1] - pred[0]
            if spread < 20:
                continue
            
            has_cons = any(pred[i+1] - pred[i] == 1 for i in range(len(pred)-1))
            if not has_cons:
                continue
            
            return sorted(pred[:6])
        
        return sorted(random.sample(range(1, 46), 6))


class FrequencyPredictor:
    """Simple frequency-based prediction."""
    
    def __init__(self, draws):
        self.freq = Counter()
        for d in draws:
            for n in d['numbers']:
                self.freq[n] += 1
    
    def predict(self, strategy='hot'):
        if strategy == 'hot':
            numbers = sorted(self.freq.keys(), key=lambda x: self.freq[x], reverse=True)[:15]
            weights = [self.freq[n] for n in numbers]
        elif strategy == 'cold':
            numbers = sorted(self.freq.keys(), key=lambda x: self.freq[x])[:15]
            weights = [46 - self.freq[n] for n in numbers]
        else:
            numbers = list(range(1, 46))
            weights = [1] * 45
        
        pred = random.choices(numbers, weights=weights, k=6)
        pred = sorted(set(pred))
        
        while len(pred) < 6:
            remaining = [n for n in range(1, 46) if n not in pred]
            pred.append(random.choice(remaining))
        
        return sorted(pred)[:6]


class CombinedPredictor:
    """Combines all predictors for ensemble prediction."""
    
    def __init__(self, draws):
        self.draws = draws
        self.bayesian = BayesianPredictor(draws)
        self.monte_carlo = MonteCarloPredictor(draws)
        self.ml = MLPredictor(draws)
        self.frequency = FrequencyPredictor(draws)
    
    def predict(self, n=1):
        """Generate predictions using all methods."""
        predictions = []
        
        # Bayesian
        predictions.append(self.bayesian.predict())
        
        # Monte Carlo
        predictions.extend(self.monte_carlo.predict_diverse(2))
        
        # ML
        predictions.append(self.ml.predict())
        
        # Frequency
        predictions.append(self.frequency.predict('hot'))
        
        # Score and return best
        scored = [(p, self.ml.score_prediction(p)) for p in predictions]
        scored.sort(key=lambda x: -x[1])
        
        if n == 1:
            return scored[0][0]
        return [p for p, s in scored[:n]]


def generate_predictions(n=5):
    """Main function to generate predictions."""
    draws = get_draws()
    predictor = CombinedPredictor(draws)
    return predictor.predict(n)


if __name__ == '__main__':
    print("="*60)
    print("ADVANCED PREDICTION ENGINE")
    print("="*60)
    
    predictions = generate_predictions(5)
    
    print("\nGenerated Predictions:")
    for i, pred in enumerate(predictions, 1):
        s = sum(pred)
        odd = sum(1 for n in pred if n % 2 == 1)
        print(f"  {i}. {' '.join(f'{n:02d}' for n in pred)} (sum:{s}, odd:{odd})")
    
    print("\nBest Prediction:")
    best = predictions[0]
    print(f"  {' '.join(f'{n:02d}' for n in best)}")