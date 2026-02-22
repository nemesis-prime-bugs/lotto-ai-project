# Lotto 6 aus 45 Analytics & Prediction Tool

Analytics for Austria Lotto 6 aus 45 with prediction capabilities.

## Architecture

```
/lotto-6aus45
  ├── scraper/        # Data collection from lotto.at
  ├── analytics/      # Frequency, pairs, gaps, heatmaps
  ├── predictor/      # Multiple prediction algorithms
  ├── ui/             # Streamlit dashboard
  └── data/
      └── lotto.db    # SQLite database
```

## Quick Start

```bash
cd lotto-6aus45
pip install requests beautifulsoup4 pandas streamlit matplotlib

# Scrape historical data
python scraper/scrape_all.py

# Run dashboard
streamlit run ui/app.py
```

## DISCLAIMER

Lotto draws are **truly random**. No algorithm can reliably predict winning numbers.
This tool is for **entertainment and analysis purposes only**.

Enjoy the patterns. Play responsibly. 🎰