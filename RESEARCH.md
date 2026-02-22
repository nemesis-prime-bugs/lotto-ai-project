# Lotto 6 aus 45 - Advanced ML Research & Analytics Report

## Dataset
- **Total draws:** 329 (verified from PDF archives)
- **Range:** 2023-01-01 to 2026-02-22

---

## Part 1: Basic Frequency Analysis

### Hot Numbers (Most Frequent)
| Number | Count | Deviation from Expected |
|--------|-------|------------------------|
| 3 | 61 | +17.1 |
| 27 | 57 | +13.1 |
| 1 | 51 | +7.1 |
| 16 | 50 | +6.1 |
| 25 | 50 | +6.1 |

### Cold Numbers (Least Frequent)
| Number | Count | Deviation |
|--------|-------|-----------|
| 6 | 31 | -12.9 |
| 22 | 34 | -9.9 |
| 8 | 37 | -6.9 |
| 12 | 37 | -6.9 |
| 28 | 37 | -6.9 |

---

## Part 2: Combination Repeat Analysis

### Key Finding: **NO exact 6-number combinations have repeated!**
- This confirms the randomness - with 1 in 8,145,060 combinations, repeats are extremely rare

### 5-out-of-6 Near Misses (2 found)
1. **2024-06-16** vs **2025-01-22**
   - Common: 3, 5, 29, 33, 45
   - Difference: 23 vs 40

2. **2025-01-12** vs **2026-02-15**
   - Common: 4, 5, 22, 24, 27
   - Difference: 2 vs 30

### Most Common 3-Number Groups
| Group | Count |
|-------|-------|
| (3, 9, 38) | 5x |
| (32, 36, 38) | 4x |
| (24, 25, 30) | 4x |
| (7, 13, 17) | 4x |
| (7, 13, 39) | 4x |

### Most Common 4-Number Groups
| Group | Count |
|-------|-------|
| (7, 13, 17, 39) | 3x |
| (21, 31, 42, 43) | 3x |

---

## Part 3: Advanced Pattern Analysis

### Sequential Patterns
| Pattern | Frequency |
|---------|-----------|
| Consecutive numbers | 55.6% |
| Skip-1 (e.g., 5, 7) | 46.8% |
| Same ending (e.g., 3, 13, 23) | 22.2% |

### Number Spread
| Spread | Frequency |
|--------|-----------|
| Wide (>25) | 88.1% |
| Medium (15-25) | 11.2% |
| Tight (<15) | 0.6% |

**Average spread: 33.3**

### Sum Distribution
| Sum Range | Count |
|-----------|-------|
| <100 | 40 |
| 100-130 | 100 |
| 130-160 | 120 |
| 160-190 | 57 |
| >190 | 12 |

**Average sum: 136.1**

### Odd/Even Distribution
| Odd | Even | Count |
|-----|------|-------|
| 3 | 3 | 103 (31.3%) |
| 4 | 2 | 84 (25.5%) |
| 2 | 4 | 78 (23.7% |

---

## Part 4: Markov Chain Analysis

Numbers that most often appear WITH number 3:
- 25: 12 times
- 27: 12 times
- 40: 11 times
- 35: 11 times
- 7: 10 times

---

## Part 5: ML Prediction Strategies

### Strategy 1: Combined ML
Combines frequency, recency, Markov follows, and pair patterns.

### Strategy 2: Hot Numbers
Favors most frequent numbers with recency weighting.

### Strategy 3: Cold Numbers
Favors least frequent numbers (gambler's fallacy but interesting to track).

### Strategy 4: Pair-Based
Uses most common number pairs.

---

## Research-Based Recommendations

### For Best Odds:
1. **Include 1-2 consecutive pairs** (55.6% of draws have them)
2. **Target sum 130-160** (36% of draws)
3. **Balance odd/even** (3/3 or 2/4)
4. **Spread numbers widely** (88% are spread >25)
5. **Mix hot and cold numbers**

### Patterns to Avoid:
- All even or all odd (rare)
- Tight clusters (<15 spread)
- Very low sums (<100) or very high (>190)

---

## Current Best Predictions

```
🎯 RESEARCH-BASED: 03 06 22 25 27 35
🎯 ML COMBINED:    04 09 10 24 27 44
🎯 HOT FREQUENCY:  04 05 10 25 27 35
🎯 PAIR-BASED:     01 03 25 27 35 41
```

---

## Conclusion

**Lotto is genuinely random.** No pattern can reliably predict winners. However, understanding the distribution helps:
- Set realistic expectations
- Make informed choices
- Have fun analyzing

⚠️ **Remember:** Play responsibly. The lottery is entertainment, not an investment strategy.

---

*Last updated: 2026-02-22*
*Data source: Official win2day.at PDF archives*