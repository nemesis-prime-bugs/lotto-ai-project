"""
Streamlit Dashboard for Lotto 6 aus 45 Analytics
"""
import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="🎰 Lotto 6 aus 45 Analytics",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')


def get_data():
    """Get all data from database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, day_of_week
        FROM draws
        ORDER BY draw_date ASC
    ''')
    conn.close()
    df['draw_date'] = pd.to_datetime(df['draw_date'])
    return df


def get_frequency(df):
    """Calculate number frequency."""
    numbers = pd.concat([df['n1'], df['n2'], df['n3'], df['n4'], df['n5'], df['n6']])
    return Counter(numbers)


# Title
st.title("🎰 Lotto 6 aus 45 Analytics Dashboard")
st.markdown("*Based on verified data from official sources*")

# Load data
df = get_data()
freq = get_frequency(df)

# Sidebar
st.sidebar.header("📊 Dashboard Controls")

# Date filter
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['draw_date'].min().date(), df['draw_date'].max().date()),
    min_value=df['draw_date'].min().date(),
    max_value=df['draw_date'].max().date()
)

# Filter data
mask = (df['draw_date'].dt.date >= date_range[0]) & (df['draw_date'].dt.date <= date_range[1])
filtered_df = df[mask]

# Stats
st.sidebar.markdown("---")
st.sidebar.markdown("### 📈 Statistics")
st.sidebar.metric("Total Draws", len(filtered_df))
st.sidebar.metric("Date Range", f"{filtered_df['draw_date'].min().strftime('%Y-%m-%d')} to {filtered_df['draw_date'].max().strftime('%Y-%m-%d')}")

# Day filter
days = st.sidebar.multiselect(
    "Day of Week",
    options=['Wed', 'Sun'],
    default=['Wed', 'Sun']
)
if days:
    filtered_df = filtered_df[filtered_df['day_of_week'].isin(days)]

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🔥 Hot/Cold", "🎯 Predictions", "📈 Trends", "🔢 Numbers"])

# Tab 1: Overview
with tab1:
    st.header("Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        all_nums = pd.concat([filtered_df['n1'], filtered_df['n2'], filtered_df['n3'], 
                             filtered_df['n4'], filtered_df['n5'], filtered_df['n6']])
        avg_sum = all_nums.sum() / len(all_nums) * 6
        st.metric("Average Sum", f"{avg_sum:.0f}")
    
    with col2:
        st.metric("Most Common", f"{freq.most_common(1)[0][0]}")
    
    with col3:
        spreads = []
        for _, row in filtered_df.iterrows():
            nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
            spreads.append(max(nums) - min(nums))
        st.metric("Avg Spread", f"{np.mean(spreads):.1f}")
    
    with col4:
        odd_counts = []
        for _, row in filtered_df.iterrows():
            nums = [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]
            odd_counts.append(sum(1 for n in nums if n % 2 == 1))
        st.metric("Avg Odd/Even", f"{np.mean(odd_counts):.1f}/{(6-np.mean(odd_counts)):.1f}")
    
    # Recent draws
    st.subheader("Recent Draws")
    recent = filtered_df.tail(10).copy()
    recent['numbers'] = recent.apply(lambda r: f"{r['n1']:02d} {r['n2']:02d} {r['n3']:02d} {r['n4']:02d} {r['n5']:02d} {r['n6']:02d}", axis=1)
    st.dataframe(recent[['draw_date', 'day_of_week', 'numbers', 'zusatzzahl']], use_container_width=True)

# Tab 2: Hot/Cold
with tab2:
    st.header("🔥 Hot & Cold Numbers")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Hot Numbers (Most Frequent)")
        hot = freq.most_common(15)
        fig, ax = plt.subplots(figsize=(10, 6))
        nums = [n for n, c in hot]
        counts = [c for n, c in hot]
        colors = plt.cm.Reds(np.linspace(0.3, 0.9, len(nums)))
        ax.barh(range(len(nums)), counts, color=colors)
        ax.set_yticks(range(len(nums)))
        ax.set_yticklabels(nums)
        ax.set_xlabel("Frequency")
        ax.invert_yaxis()
        st.pyplot(fig)
    
    with col2:
        st.subheader("Cold Numbers (Least Frequent)")
        cold = freq.most_common()[-15:]
        fig, ax = plt.subplots(figsize=(10, 6))
        nums = [n for n, c in cold]
        counts = [c for n, c in cold]
        colors = plt.cm.Blues(np.linspace(0.3, 0.9, len(nums)))
        ax.barh(range(len(nums)), counts, color=colors)
        ax.set_yticks(range(len(nums)))
        ax.set_yticklabels(nums)
        ax.set_xlabel("Frequency")
        ax.invert_yaxis()
        st.pyplot(fig)

# Tab 3: Predictions
with tab3:
    st.header("🎯 Predictions")
    
    st.info("⚠️ Remember: Lotto is random! These are for entertainment only.")
    
    # Import prediction engine
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from predictor.ml_engine import CombinedPredictor
    
    if st.button("🎲 Generate New Predictions"):
        predictor = CombinedPredictor(get_data().to_dict('records'))
        predictions = predictor.predict(5)
        
        for i, pred in enumerate(predictions, 1):
            s = sum(pred)
            odd = sum(1 for n in pred if n % 2 == 1)
            spread = pred[-1] - pred[0]
            has_cons = any(pred[i+1] - pred[i] == 1 for i in range(5))
            
            st.success(f"**Prediction {i}:** {' '.join(f'{n:02d}' for n in pred)}")
            st.caption(f"Sum: {s} | Odd: {odd} | Spread: {spread} | Consecutive: {'Yes' if has_cons else 'No'}")
    
    st.markdown("---")
    st.subheader("Prediction Strategies")
    
    strategies = {
        "🎯 Combined ML": "Uses frequency, recency, and pattern matching",
        "🔥 Hot Numbers": "Favors most frequent numbers",
        "❄️ Cold Numbers": "Favors least frequent numbers",
        "🔢 Pairs": "Uses most common number pairs",
    }
    
    for strategy, desc in strategies.items():
        st.write(f"**{strategy}**: {desc}")

# Tab 4: Trends
with tab4:
    st.header("📈 Trends Over Time")
    
    # Draws per month
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['month'] = filtered_df_copy['draw_date'].dt.to_period('M')
    monthly_counts = filtered_df_copy.groupby('month').size()
    
    fig, ax = plt.subplots(figsize=(12, 4))
    monthly_counts.plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title("Draws Per Month")
    ax.set_xlabel("Month")
    ax.set_ylabel("Count")
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    # Sum trend
    filtered_df_copy['sum'] = (filtered_df_copy['n1'] + filtered_df_copy['n2'] + 
                               filtered_df_copy['n3'] + filtered_df_copy['n4'] + 
                               filtered_df_copy['n5'] + filtered_df_copy['n6'])
    
    fig, ax = plt.subplots(figsize=(12, 4))
    rolling_sum = filtered_df_copy['sum'].rolling(window=10).mean()
    ax.plot(filtered_df_copy['draw_date'], filtered_df_copy['sum'], alpha=0.3)
    ax.plot(filtered_df_copy['draw_date'], rolling_sum, color='red', linewidth=2)
    ax.set_title("Sum Trend (10-draw rolling average)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Sum")
    st.pyplot(fig)

# Tab 5: Number Analysis
with tab5:
    st.header("🔢 Number Analysis")
    
    # Position analysis
    st.subheader("Position Frequency")
    positions = {i: Counter() for i in range(6)}
    for _, row in filtered_df.iterrows():
        nums = sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        for i, n in enumerate(nums):
            positions[i][n] += 1
    
    # Create position heatmap data
    pos_data = np.zeros((6, 45))
    for pos in range(6):
        for n, count in positions[pos].items():
            pos_data[pos, n-1] = count
    
    fig, ax = plt.subplots(figsize=(14, 4))
    im = ax.imshow(pos_data, cmap='YlOrRd', aspect='auto')
    ax.set_yticks(range(6))
    ax.set_yticklabels(['1st', '2nd', '3rd', '4th', '5th', '6th'])
    ax.set_xlabel("Number")
    ax.set_ylabel("Position (sorted)")
    plt.colorbar(im, ax=ax, label="Count")
    st.pyplot(fig)
    
    # Consecutive analysis
    st.subheader("Consecutive Numbers")
    consec_counts = []
    for _, row in filtered_df.iterrows():
        nums = sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        count = sum(1 for i in range(5) if nums[i+1] - nums[i] == 1)
        consec_counts.append(count)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    pd.Series(consec_counts).value_counts().sort_index().plot(kind='bar', ax=ax, color='steelblue')
    ax.set_title("Consecutive Pairs per Draw")
    ax.set_xlabel("Number of Consecutive Pairs")
    ax.set_ylabel("Count")
    st.pyplot(fig)


if __name__ == '__main__':
    st.run()