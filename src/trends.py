"""
Multi-year spending trend analysis.

Works with any date range; year-over-year comparisons activate once
two or more calendar years have transaction data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out['timestamp'] = pd.to_datetime(out['timestamp'])
    out['year'] = out['timestamp'].dt.year
    out['month_num'] = out['timestamp'].dt.month
    out['month_label'] = out['timestamp'].dt.strftime('%b')
    return out


def calendar_years_in_data(df: pd.DataFrame) -> List[int]:
    """Sorted list of calendar years present in the data."""
    prepared = _prepare(df)
    return sorted(prepared['year'].unique().tolist())


def multi_year_ready(df: pd.DataFrame) -> bool:
    """True when at least two calendar years have spending data."""
    return len(calendar_years_in_data(df)) >= 2


def yearly_totals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Total spend and transaction count per calendar year.

    Returns columns: year, total_spend, txn_count, avg_per_month
    """
    prepared = _prepare(df)
    yearly = prepared.groupby('year').agg(
        total_spend=('amount', 'sum'),
        txn_count=('amount', 'count'),
    ).reset_index()
    months_per_year = prepared.groupby('year')['month_num'].nunique()
    yearly['months_covered'] = yearly['year'].map(months_per_year)
    yearly['avg_per_month'] = yearly['total_spend'] / yearly['months_covered'].clip(lower=1)
    return yearly


def yearly_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Spend by calendar year and category (for stacked bar charts)."""
    prepared = _prepare(df)
    return (
        prepared.groupby(['year', 'category'])['amount']
        .sum()
        .reset_index()
    )


def month_of_year_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Seasonal profile: average spend per calendar month (Jan–Dec).

    Pools all years — useful even with a single year of data.
    """
    prepared = _prepare(df)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    by_ym = prepared.groupby(['year', 'month_num'])['amount'].sum().reset_index()
    profile = by_ym.groupby('month_num')['amount'].agg(['mean', 'std', 'count']).reset_index()
    profile['month_label'] = profile['month_num'].map(
        {i + 1: name for i, name in enumerate(month_names)}
    )
    profile['std'] = profile['std'].fillna(0)
    return profile.sort_values('month_num')


def year_over_year_same_month(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Compare the same calendar month across years (e.g. all Septembers).

    Returns None if fewer than two calendar years are present.
    Columns: month_num, month_label, year, amount
    """
    if not multi_year_ready(df):
        return None

    prepared = _prepare(df)
    monthly = (
        prepared.groupby(['year', 'month_num', 'month_label'])['amount']
        .sum()
        .reset_index()
    )
    return monthly.sort_values(['month_num', 'year'])


def year_over_year_growth(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Year-on-year % change in total annual spend.

    Returns None if fewer than two full-ish years exist.
    """
    yearly = yearly_totals(df)
    if len(yearly) < 2:
        return None

    yearly = yearly.sort_values('year')
    yearly['prev_year_spend'] = yearly['total_spend'].shift(1)
    yearly['yoy_pct'] = (
        (yearly['total_spend'] - yearly['prev_year_spend'])
        / yearly['prev_year_spend'] * 100
    )
    return yearly.dropna(subset=['yoy_pct'])


def trend_summary(df: pd.DataFrame) -> Dict:
    """Human-readable summary for dashboard captions."""
    years = calendar_years_in_data(df)
    yearly = yearly_totals(df)
    growth = year_over_year_growth(df)

    summary = {
        'years': years,
        'n_years': len(years),
        'multi_year_ready': len(years) >= 2,
        'date_range': (
            pd.to_datetime(df['timestamp']).min().strftime('%Y-%m-%d'),
            pd.to_datetime(df['timestamp']).max().strftime('%Y-%m-%d'),
        ),
    }

    if len(yearly) > 0:
        summary['latest_year'] = int(yearly.iloc[-1]['year'])
        summary['latest_year_spend'] = float(yearly.iloc[-1]['total_spend'])

    if growth is not None and len(growth) > 0:
        last = growth.iloc[-1]
        summary['latest_yoy_pct'] = float(last['yoy_pct'])

    return summary
