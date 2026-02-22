"""
Heatmap Visualizations for Lotto 6 aus 45
"""
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'lotto.db')


def get_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT draw_date, n1, n2, n3, n4, n5, n6, zusatzzahl, day_of_week
        FROM draws ORDER BY draw_date ASC
    ''')
    conn.close()
    df['draw_date'] = pd.to_datetime(df['draw_date'])
    return df


def create_yearly_heatmap(df, year):
    """Create yearly heatmap for a specific year."""
    year_df = df[df['draw_date'].dt.year == year]
    
    # Create heatmap data: weeks x numbers
    # Get week number for each draw
    year_df = year_df.copy()
    year_df['week'] = year_df['draw_date'].dt.isocalendar().week
    
    heatmap_data = np.zeros((53, 45))
    
    for _, row in year_df.iterrows():
        week = row['week'] - 1
        for n in [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]:
            heatmap_data[week, n-1] += 1
    
    fig, ax = plt.subplots(figsize=(14, 8))
    im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
    ax.set_xlabel("Number (1-45)")
    ax.set_ylabel("Week of Year")
    ax.set_title(f"Number Frequency Heatmap - {year}")
    plt.colorbar(im, ax=ax, label="Count")
    return fig


def create_position_heatmap(df):
    """Create position-based heatmap."""
    positions = {i: Counter() for i in range(6)}
    
    for _, row in df.iterrows():
        nums = sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        for i, n in enumerate(nums):
            positions[i][n] += 1
    
    # Create matrix
    pos_data = np.zeros((6, 45))
    for pos in range(6):
        for n, count in positions[pos].items():
            pos_data[pos, n-1] = count
    
    fig, ax = plt.subplots(figsize=(14, 4))
    im = ax.imshow(pos_data, cmap='YlOrRd', aspect='auto')
    ax.set_yticks(range(6))
    ax.set_yticklabels(['1st (smallest)', '2nd', '3rd', '4th', '5th', '6th (largest)'])
    ax.set_xlabel("Number (1-45)")
    ax.set_ylabel("Position in Sorted Draw")
    ax.set_title("Number Position Frequency Heatmap")
    plt.colorbar(im, ax=ax, label="Count")
    return fig


def create_monthly_heatmap(df):
    """Create monthly pattern heatmap."""
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Monthly frequency for each number
    monthly_data = np.zeros((12, 45))
    
    for _, row in df.iterrows():
        month = row['draw_date'].month - 1
        for n in [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]:
            monthly_data[month, n-1] += 1
    
    # Normalize by month length
    for m in range(12):
        month_df = df[df['draw_date'].dt.month == m + 1]
        if len(month_df) > 0:
            monthly_data[m] = monthly_data[m] / len(month_df) * 30  # Normalize to 30 days
    
    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(monthly_data, cmap='YlOrRd', aspect='auto')
    ax.set_yticks(range(12))
    ax.set_yticklabels(months)
    ax.set_xlabel("Number (1-45)")
    ax.set_ylabel("Month")
    ax.set_title("Monthly Number Frequency (Normalized)")
    plt.colorbar(im, ax=ax, label="Normalized Count")
    return fig


def create_day_comparison_heatmap(df):
    """Compare Wednesday vs Sunday draws."""
    days = ['Wed', 'Sun']
    
    day_data = {d: np.zeros(45) for d in days}
    
    for _, row in df.iterrows():
        if row['day_of_week'] in days:
            for n in [row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']]:
                day_data[row['day_of_week']][n-1] += 1
    
    # Normalize
    for d in days:
        day_df = df[df['day_of_week'] == d]
        if len(day_df) > 0:
            day_data[d] = day_data[d] / len(day_df) * 100  # Per 100 draws
    
    # Create difference heatmap
    diff_data = day_data['Wed'] - day_data['Sun']
    
    fig, ax = plt.subplots(figsize=(14, 3))
    im = ax.imshow([diff_data], cmap='RdBu_r', aspect='auto', vmin=-10, vmax=10)
    ax.set_yticks([])
    ax.set_xlabel("Number (1-45)")
    ax.set_title("Wednesday vs Sunday Difference (Red=Wed hotter, Blue=Sun hotter)")
    plt.colorbar(im, ax=ax, label="Difference per 100 draws")
    return fig


def create_pair_heatmap(df):
    """Create pair frequency heatmap."""
    pair_counts = Counter()
    
    for _, row in df.iterrows():
        nums = sorted([row['n1'], row['n2'], row['n3'], row['n4'], row['n5'], row['n6']])
        for i in range(6):
            for j in range(i+1, 6):
                pair_counts[(nums[i], nums[j])] += 1
    
    # Create matrix
    pair_matrix = np.zeros((45, 45))
    for (a, b), count in pair_counts.items():
        pair_matrix[a-1, b-1] = count
        pair_matrix[b-1, a-1] = count  # Symmetric
    
    fig, ax = plt.subplots(figsize=(10, 10))
    im = ax.imshow(pair_matrix, cmap='YlOrRd')
    ax.set_xlabel("Number 1")
    ax.set_ylabel("Number 2")
    ax.set_title("Number Pair Frequency")
    plt.colorbar(im, ax=ax, label="Count")
    return fig


if __name__ == '__main__':
    import pandas as pd
    
    df = get_data()
    
    print("Generating heatmaps...")
    
    # Position heatmap
    fig = create_position_heatmap(df)
    fig.savefig('heatmap_position.png', dpi=100, bbox_inches='tight')
    print("Saved: heatmap_position.png")
    
    # Monthly heatmap
    fig = create_monthly_heatmap(df)
    fig.savefig('heatmap_monthly.png', dpi=100, bbox_inches='tight')
    print("Saved: heatmap_monthly.png")
    
    # Day comparison
    fig = create_day_comparison_heatmap(df)
    fig.savefig('heatmap_day_diff.png', dpi=100, bbox_inches='tight')
    print("Saved: heatmap_day_diff.png")
    
    # Pair heatmap
    fig = create_pair_heatmap(df)
    fig.savefig('heatmap_pairs.png', dpi=100, bbox_inches='tight')
    print("Saved: heatmap_pairs.png")
    
    print("\nAll heatmaps saved!")