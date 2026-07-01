"""
Streamlit Dashboard — Personal Finance Categorizer
Real-time spending monitoring with budget tracking and action planning.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dashboard_helpers import (
    load_budget_config,
    calculate_ytd_vs_budget,
    get_status_badge,
    get_budget_type,
    apply_chart_theme,
    CHART_COLORS,
)
from forecast import (
    calculate_historical_patterns,
    project_spending,
    calculate_savings_projection,
)
from merchant_display import display_merchant, add_display_names, aggregate_merchants

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — clean dark theme, no sidebar, responsive KPI cards ──────────
st.markdown("""
<style>
    /* Hide sidebar entirely */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* Tighter top padding */
    .block-container { padding-top: 1.5rem; max-width: 1400px; }

    /* Header */
    .dash-header { margin-bottom: 0.25rem; }
    .dash-header h1 {
        font-size: 1.75rem; font-weight: 700; color: #e8eaed;
        margin: 0; letter-spacing: -0.02em;
    }
    .dash-subtitle { color: #8899a6; font-size: 0.85rem; margin-bottom: 1rem; }

    /* KPI cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    @media (max-width: 1100px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
    @media (max-width: 700px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

    .kpi-card {
        background: linear-gradient(145deg, #1a1d24 0%, #161920 100%);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 1rem 1.1rem;
    }
    .kpi-label {
        font-size: 0.72rem; text-transform: uppercase;
        letter-spacing: 0.06em; color: #8899a6; margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.45rem; font-weight: 700; color: #e8eaed;
        line-height: 1.2;
    }
    .kpi-delta { font-size: 0.78rem; margin-top: 0.3rem; }
    .delta-up   { color: #e74c3c; }
    .delta-down { color: #2ecc71; }
    .delta-neutral { color: #8899a6; }
    .accent-purple { color: #7c6af7; }
    .accent-cyan   { color: #4fc3f7; }
    .accent-green  { color: #2ecc71; }
    .accent-orange { color: #f39c12; }

    /* Section headers inside tabs */
    .section-title {
        font-size: 1.05rem; font-weight: 600; color: #e8eaed;
        margin: 1.5rem 0 0.75rem 0; padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    /* Filter bar */
    .filter-hint { color: #8899a6; font-size: 0.8rem; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1.25rem;
        font-weight: 500;
    }

    /* Footer */
    .dash-footer {
        text-align: center; color: #5a6570;
        font-size: 0.75rem; padding: 1.5rem 0 0.5rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 2rem;
    }

    /* Budget tab — 7 category cards in one row */
    .budget-toolbar {
        display: flex; align-items: center; justify-content: space-between;
        flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem;
    }
    .budget-summary-strip {
        display: flex; gap: 1.5rem; flex-wrap: wrap;
        background: rgba(124, 106, 247, 0.08);
        border: 1px solid rgba(124, 106, 247, 0.18);
        border-radius: 10px; padding: 0.65rem 1rem;
        font-size: 0.82rem; color: #c8cdd3;
    }
    .budget-summary-strip strong { color: #e8eaed; }

    .budget-row {
        display: grid;
        grid-template-columns: repeat(9, 1fr);
        gap: 0.55rem;
        margin-bottom: 0.5rem;
    }
    @media (max-width: 1400px) {
        .budget-row { grid-template-columns: repeat(5, 1fr); }
    }
    @media (max-width: 900px) {
        .budget-row { grid-template-columns: repeat(3, 1fr); }
    }

    .budget-cat-card {
        background: #1a1d24;
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 10px;
        padding: 0.7rem 0.65rem 0.75rem;
        min-width: 0;
        display: flex; flex-direction: column; gap: 0.3rem;
        transition: border-color 0.15s;
    }
    .budget-cat-card:hover { border-color: rgba(124, 106, 247, 0.35); }
    .budget-cat-card.status-ok   { border-top: 3px solid #2ecc71; }
    .budget-cat-card.status-warn { border-top: 3px solid #f39c12; }
    .budget-cat-card.status-over { border-top: 3px solid #e74c3c; }

    .bc-top {
        display: flex; align-items: flex-start; justify-content: space-between;
        gap: 0.25rem;
    }
    .bc-name {
        font-size: 0.72rem; font-weight: 600; color: #e8eaed;
        line-height: 1.25; word-break: break-word;
    }
    .bc-type {
        font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.04em;
        padding: 0.1rem 0.35rem; border-radius: 4px; flex-shrink: 0;
        font-weight: 600;
    }
    .bc-type.need { background: rgba(231, 76, 60, 0.15); color: #e74c3c; }
    .bc-type.want { background: rgba(124, 106, 247, 0.15); color: #7c6af7; }

    .bc-amount {
        font-size: 1.05rem; font-weight: 700; color: #e8eaed;
        line-height: 1.1; margin-top: 0.15rem;
    }
    .bc-budget { font-size: 0.68rem; color: #8899a6; }

    .bc-bar {
        height: 5px; background: rgba(255,255,255,0.08);
        border-radius: 3px; overflow: hidden; margin-top: 0.2rem;
    }
    .bc-fill {
        height: 100%; border-radius: 3px;
        transition: width 0.3s ease;
    }
    .bc-fill.ok   { background: linear-gradient(90deg, #27ae60, #2ecc71); }
    .bc-fill.warn { background: linear-gradient(90deg, #e67e22, #f39c12); }
    .bc-fill.over { background: linear-gradient(90deg, #c0392b, #e74c3c); }

    .bc-footer {
        display: flex; justify-content: space-between; align-items: center;
        font-size: 0.65rem; color: #8899a6; margin-top: 0.1rem;
    }
    .bc-status { font-weight: 600; }
    .bc-status.ok   { color: #2ecc71; }
    .bc-status.warn { color: #f39c12; }
    .bc-status.over { color: #e74c3c; }
    .bc-remaining { color: #8899a6; }
</style>
""", unsafe_allow_html=True)

# Fixed display order: essentials first, then discretionary
BUDGET_CATEGORIES = [
    'Groceries', 'Transportation', 'Utilities & Services',
    'Eating Out', 'Shopping', 'Transfers & Gifts', 'Other',
    'Saving', 'Investing',
]

CATEGORY_SHORT = {
    'Groceries': 'Groceries',
    'Transportation': 'Transit',
    'Utilities & Services': 'Utilities',
    'Eating Out': 'Eating Out',
    'Shopping': 'Shopping',
    'Transfers & Gifts': 'Transfers',
    'Other': 'Other',
    'Saving': 'Saving',
    'Investing': 'Investing',
}


def get_monthly_budget_amount(budget_config, category, df_fallback):
    """Monthly budget for a category; fall back to historical average."""
    budget_amt = budget_config['categories'].get(category, {}).get('monthly_budget', 0)
    if budget_amt and budget_amt > 0:
        return float(budget_amt)
    hist = df_fallback[df_fallback['category'] == category].groupby('month')['amount'].sum()
    return float(hist.mean()) if len(hist) > 0 else 0.0


def budget_status_class(pct, cat_type):
    """Return (card_class, fill_class, status_class, status_text)."""
    _, _, status_text = get_status_badge(pct, cat_type)
    if pct >= 100:
        return 'status-over', 'over', 'over', status_text
    if pct >= 80:
        return 'status-warn', 'warn', 'warn', status_text
    return 'status-ok', 'ok', 'ok', status_text


def build_budget_category_row(month_df, budget_config, df_all):
    """Build HTML for category budget cards in one row."""
    cards = []
    on_track = 0
    total_actual = 0.0
    total_budget = 0.0

    for cat in BUDGET_CATEGORIES:
        actual = float(month_df[month_df['category'] == cat]['amount'].sum())
        budget_amt = get_monthly_budget_amount(budget_config, cat, df_all)

        if budget_amt <= 0:
            pct = 0
            card_cls, fill_cls, stat_cls = 'status-ok', 'ok', 'ok'
            status_text = 'Not started'
            remain_text = 'Starts next semester'
            bar_pct = 0
            on_track += 1
        else:
            pct = (actual / budget_amt * 100)
            cat_type = get_budget_type(budget_config, cat) or 'Want'
            card_cls, fill_cls, stat_cls, status_text = budget_status_class(pct, cat_type)
            if pct < 100:
                on_track += 1
            bar_pct = min(pct, 100)
            remaining = budget_amt - actual
            remain_text = (
                f"¥{remaining:,.0f} left" if remaining >= 0
                else f"¥{abs(remaining):,.0f} over"
            )

        total_actual += actual
        total_budget += budget_amt

        cat_type = get_budget_type(budget_config, cat) or 'Need'
        short = CATEGORY_SHORT.get(cat, cat)
        type_cls = 'need' if cat_type == 'Need' else 'want'

        cards.append(f"""
        <div class="budget-cat-card {card_cls}">
            <div class="bc-top">
                <span class="bc-name">{short}</span>
                <span class="bc-type {type_cls}">{cat_type}</span>
            </div>
            <div class="bc-amount">¥{actual:,.0f}</div>
            <div class="bc-budget">of ¥{budget_amt:,.0f}</div>
            <div class="bc-bar"><div class="bc-fill {fill_cls}" style="width:{bar_pct:.0f}%"></div></div>
            <div class="bc-footer">
                <span class="bc-status {stat_cls}">{pct:.0f}% · {status_text}</span>
                <span class="bc-remaining">{remain_text}</span>
            </div>
        </div>""")

    summary = {
        'total_actual': total_actual,
        'total_budget': total_budget,
        'on_track': on_track,
        'total_cats': len(BUDGET_CATEGORIES),
        'overall_pct': (total_actual / total_budget * 100) if total_budget > 0 else 0,
    }
    return '<div class="budget-row">' + ''.join(cards) + '</div>', summary


# ── Data loading ─────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / 'data' / 'processed' / 'transactions_classified.csv'


@st.cache_data
def load_data(file_mtime: float):
    """Load classified transactions; cache invalidates when CSV is updated."""
    df = pd.read_csv(DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['date'] = df['timestamp'].dt.date
    df = normalize_categories(df)
    return df


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Fix known category patterns at load time (e.g. catering companies → Eating Out)."""
    df = df.copy()
    catering_mask = df['merchant'].str.contains('catering|餐饮', case=False, na=False)
    df.loc[catering_mask, 'category'] = 'Eating Out'
    return df


def render_filters(df):
    """Inline filter bar (replaces sidebar). Returns filtered DataFrame + meta."""
    with st.expander("🔍 Filters", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 2, 1.5, 1.5])
        min_date = df['timestamp'].min().date()
        max_date = df['timestamp'].max().date()

        with c1:
            date_range = st.date_input(
                "Date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )
        with c2:
            categories = st.multiselect(
                "Categories",
                options=sorted(df['category'].unique()),
                default=sorted(df['category'].unique()),
            )
        with c3:
            source_options = sorted(df['source'].unique())
            sources = st.multiselect(
                "Payment source",
                options=source_options,
                default=source_options,
                key=f"source_filter_{len(df)}",
            )
        with c4:
            min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05)

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    filtered = df[
        (df['date'] >= start_date) &
        (df['date'] <= end_date) &
        (df['category'].isin(categories)) &
        (df['source'].isin(sources)) &
        (df['confidence'] >= min_conf)
    ].copy()

    return filtered, start_date, end_date


def kpi_card(label, value, delta_text, delta_class="delta-neutral"):
    return (
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-delta {delta_class}">{delta_text}</div>'
        f'</div>'
    )


def compute_kpis(df_filtered, df_all, budget_config):
    """Build the five headline metrics."""
    total = df_filtered['amount'].sum()
    days = (df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).days + 1

    # Trend: compare to prior period of equal length
    span = df_filtered['timestamp'].max() - df_filtered['timestamp'].min()
    prior_end = df_filtered['timestamp'].min() - timedelta(days=1)
    prior_start = prior_end - span
    prior = df_all[
        (df_all['timestamp'] >= prior_start) & (df_all['timestamp'] <= prior_end)
    ]
    prior_total = prior['amount'].sum() if len(prior) > 0 else 0
    if prior_total > 0:
        pct_change = (total - prior_total) / prior_total * 100
        trend_text = f"{'↑' if pct_change > 0 else '↓'} {abs(pct_change):.1f}% vs prior period"
        trend_class = "delta-up" if pct_change > 0 else "delta-down"
    else:
        trend_text = f"{len(df_filtered):,} transactions"
        trend_class = "delta-neutral"

    # Budget status (YTD)
    if budget_config:
        ytd = calculate_ytd_vs_budget(df_filtered, budget_config)
        total_budget = ytd['budget'].sum()
        total_actual = ytd['ytd_actual'].sum()
        pct_budget = (total_actual / total_budget * 100) if total_budget > 0 else 0
        over = total_actual > total_budget
        budget_value = f"¥{total_actual:,.0f}"
        budget_delta = f"{'Over' if over else 'Under'} by ¥{abs(total_actual - total_budget):,.0f} ({pct_budget:.0f}%)"
        budget_class = "delta-up" if over else "delta-down"
    else:
        budget_value = "—"
        budget_delta = "No budget config"
        budget_class = "delta-neutral"

    # Current month vs forecast
    if budget_config and len(df_filtered) > 0:
        patterns = calculate_historical_patterns(df_filtered)
        forecast_df = project_spending(df_filtered, patterns, budget_config, forecast_months=9)
        current_month_str = df_filtered['month'].max()
        month_idx = list(df_filtered['month'].unique()).index(current_month_str)
        # Use latest month actual
        month_actual = df_filtered[df_filtered['month'] == current_month_str]['amount'].sum()
        # Forecast total for next projected month (first month in forecast)
        if len(forecast_df) > 0:
            first_fc_month = forecast_df['month'].iloc[0]
            month_forecast = forecast_df[forecast_df['month'] == first_fc_month]['projected_spend'].sum()
            fc_delta = month_actual - month_forecast
            fc_text = f"Actual ¥{month_actual:,.0f} vs forecast ¥{month_forecast:,.0f}"
            fc_class = "delta-up" if fc_delta > 0 else "delta-down"
            fc_value = str(current_month_str)
        else:
            fc_value = str(current_month_str)
            fc_text = f"¥{month_actual:,.0f} this month"
            fc_class = "delta-neutral"
    else:
        fc_value = "—"
        fc_text = "No forecast data"
        fc_class = "delta-neutral"

    # Largest category
    cat_spend = df_filtered.groupby('category')['amount'].sum()
    if len(cat_spend) > 0:
        top_cat = cat_spend.idxmax()
        top_amt = cat_spend.max()
        top_pct = top_amt / total * 100 if total > 0 else 0
        top_value = top_cat
        top_delta = f"¥{top_amt:,.0f} ({top_pct:.0f}% of total)"
        top_class = "delta-neutral"
    else:
        top_value = "—"
        top_delta = "No data"
        top_class = "delta-neutral"

    # Savings potential
    if budget_config:
        savings = calculate_savings_projection(df_filtered, budget_config)
        want_cats = [c for c, i in budget_config['categories'].items() if i['type'] == 'Want']
        want_df = df_filtered[df_filtered['category'].isin(want_cats)]
        months = max(len(df_filtered['month'].unique()), 1)
        want_monthly = want_df['amount'].sum() / months
        # Top-10 cuttable heuristic: 30% of discretionary
        potential = want_monthly * 0.30
        sav_value = f"¥{potential:,.0f}/mo"
        gap = max(0, budget_config['saving_goal_monthly'] - savings['ytd_savings'] / max(savings['months_passed'], 1))
        sav_delta = f"~30% discretionary cut · gap ¥{gap:.0f}/mo to goal"
        sav_class = "delta-down"
    else:
        sav_value = "—"
        sav_delta = "Load budget config"
        sav_class = "delta-neutral"

    return [
        ("Total Spend", f"¥{total:,.0f}", trend_text, trend_class),
        ("Budget Status", budget_value, budget_delta, budget_class),
        ("Monthly vs Forecast", fc_value, fc_text, fc_class),
        ("Largest Category", top_value, top_delta, top_class),
        ("Savings Potential", sav_value, sav_delta, sav_class),
    ]


def detect_anomalies(df_filtered):
    """Flag high-value, one-off, and low-confidence transactions."""
    anomalies = []
    valid = df_filtered[~df_filtered['category'].isin(['???'])].copy()

    for cat in valid['category'].unique():
        cat_data = valid[valid['category'] == cat]
        if len(cat_data) == 0:
            continue
        Q1, Q3 = cat_data['amount'].quantile(0.25), cat_data['amount'].quantile(0.75)
        threshold = max(Q3 + 1.5 * (Q3 - Q1), 150)
        high_value = cat_data[cat_data['amount'] > threshold].copy()
        high_value['flag_reason'] = f"High value (>{threshold:.0f}¥)"
        anomalies.append(high_value)

    merchant_counts = valid['merchant'].value_counts()
    one_off_merchants = merchant_counts[merchant_counts == 1].index
    one_off_all = valid[valid['merchant'].isin(one_off_merchants)].copy()
    if len(one_off_all) > 0:
        chunks = []
        for cat in one_off_all['category'].unique():
            cat_p90 = valid[valid['category'] == cat]['amount'].quantile(0.90)
            chunk = one_off_all[(one_off_all['category'] == cat) & (one_off_all['amount'] > cat_p90)]
            if len(chunk) > 0:
                chunks.append(chunk)
        if chunks:
            one_off = pd.concat(chunks, ignore_index=True)
            one_off['flag_reason'] = "One-off merchant, high spend"
            anomalies.append(one_off)

    low_conf = valid[
        (valid['confidence'] < 0.50) & (valid['category'] != 'Other')
    ].copy()
    if len(low_conf) > 0:
        low_conf['flag_reason'] = "Low confidence (<50%)"
        anomalies.append(low_conf)

    if not anomalies:
        return pd.DataFrame()
    result = pd.concat(anomalies, ignore_index=True)
    return result.drop_duplicates(subset=['timestamp', 'merchant', 'amount'], keep='first')


# ── Load data ────────────────────────────────────────────────────────────────
df = load_data(DATA_PATH.stat().st_mtime)
budget_config = load_budget_config('data/budget_config.json')

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="dash-header"><h1>Personal Finance Dashboard</h1></div>',
    unsafe_allow_html=True,
)

df_filtered, start_date, end_date = render_filters(df)

st.markdown(
    f'<div class="dash-subtitle">'
    f'{start_date.strftime("%b %d, %Y")} — {end_date.strftime("%b %d, %Y")} · '
    f'{len(df_filtered):,} transactions</div>',
    unsafe_allow_html=True,
)

# ── KPI row ──────────────────────────────────────────────────────────────────
kpis = compute_kpis(df_filtered, df, budget_config)
kpi_html = '<div class="kpi-grid">' + ''.join(
    kpi_card(l, v, d, c) for l, v, d, c in kpis
) + '</div>'
st.markdown(kpi_html, unsafe_allow_html=True)

# ── Main tabs (3 priority tabs) ──────────────────────────────────────────────
tab_overview, tab_budget, tab_action = st.tabs([
    "📊 Spending Overview",
    "💳 Budget Tracking",
    "🎯 Action Plan",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SPENDING OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    # Row 1: trend line + donut
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown('<div class="section-title">Monthly Spending Trend</div>', unsafe_allow_html=True)
        monthly = df_filtered.groupby('month')['amount'].sum().reset_index()
        monthly['month'] = monthly['month'].astype(str)
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=monthly['month'], y=monthly['amount'],
            mode='lines+markers',
            fill='tozeroy',
            fillcolor='rgba(124, 106, 247, 0.15)',
            line=dict(color='#7c6af7', width=2.5),
            marker=dict(size=8),
            name='Spend',
        ))
        fig_trend.update_layout(
            xaxis_title='', yaxis_title='¥',
            hovermode='x unified',
        )
        apply_chart_theme(fig_trend, height=340)
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-title">Category Breakdown</div>', unsafe_allow_html=True)
        cat_spend = df_filtered.groupby('category')['amount'].sum().reset_index()
        fig_donut = px.pie(
            cat_spend, values='amount', names='category',
            hole=0.55, color_discrete_sequence=CHART_COLORS,
        )
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        apply_chart_theme(fig_donut, height=340)
        st.plotly_chart(fig_donut, use_container_width=True)

    # Row 2: stacked bar by category + cumulative line
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="section-title">Spend by Category (Monthly)</div>', unsafe_allow_html=True)
        monthly_cat = df_filtered.groupby(['month', 'category'])['amount'].sum().reset_index()
        monthly_cat['month'] = monthly_cat['month'].astype(str)
        fig_stack = px.bar(
            monthly_cat, x='month', y='amount', color='category',
            barmode='stack', color_discrete_sequence=CHART_COLORS,
        )
        apply_chart_theme(fig_stack, height=360)
        st.plotly_chart(fig_stack, use_container_width=True)

    with col_d:
        st.markdown('<div class="section-title">Cumulative Spend</div>', unsafe_allow_html=True)
        daily = df_filtered.sort_values('timestamp').copy()
        daily['cumsum'] = daily['amount'].cumsum()
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=daily['timestamp'], y=daily['cumsum'],
            mode='lines', line=dict(color='#4fc3f7', width=2),
            fill='tozeroy', fillcolor='rgba(79, 195, 247, 0.1)',
        ))
        apply_chart_theme(fig_cum, height=360)
        st.plotly_chart(fig_cum, use_container_width=True)

    # Row 3: top merchants horizontal bar
    st.markdown('<div class="section-title">Top Merchants</div>', unsafe_allow_html=True)
    top_m = aggregate_merchants(df_filtered, n=12).sort_values('amount')
    fig_merch = px.bar(
        top_m, x='amount', y='merchant_display', orientation='h',
        color='amount', color_continuous_scale=[[0, '#1a1d24'], [1, '#7c6af7']],
    )
    fig_merch.update_layout(coloraxis_showscale=False, yaxis_title='')
    apply_chart_theme(fig_merch, height=380)
    st.plotly_chart(fig_merch, use_container_width=True)

    # Monthly detail table
    with st.expander("📋 Monthly detail report"):
        month_options = sorted([str(m) for m in df['month'].unique()], reverse=True)
        selected_month = st.selectbox("Select month", month_options, key="overview_month")
        month_df = df[df['month'].astype(str) == selected_month]
        summary = month_df.groupby('category').agg(
            Count=('amount', 'count'), Total=('amount', 'sum'),
            Average=('amount', 'mean'), Max=('amount', 'max'),
        ).reset_index().sort_values('Total', ascending=False)
        summary['% of Total'] = (summary['Total'] / summary['Total'].sum() * 100).round(1)
        st.dataframe(summary, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — BUDGET TRACKING
# ══════════════════════════════════════════════════════════════════════════════
with tab_budget:
    if not budget_config:
        st.warning("Budget config not found. Run `python src/budget_loader.py` first.")
    else:
        ytd_df = calculate_ytd_vs_budget(df_filtered, budget_config)

        # ── Category budget row (7 cards, one row) ───────────────────────────
        st.markdown('<div class="section-title">Monthly Budget</div>', unsafe_allow_html=True)

        month_options = sorted(df['month'].unique())
        selected_budget_month = st.selectbox(
            "Month",
            month_options,
            index=len(month_options) - 1,
            format_func=lambda m: str(m),
            key="budget_month_pick",
        )

        month_df = df[df['month'] == selected_budget_month]
        row_html, summary = build_budget_category_row(month_df, budget_config, df)
        st.markdown(
            f'<div class="budget-summary-strip">'
            f'<span><strong>¥{summary["total_actual"]:,.0f}</strong> spent'
            f' &nbsp;·&nbsp; <strong>¥{summary["total_budget"]:,.0f}</strong> budget'
            f' &nbsp;·&nbsp; <strong>{summary["overall_pct"]:.0f}%</strong> used</span>'
            f'<span><strong>{summary["on_track"]}/{summary["total_cats"]}</strong> categories on track</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(row_html, unsafe_allow_html=True)

        # YTD progress bars
        st.markdown('<div class="section-title">Year-to-Date vs Annual Budget</div>', unsafe_allow_html=True)
        ytd_sorted = ytd_df.sort_values('pct_of_budget', ascending=True)
        fig_bars = go.Figure()
        colors = []
        for _, row in ytd_sorted.iterrows():
            _, color, _ = get_status_badge(row['pct_of_budget'], row['type'])
            colors.append(color)
        fig_bars.add_trace(go.Bar(
            y=ytd_sorted['category'], x=ytd_sorted['pct_of_budget'],
            orientation='h', marker_color=colors,
            text=[f"{p:.0f}%" for p in ytd_sorted['pct_of_budget']],
            textposition='outside',
        ))
        fig_bars.add_vline(x=100, line_dash='dash', line_color='#8899a6', annotation_text='100%')
        fig_bars.update_layout(xaxis_title='% of Annual Budget', yaxis_title='')
        apply_chart_theme(fig_bars, height=max(300, len(ytd_sorted) * 32))
        st.plotly_chart(fig_bars, use_container_width=True)

        # Forecast section
        st.markdown('<div class="section-title">Spending Forecast</div>', unsafe_allow_html=True)
        patterns = calculate_historical_patterns(df_filtered)
        forecast_df = project_spending(df_filtered, patterns, budget_config, forecast_months=9)

        fc_col1, fc_col2 = st.columns([2, 1])
        with fc_col1:
            heatmap_data = forecast_df.pivot_table(
                values='pct_of_budget', index='category', columns='month', aggfunc='mean',
            )
            fig_heat = go.Figure(data=go.Heatmap(
                z=heatmap_data.values,
                x=heatmap_data.columns, y=heatmap_data.index,
                colorscale=[[0, '#2ecc71'], [0.5, '#f39c12'], [1, '#e74c3c']],
                zmid=100, text=np.round(heatmap_data.values, 0),
                texttemplate='%{text}%', textfont=dict(size=10),
                colorbar=dict(title='% Budget'),
            ))
            apply_chart_theme(fig_heat, height=400)
            st.plotly_chart(fig_heat, use_container_width=True)

        with fc_col2:
            months_fc = forecast_df['month'].unique()
            selected_fc = st.selectbox("Forecast month", months_fc, key="fc_month")
            month_fc = forecast_df[forecast_df['month'] == selected_fc]
            risk_counts = month_fc['risk'].value_counts()
            fig_risk = px.pie(
                values=risk_counts.values, names=risk_counts.index,
                color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c'],
                hole=0.4,
            )
            apply_chart_theme(fig_risk, height=300)
            st.plotly_chart(fig_risk, use_container_width=True)

        # Savings tracker
        st.markdown('<div class="section-title">Savings Progress</div>', unsafe_allow_html=True)
        savings = calculate_savings_projection(df_filtered, budget_config)
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Monthly Income", f"¥{budget_config['income']:,.0f}")
        s2.metric("YTD Savings", f"¥{savings['ytd_savings']:,.0f}",
                  f"{savings['ytd_savings_pct']:.1f}% of income")
        s3.metric("Monthly Goal", f"¥{budget_config['saving_goal_monthly']:,.0f}")
        status = "On track" if savings['on_track'] else "At risk"
        s4.metric("Year-End Projection", f"¥{savings['projected_year_end_savings']:,.0f}", status)

        goal = budget_config['saving_goal_annual']
        projected = savings['projected_year_end_savings']
        fig_prog = go.Figure()
        fig_prog.add_trace(go.Bar(
            y=['Goal'], x=[goal], orientation='h',
            marker=dict(color='rgba(255,255,255,0.08)'), showlegend=False,
        ))
        fig_prog.add_trace(go.Bar(
            y=['Projected'], x=[projected], orientation='h',
            marker=dict(color='#2ecc71' if savings['on_track'] else '#f39c12'),
            text=f"¥{projected:,.0f}", textposition='auto', showlegend=False,
        ))
        apply_chart_theme(fig_prog, height=120)
        st.plotly_chart(fig_prog, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ACTION PLAN
# ══════════════════════════════════════════════════════════════════════════════
with tab_action:
    if not budget_config:
        st.warning("Budget config required for action planning.")
    else:
        want_categories = [
            c for c, info in budget_config['categories'].items() if info['type'] == 'Want'
        ]
        df_monthly = df_filtered.copy()

        # Need vs Want efficiency
        st.markdown('<div class="section-title">Need vs Want Breakdown</div>', unsafe_allow_html=True)
        efficiency_data = []
        for month in sorted(df_monthly['month'].unique()):
            mdf = df_monthly[df_monthly['month'] == month]
            total_s = mdf['amount'].sum()
            want_s = mdf[mdf['category'].isin(want_categories)]['amount'].sum()
            need_s = total_s - want_s
            monthly_savings = budget_config['income'] - total_s
            savings_gap = max(0, budget_config['saving_goal_monthly'] - monthly_savings)
            efficiency_data.append({
                'month': str(month), 'need_spend': need_s, 'want_spend': want_s,
                'savings_gap': savings_gap,
            })
        eff_df = pd.DataFrame(efficiency_data)

        fig_eff = go.Figure()
        fig_eff.add_trace(go.Bar(x=eff_df['month'], y=eff_df['need_spend'],
                                  name='Need', marker_color='#e74c3c'))
        fig_eff.add_trace(go.Bar(x=eff_df['month'], y=eff_df['want_spend'],
                                  name='Want', marker_color='#7c6af7'))
        fig_eff.add_trace(go.Bar(x=eff_df['month'], y=eff_df['savings_gap'],
                                  name='Savings gap', marker_color='#f39c12', opacity=0.5))
        fig_eff.update_layout(barmode='stack', hovermode='x unified')
        apply_chart_theme(fig_eff, height=360)
        st.plotly_chart(fig_eff, use_container_width=True)

        # Cuttable merchants
        st.markdown('<div class="section-title">Top Cuttable Merchants</div>', unsafe_allow_html=True)
        want_df = df_filtered[df_filtered['category'].isin(want_categories)]
        if len(want_df) > 0:
            months_in_data = max((df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).days / 30, 1)
            impacts = []
            for merchant in want_df['merchant'].unique():
                mtx = want_df[want_df['merchant'] == merchant]
                total_s = mtx['amount'].sum()
                impacts.append({
                    'merchant': merchant,
                    'monthly_impact': total_s / months_in_data,
                    'visits': len(mtx),
                    'total': total_s,
                })
            cut_df = pd.DataFrame(impacts).sort_values('monthly_impact', ascending=False)
            cut_df = add_display_names(cut_df)
            cut_df = (
                cut_df.groupby('merchant_display', as_index=False)
                .agg(monthly_impact=('monthly_impact', 'sum'), visits=('visits', 'sum'))
                .nlargest(10, 'monthly_impact')
            )
            fig_cut = px.bar(
                cut_df.sort_values('monthly_impact'),
                x='monthly_impact', y='merchant_display', orientation='h',
                color='monthly_impact',
                color_continuous_scale=[[0, '#1a1d24'], [1, '#f39c12']],
            )
            fig_cut.update_layout(coloraxis_showscale=False, yaxis_title='', xaxis_title='¥/month')
            apply_chart_theme(fig_cut, height=360)
            st.plotly_chart(fig_cut, use_container_width=True)
            total_cut = cut_df['monthly_impact'].sum()
            st.caption(f"Top 10 combined: **¥{total_cut:,.0f}/month** (¥{total_cut * 12:,.0f}/year)")

        # Anomalies (collapsed)
        with st.expander(f"🚨 Anomalies ({len(detect_anomalies(df_filtered))} flagged)"):
            anomaly_df = detect_anomalies(df_filtered)
            if len(anomaly_df) > 0:
                anomaly_show = add_display_names(anomaly_df)[
                    ['timestamp', 'merchant_display', 'amount', 'category', 'confidence', 'flag_reason']
                ].rename(columns={'merchant_display': 'Merchant'})
                st.dataframe(
                    anomaly_show.sort_values('amount', ascending=False),
                    use_container_width=True, hide_index=True,
                )
            else:
                st.info("No anomalies in current filter range.")

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="dash-footer">'
    'Personal Finance Categorizer · Logistic Regression · 97.3% accuracy'
    '</div>',
    unsafe_allow_html=True,
)
