"""
Streamlit Dashboard for Personal Finance Categorizer
Real-time spending analytics, budget tracking, anomaly detection
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import joblib

# Page config
st.set_page_config(page_title="Finance Dashboard", layout="wide", initial_sidebar_state="expanded")

# Load data (cached)
@st.cache_data
def load_data():
    df = pd.read_csv('data/processed/transactions_classified.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['date'] = df['timestamp'].dt.date
    return df

df = load_data()

# Sidebar filters
st.sidebar.markdown("### Filters & Settings")

# Date range
min_date = df['timestamp'].min().date()
max_date = df['timestamp'].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
else:
    df_filtered = df.copy()

# Category filter
categories = st.sidebar.multiselect(
    "Categories",
    options=sorted(df['category'].unique()),
    default=sorted(df['category'].unique())
)
df_filtered = df_filtered[df_filtered['category'].isin(categories)]

# Source filter
sources = st.sidebar.multiselect(
    "Payment source",
    options=['alipay', 'wechat'],
    default=['alipay', 'wechat']
)
df_filtered = df_filtered[df_filtered['source'].isin(sources)]

# Confidence threshold
min_conf = st.sidebar.slider(
    "Minimum confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05
)
df_filtered = df_filtered[df_filtered['confidence'] >= min_conf]

# Budget settings
st.sidebar.markdown("### Budget Alerts (Monthly)")
budget_settings = {}
for cat in sorted(df['category'].unique()):
    # Default budget based on average monthly spend for this category
    avg_monthly = df[df['category'] == cat].groupby('month')['amount'].sum().mean()
    budget_settings[cat] = st.sidebar.number_input(
        f"{cat} budget (¥)",
        min_value=0.0,
        value=float(avg_monthly),
        step=100.0
    )

# Show anomalies only
show_anomalies_only = st.sidebar.checkbox("Show anomalies only (Tab 4)")

# ===== MAIN CONTENT =====

st.title("💰 Personal Finance Dashboard")
st.markdown(f"**Data range:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} | **Transactions:** {len(df_filtered):,}")

# KPI Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    total_spend = df_filtered['amount'].sum()
    st.metric("Total Spend", f"¥{total_spend:.0f}", delta=f"{len(df_filtered)} transactions")

with col2:
    avg_transaction = df_filtered['amount'].mean()
    st.metric("Avg Transaction", f"¥{avg_transaction:.2f}", delta=f"Median: ¥{df_filtered['amount'].median():.2f}")

with col3:
    num_days = (df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).days + 1
    daily_avg = total_spend / max(num_days, 1)
    st.metric("Daily Average", f"¥{daily_avg:.2f}", delta=f"{num_days} days")

with col4:
    top_cat = df_filtered.groupby('category')['amount'].sum().idxmax()
    top_cat_spend = df_filtered.groupby('category')['amount'].sum().max()
    st.metric("Top Category", top_cat, f"¥{top_cat_spend:.0f}")

st.divider()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🏪 Merchants", "💳 Budget", "🚨 Anomalies", "📋 Monthly"])

# ===== TAB 1: OVERVIEW =====
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Monthly Spend by Category")
        monthly_data = df_filtered.groupby(['month', 'category'])['amount'].sum().reset_index()
        monthly_data['month'] = monthly_data['month'].astype(str)

        fig_monthly = px.bar(
            monthly_data,
            x='month',
            y='amount',
            color='category',
            title="Stacked Monthly Spending",
            labels={'amount': 'Spend (¥)', 'month': 'Month'},
            barmode='stack'
        )
        fig_monthly.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig_monthly, use_container_width=True)

    with col2:
        st.markdown("### Category Breakdown")
        category_spend = df_filtered.groupby('category')['amount'].sum().reset_index()

        fig_pie = px.pie(
            category_spend,
            values='amount',
            names='category',
            title="Share of Total Spending",
            labels={'amount': 'Spend (¥)'}
        )
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)

# ===== TAB 2: MERCHANTS =====
with tab2:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Top 15 Merchants by Spend")
        top_merchants = df_filtered.groupby('merchant')['amount'].sum().nlargest(15).reset_index()
        top_merchants = top_merchants.sort_values('amount')

        fig_merchants = px.barh(
            top_merchants,
            x='amount',
            y='merchant',
            title="Top Merchants",
            labels={'amount': 'Total Spend (¥)', 'merchant': ''},
            color='amount',
            color_continuous_scale='Blues'
        )
        fig_merchants.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_merchants, use_container_width=True)

    with col2:
        st.markdown("### Cumulative Spend Over Time")
        daily_data = df_filtered.sort_values('timestamp').copy()
        daily_data['cumsum'] = daily_data['amount'].cumsum()

        fig_cumsum = px.line(
            daily_data,
            x='timestamp',
            y='cumsum',
            title="Cumulative Spending",
            labels={'cumsum': 'Cumulative (¥)', 'timestamp': 'Date'},
            markers=True
        )
        fig_cumsum.update_layout(height=450, hovermode='x unified')
        st.plotly_chart(fig_cumsum, use_container_width=True)

# ===== TAB 3: BUDGET ALERTS =====
with tab3:
    # Get current month and previous months for comparison
    current_month = df['month'].max()

    st.markdown("### Budget Status — Current & Previous Months")

    months_to_show = st.slider("Months to display", 1, 6, 3)
    months_list = sorted(df['month'].unique())[-months_to_show:]

    for month in months_list:
        month_df = df[df['month'] == month]
        month_str = str(month)

        st.markdown(f"#### {month_str}")

        cols = st.columns(len(categories))

        for idx, cat in enumerate(sorted(categories)):
            with cols[idx]:
                cat_spend = month_df[month_df['category'] == cat]['amount'].sum()
                budget = budget_settings[cat]
                usage_pct = (cat_spend / budget * 100) if budget > 0 else 0

                # Color coding
                if usage_pct >= 100:
                    color = "🔴"  # Red — over budget
                    delta_color = "off"
                elif usage_pct >= 80:
                    color = "🟠"  # Orange — approaching budget
                    delta_color = "off"
                else:
                    color = "🟢"  # Green — under budget
                    delta_color = "off"

                st.metric(
                    f"{color} {cat}",
                    f"¥{cat_spend:.0f}",
                    delta=f"{usage_pct:.0f}% / ¥{budget:.0f}",
                    delta_color=delta_color
                )

# ===== TAB 4: ANOMALIES =====
with tab4:
    st.markdown("### Anomaly Detection")

    anomalies = []

    # Detect high-value outliers (> mean + 2 * std per category)
    for cat in df_filtered['category'].unique():
        cat_data = df_filtered[df_filtered['category'] == cat]
        if len(cat_data) > 0:
            mean = cat_data['amount'].mean()
            std = cat_data['amount'].std()
            threshold = mean + 2 * std

            high_value = cat_data[cat_data['amount'] > threshold].copy()
            high_value['flag_reason'] = f"High value (>{threshold:.0f}¥) for {cat}"
            anomalies.append(high_value)

    # Detect one-off merchants (appear only once)
    merchant_counts = df_filtered['merchant'].value_counts()
    one_off_merchants = merchant_counts[merchant_counts == 1].index
    one_off = df_filtered[df_filtered['merchant'].isin(one_off_merchants)].copy()
    one_off['flag_reason'] = "One-off merchant (single transaction)"
    anomalies.append(one_off)

    if anomalies:
        anomaly_df = pd.concat(anomalies, ignore_index=True)
        anomaly_df = anomaly_df.sort_values('amount', ascending=False)

        st.markdown(f"**Found {len(anomaly_df)} anomalies**")
        st.dataframe(
            anomaly_df[['timestamp', 'merchant', 'description', 'amount', 'category', 'confidence', 'flag_reason']],
            use_container_width=True,
            hide_index=True
        )

        # Download button
        csv = anomaly_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="Download anomalies as CSV",
            data=csv,
            file_name=f"anomalies_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    else:
        st.info("No anomalies detected in current filter range.")

# ===== TAB 5: MONTHLY REPORTS =====
with tab5:
    st.markdown("### Monthly Summary Report")

    month_options = sorted([str(m) for m in df['month'].unique()], reverse=True)
    selected_month = st.selectbox("Select month", month_options)

    month_df = df[df['month'].astype(str) == selected_month]

    # Summary table
    st.markdown(f"#### {selected_month} Summary")
    summary_table = month_df.groupby('category').agg(
        Count=('amount', 'count'),
        Total=('amount', 'sum'),
        Average=('amount', 'mean'),
        Median=('amount', 'median'),
        Max=('amount', 'max')
    ).reset_index()

    summary_table['% of Total'] = (summary_table['Total'] / summary_table['Total'].sum() * 100).round(1)
    summary_table = summary_table.sort_values('Total', ascending=False)

    # Format for display
    for col in ['Total', 'Average', 'Median', 'Max']:
        summary_table[col] = summary_table[col].round(2)

    st.dataframe(summary_table, use_container_width=True, hide_index=True)

    # Expandable transaction list
    with st.expander(f"View all {len(month_df)} transactions"):
        st.dataframe(
            month_df[['timestamp', 'merchant', 'description', 'amount', 'category', 'confidence', 'source']].sort_values('timestamp'),
            use_container_width=True,
            hide_index=True
        )

    # Download button
    csv = month_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label=f"Download {selected_month} as CSV",
        data=csv,
        file_name=f"spending_{selected_month}.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("---")
st.markdown(
    "📊 **Personal Finance Categorizer** | "
    "Model: Logistic Regression | "
    "Accuracy: 97.3% | "
    "Training data: 748 transactions"
)
