"""Visualize spending by category, merchant, and time."""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np


def monthly_spend_by_category(df, output_path='_chart_monthly_category.png'):
    """Stacked bar chart: monthly spend by category."""
    df = df.copy()
    df['month'] = pd.to_datetime(df['timestamp']).dt.to_period('M')

    monthly = df.groupby(['month', 'category'])['amount'].sum().unstack(fill_value=0)

    fig, ax = plt.subplots(figsize=(14, 6))
    monthly.plot(kind='bar', stacked=True, ax=ax, width=0.7)

    ax.set_title('Monthly Spending by Category', fontsize=14, fontweight='bold')
    ax.set_xlabel('Month')
    ax.set_ylabel('Amount (CNY)')
    ax.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"Saved: {output_path}")
    return fig


def top_merchants(df, n=15, output_path='_chart_top_merchants.png'):
    """Bar chart: top merchants by total spend."""
    top = df.groupby('merchant')['amount'].sum().nlargest(n).sort_values()

    fig, ax = plt.subplots(figsize=(12, 6))
    top.plot(kind='barh', ax=ax, color='steelblue')

    ax.set_title(f'Top {n} Merchants by Spending', fontsize=14, fontweight='bold')
    ax.set_xlabel('Total Spend (CNY)')
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"Saved: {output_path}")
    return fig


def cumulative_spend_over_time(df, output_path='_chart_cumulative.png'):
    """Line chart: cumulative spending over time."""
    df = df.copy()
    df = df.sort_values('timestamp')
    df['cumulative'] = df['amount'].cumsum()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(pd.to_datetime(df['timestamp']), df['cumulative'], linewidth=2, color='darkgreen')
    ax.fill_between(pd.to_datetime(df['timestamp']), df['cumulative'], alpha=0.3, color='lightgreen')

    ax.set_title('Cumulative Spending Over Time', fontsize=14, fontweight='bold')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative Amount (CNY)')
    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"Saved: {output_path}")
    return fig


def category_breakdown(df, output_path='_chart_category_pie.png'):
    """Pie chart: total spending by category."""
    category_totals = df.groupby('category')['amount'].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = plt.cm.Set3(np.linspace(0, 1, len(category_totals)))
    wedges, texts, autotexts = ax.pie(
        category_totals.values,
        labels=category_totals.index,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors
    )

    ax.set_title('Spending Distribution by Category', fontsize=14, fontweight='bold')

    # Improve text readability
    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_color('black')
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"Saved: {output_path}")
    return fig


def spending_summary(df):
    """Print and save spending summary statistics."""
    print("\n" + "="*70)
    print("SPENDING SUMMARY")
    print("="*70)

    total = df['amount'].sum()
    mean = df['amount'].mean()
    median = df['amount'].median()
    std = df['amount'].std()

    print(f"\nTotal spending: ¥{total:,.2f}")
    print(f"Average transaction: ¥{mean:.2f}")
    print(f"Median transaction: ¥{median:.2f}")
    print(f"Std deviation: ¥{std:.2f}")

    print(f"\nByCategory:")
    category_stats = df.groupby('category')['amount'].agg(['count', 'sum', 'mean'])
    category_stats = category_stats.sort_values('sum', ascending=False)

    with open('_spending_summary.txt', 'w', encoding='utf-8') as f:
        f.write("SPENDING SUMMARY\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total spending: CNY {total:,.2f}\n")
        f.write(f"Average transaction: CNY {mean:.2f}\n")
        f.write(f"Median transaction: CNY {median:.2f}\n")
        f.write(f"Transactions: {len(df)}\n\n")

        f.write("BY CATEGORY:\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Category':30s} {'Count':>6s} {'Total':>12s} {'Average':>12s}\n")
        f.write("-"*80 + "\n")

        for cat, row in category_stats.iterrows():
            count = int(row['count'])
            total_cat = row['sum']
            avg_cat = row['mean']
            f.write(f"{cat:30s} {count:6d} CNY {total_cat:10,.2f} CNY {avg_cat:10,.2f}\n")

    print("Summary saved to _spending_summary.txt")


if __name__ == '__main__':
    print("="*70)
    print("STAGE 7: VISUALIZATION")
    print("="*70)

    # Load classified data
    df = pd.read_csv('data/processed/transactions_classified.csv')
    print(f"\n1. Loaded {len(df)} classified transactions")

    # Create visualizations
    print(f"\n2. Creating charts...")
    monthly_spend_by_category(df)
    top_merchants(df, n=15)
    cumulative_spend_over_time(df)
    category_breakdown(df)

    # Summary statistics
    spending_summary(df)

    print(f"\n{'='*70}")
    print("Stage 7 Complete!")
    print("Charts saved as PNG files in project root")
    print("="*70)
