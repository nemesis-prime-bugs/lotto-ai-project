"""
Streamlit Dashboard for Lotto 6 aus 45 Analytics
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics import (
    get_all_draws, get_recent_draws, get_number_frequency,
    get_zusatzzahl_frequency, get_pair_frequency, get_statistics_summary
)
from predictor import (
    generate_predictions, get_algorithm_descriptions, predict_algorithm
)

# Page config
st.set_page_config(
    page_title="🎰 Lotto 6 aus 45 Analytics",
    page_icon="🎰",
    layout="wide"
)

st.title("🎰 Lotto 6 aus 45 Analytics")
st.markdown("*For entertainment purposes only — Lotto is random!*")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["📊 Dashboard", "🔢 Numbers", "🎯 Predict", "📈 Analysis"])

# Load data
@st.cache_data
def load_data():
    return get_all_draws()

@st.cache_data
def load_recent_data(days=90):
    return get_recent_draws(days)

try:
    df = load_data()
    recent_df = load_recent_data(90)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.info("Run the scraper first: `python scraper/scrape.py`")
    st.stop()

if df.empty:
    st.warning("No data found. Run the scraper first!")
    st.stop()

# Stats
total_draws = len(df)
date_range = f"{df['draw_date'].min().date()} to {df['draw_date'].max().date()}"

# Dashboard Page
if page == "📊 Dashboard":
    st.header("Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Draws", total_draws)
    col2.metric("Date Range", date_range)
    col3.metric("Years of Data", (df['draw_date'].max() - df['draw_date'].min()).days // 365)

    st.divider()

    # Recent draws
    st.subheader("Recent Draws")
    display_df = df.tail(10).copy()
    display_df['numbers'] = display_df.apply(
        lambda r: f"{r['n1']:02d} {r['n2']:02d} {r['n3']:02d} {r['n4']:02d} {r['n5']:02d} {r['n6']:02d}",
        axis=1
    )
    display_df['Z'] = display_df['zusatzzahl']
    st.dataframe(
        display_df[['draw_date', 'draw_number', 'numbers', 'Z']],
        use_container_width=True,
        hide_index=True
    )

# Numbers Page
elif page == "🔢 Numbers":
    st.header("Number Frequencies")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Main Numbers (1-45)")
        freq = get_number_frequency(df)

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.RdYlGn_r(freq / freq.max())
        freq.plot(kind='bar', ax=ax, color=colors)
        ax.set_xlabel("Number")
        ax.set_ylabel("Frequency")
        ax.set_title("Number Frequency (All Time)")
        ax.set_xticklabels(freq.index, rotation=0)
        st.pyplot(fig)

    with col2:
        st.subheader("Zusatzzahl")
        zz_freq = get_zusatzzahl_frequency(df)

        fig, ax = plt.subplots(figsize=(10, 8))
        colors = plt.cm.Blues(zz_freq / max(zz_freq.max(), 1))
        zz_freq.plot(kind='bar', ax=ax, color=colors)
        ax.set_xlabel("Number")
        ax.set_ylabel("Frequency")
        ax.set_title("Zusatzzahl Frequency")
        ax.set_xticklabels(zz_freq.index, rotation=0)
        st.pyplot(fig)

    st.divider()

    # Top/Bottom numbers
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔥 Hot Numbers")
        hot = freq.head(10)
        st.write(", ".join(f"**{n}** ({c})" for n, c in hot.items()))

    with col2:
        st.subheader("❄️ Cold Numbers")
        cold = freq.nsmallest(10)
        st.write(", ".join(f"**{n}** ({c})" for n, c in cold.items()))

# Predict Page
elif page == "🎯 Predict":
    st.header("🎯 Generate Predictions")

    st.warning("⚠️ **DISCLAIMER**: Lotto draws are completely random. These predictions are for entertainment only!")

    st.subheader("Select Algorithm")

    algorithms = get_algorithm_descriptions()

    selected_algo = st.selectbox(
        "Prediction Method",
        options=list(algorithms.keys()),
        format_func=lambda x: f"{x.title()} — {algorithms[x]}"
    )

    if st.button("🎲 Generate Numbers"):
        with st.spinner("Crunching the numbers..."):
            numbers = predict_algorithm(selected_algo)

        st.success("Your lucky numbers:")
        st.markdown(f"## 🎰 {' - '.join(f'{n:02d}' for n in numbers)}")

        # Also show additional number (Zusatzzahl)
        zusatzzahl = random.randint(1, 45)
        st.info(f"Zusatzzahl (bonus): **{zusatzzahl:02d}**")

    st.divider()

    st.subheader("Quick Predictions (All Methods)")

    if st.button("🔮 Generate All Methods"):
        all_predictions = {}
        for algo in algorithms.keys():
            all_predictions[algo] = predict_algorithm(algo)

        for algo, numbers in all_predictions.items():
            st.write(f"**{algo.title()}**: {' - '.join(f'{n:02d}' for n in numbers)}")

# Analysis Page
elif page == "📈 Analysis":
    st.header("📈 Deep Analysis")

    # Recent draws analysis
    st.subheader("Recent Draws Analysis")
    recent_days = st.slider("Days to analyze", 30, 730, 180)

    recent_df = load_recent_data(recent_days)
    recent_freq = get_number_frequency(recent_df)

    fig, ax = plt.subplots(figsize=(12, 6))
    recent_freq.plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title(f"Number Frequency (Last {recent_days} Days)")
    ax.set_xlabel("Number")
    ax.set_ylabel("Frequency")
    ax.set_xticklabels(recent_freq.index, rotation=0)
    st.pyplot(fig)

    # Statistics
    st.divider()
    st.subheader("📊 Statistics")

    stats = get_statistics_summary(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Average Sum", f"{stats['avg_sum']:.0f}")
    col2.metric("Min Sum", f"{stats['min_sum']:.0f}")
    col3.metric("Max Sum", f"{stats['max_sum']:.0f}")
    col4.metric("Even/Odd Ratio", f"{stats['even_odd_ratio']:.2f}")

    # Common pairs
    st.divider()
    st.subheader("🔗 Most Common Number Pairs")

    pairs = get_pair_frequency(df)

    if pairs:
        pair_data = [{"Numbers": f"{p[0]:02d} - {p[1]:02d}", "Count": p[1]} for p in pairs[:15]]
        st.dataframe(pd.DataFrame(pair_data), use_container_width=True, hide_index=True)

import random  # Needed for Zusatzzahl