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
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from dashboard_helpers import load_budget_config, get_budget_for_category, get_budget_type, calculate_ytd_vs_budget, get_status_badge, get_type_color
from forecast import calculate_historical_patterns, project_spending, calculate_savings_projection

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
# Load budget config
budget_config = load_budget_config('data/budget_config.json')

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 Overview", "🏪 Merchants", "💳 Budget", "🚨 Anomalies", "📋 Monthly", "🔮 Forecast", "💰 Savings", "🎯 Action Plan"])

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

        fig_merchants = px.bar(
            top_merchants,
            x='amount',
            y='merchant',
            orientation='h',
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
    st.markdown("Transactions flagged by three criteria: unusually high value, one-off merchant with high amount, or low model confidence.")

    anomalies = []

    # Detect high-value outliers using IQR method (Tukey's fences)
    # More robust for right-skewed distributions than mean+2*std
    for cat in df_filtered['category'].unique():
        cat_data = df_filtered[df_filtered['category'] == cat]
        if len(cat_data) > 0:
            Q1 = cat_data['amount'].quantile(0.25)
            Q3 = cat_data['amount'].quantile(0.75)
            IQR = Q3 - Q1
            threshold = Q3 + 1.5 * IQR
            # Absolute floor: don't flag as anomaly unless truly large
            threshold = max(threshold, 150)

            high_value = cat_data[cat_data['amount'] > threshold].copy()
            high_value['flag_reason'] = f"High value (>{threshold:.0f}¥) for {cat}"
            anomalies.append(high_value)

    # Detect one-off merchants ONLY if amount exceeds 90th percentile of their category
    # This targets genuinely unusual single purchases (e.g., ¥500 restaurant vs normal ¥30 meal)
    merchant_counts = df_filtered['merchant'].value_counts()
    one_off_merchants = merchant_counts[merchant_counts == 1].index
    one_off_all = df_filtered[df_filtered['merchant'].isin(one_off_merchants)].copy()

    if len(one_off_all) > 0:
        # Filter to only those above their category's 90th percentile
        one_off = []
        for cat in one_off_all['category'].unique():
            cat_p90 = df_filtered[df_filtered['category'] == cat]['amount'].quantile(0.90)
            cat_one_off = one_off_all[(one_off_all['category'] == cat) & (one_off_all['amount'] > cat_p90)]
            if len(cat_one_off) > 0:
                one_off.append(cat_one_off)

        if one_off:
            one_off = pd.concat(one_off, ignore_index=True)
            one_off['flag_reason'] = "One-off merchant with very high spending"
            anomalies.append(one_off)

    # Detect low-confidence predictions (model wasn't sure)
    # Exclude "Other" category which naturally has low confidence (66.9% mean)
    low_conf = df_filtered[
        (df_filtered['confidence'] < 0.50) &
        (df_filtered['category'] != 'Other')
    ].copy()
    if len(low_conf) > 0:
        low_conf['flag_reason'] = "Low confidence prediction (<50%)"
        anomalies.append(low_conf)

    if anomalies:
        anomaly_df = pd.concat(anomalies, ignore_index=True)
        # Remove duplicates (same transaction flagged by multiple rules)
        anomaly_df = anomaly_df.drop_duplicates(subset=['timestamp', 'merchant', 'amount'], keep='first')
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

# ===== TAB 6: FORECASTING =====
with tab6:
    st.markdown("### Spending Forecast (Sep 2026 - May 2027)")
    st.markdown("Based on your historical spending patterns and current trends")

    if budget_config:
        # Calculate forecast
        patterns = calculate_historical_patterns(df_filtered)
        forecast_df = project_spending(df_filtered, patterns, budget_config, forecast_months=9)

        # Month selector
        months = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']
        selected_month_forecast = st.selectbox("Select month", months, key="forecast_month")

        month_forecast = forecast_df[forecast_df['month'] == selected_month_forecast].copy()

        col1, col2 = st.columns([1.5, 1])

        with col1:
            # Forecast table
            display_cols = ['category', 'type', 'projected_spend', 'budget', 'variance', 'pct_of_budget', 'risk']
            month_forecast_display = month_forecast[display_cols].copy()
            month_forecast_display.columns = ['Category', 'Type', 'Projected', 'Budget', 'Variance', '% of Budget', 'Risk']

            # Format numbers
            for col in ['Projected', 'Budget', 'Variance']:
                month_forecast_display[col] = month_forecast_display[col].apply(lambda x: f"¥{x:.0f}")
            month_forecast_display['% of Budget'] = month_forecast_display['% of Budget'].apply(lambda x: f"{x:.0f}%")

            st.dataframe(month_forecast_display, use_container_width=True, hide_index=True)

        with col2:
            # Risk summary
            st.markdown("**Risk Distribution**")
            risk_counts = month_forecast['risk'].value_counts()
            fig_risk = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                color_discrete_sequence=['#00CC96', '#FFA15A', '#EF553B'],
                title="Risk Levels"
            )
            fig_risk.update_layout(height=300, showlegend=True)
            st.plotly_chart(fig_risk, use_container_width=True)

        # Full year projection heatmap
        st.markdown("### Full Year Projection (Sep-May)")
        heatmap_data = forecast_df.pivot_table(
            values='pct_of_budget',
            index='category',
            columns='month',
            aggfunc='mean'
        )

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn_r',
            zmid=100,
            text=np.round(heatmap_data.values, 0),
            texttemplate='%{text:.0f}%',
            textfont={"size": 10},
            colorbar=dict(title="% of Budget")
        ))
        fig_heatmap.update_layout(title="Monthly Forecast as % of Budget", height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    else:
        st.warning("Budget configuration not loaded. Run `python src/budget_loader.py` first.")

# ===== TAB 7: SAVINGS & INCOME =====
with tab7:
    st.markdown("### Savings & Income Tracking")

    if budget_config:
        # Calculate savings projection
        savings = calculate_savings_projection(df_filtered, budget_config)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Monthly Income",
                f"¥{budget_config['income']:.0f}",
                delta=f"Annual: ¥{budget_config['income']*12:.0f}"
            )

        with col2:
            st.metric(
                "YTD Savings",
                f"¥{savings['ytd_savings']:.0f}",
                delta=f"{savings['ytd_savings_pct']:.1f}% of income"
            )

        with col3:
            st.metric(
                "Savings Goal",
                f"¥{budget_config['saving_goal_monthly']:.0f}/month",
                delta=f"¥{budget_config['saving_goal_annual']:.0f}/year"
            )

        with col4:
            status = "✅ On Track" if savings['on_track'] else "⚠️ At Risk"
            st.metric(
                "Year-End Projection",
                f"¥{savings['projected_year_end_savings']:.0f}",
                delta=status
            )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Savings Progress")

            # Progress meter
            goal = budget_config['saving_goal_annual']
            projected = savings['projected_year_end_savings']
            progress_pct = min((projected / goal * 100), 120) if goal > 0 else 0

            # Create progress bar using plotly
            fig_progress = go.Figure(data=[
                go.Bar(
                    y=['Savings Goal'],
                    x=[goal],
                    orientation='h',
                    marker=dict(color='rgba(200,200,200,0.3)'),
                    name='Goal',
                    showlegend=False
                ),
                go.Bar(
                    y=['Savings Goal'],
                    x=[projected],
                    orientation='h',
                    marker=dict(color='#00CC96' if savings['on_track'] else '#FFA15A'),
                    name='Projected',
                    showlegend=False,
                    text=f"¥{projected:.0f}",
                    textposition='auto'
                )
            ])
            fig_progress.update_layout(
                barmode='overlay',
                height=150,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Amount (¥)",
                yaxis_title=""
            )
            st.plotly_chart(fig_progress, use_container_width=True)

            # Monthly breakdown
            st.markdown("**Monthly Breakdown**")
            breakdown_data = {
                'Need Spending': df_filtered[df_filtered['category'].isin(['Groceries', 'Transportation'])]['amount'].sum(),
                'Want Spending': df_filtered[df_filtered['category'].isin(['Eating Out', 'Shopping'])]['amount'].sum(),
                'Savings': savings['ytd_savings']
            }

            fig_breakdown = px.pie(
                values=breakdown_data.values(),
                names=breakdown_data.keys(),
                color_discrete_sequence=['#EF553B', '#636EFA', '#00CC96'],
                title="YTD Allocation"
            )
            fig_breakdown.update_layout(height=300)
            st.plotly_chart(fig_breakdown, use_container_width=True)

        with col2:
            st.markdown("### Spending Trend")

            # Line chart: cumulative savings over time
            df_daily = df_filtered.sort_values('timestamp').copy()
            df_daily['cumsum'] = df_daily['amount'].cumsum()

            # Calculate expected savings trajectory
            days_elapsed = (df_daily['timestamp'].max() - df_daily['timestamp'].min()).days + 1
            total_days = 365
            expected_daily = budget_config['saving_goal_annual'] / total_days
            df_daily['expected_cumsum'] = expected_daily * (df_daily['timestamp'] - df_daily['timestamp'].min()).dt.days

            fig_savings_trend = go.Figure()

            fig_savings_trend.add_trace(go.Scatter(
                x=df_daily['timestamp'],
                y=savings['ytd_income'] - df_daily['cumsum'],
                fill='tozeroy',
                name='Actual Savings',
                line=dict(color='#00CC96'),
                hovertemplate='%{x|%Y-%m-%d}<br>¥%{y:.2f}<extra></extra>'
            ))

            fig_savings_trend.update_layout(
                title="Cumulative Savings Over Time",
                xaxis_title="Date",
                yaxis_title="Savings (¥)",
                hovermode='x unified',
                height=350
            )
            st.plotly_chart(fig_savings_trend, use_container_width=True)

            # Summary stats
            st.markdown("**Summary**")
            st.write(f"""
            - **Days with data**: {savings['months_passed']} months (~{days_elapsed} days)
            - **Average monthly spend**: ¥{savings['avg_monthly_spend']:.2f}
            - **Average monthly savings**: ¥{savings['ytd_savings']/savings['months_passed']:.2f}
            - **Projected remainder**: ¥{savings['projected_total_spend'] - savings['ytd_spend']:.2f} ({12-savings['months_passed']} months)
            - **Variance to goal**: ¥{savings['projected_vs_goal']:.2f}
            """)

    else:
        st.warning("Budget configuration not loaded.")

# ===== TAB 8: ACTION PLAN =====
with tab8:
    st.markdown("### Decision-Making Dashboard: Cut Non-Essential Costs & Hit Savings Goals")

    # Feature 1: Need vs Want Efficiency Score
    st.markdown("## 1️⃣ Need vs Want Efficiency Score")
    st.markdown("Monthly breakdown: what % of your spend is discretionary (Want) vs essential (Need)?")

    # Calculate Want categories from budget_config
    want_categories = [cat for cat, info in budget_config['categories'].items() if info['type'] == 'Want']
    df_monthly = df_filtered.copy()
    df_monthly['month'] = df_monthly['timestamp'].dt.to_period('M')

    efficiency_data = []
    for month in sorted(df_monthly['month'].unique()):
        month_df = df_monthly[df_monthly['month'] == month]
        total_spend = month_df['amount'].sum()
        want_spend = month_df[month_df['category'].isin(want_categories)]['amount'].sum()
        need_spend = month_df[~month_df['category'].isin(want_categories)]['amount'].sum()

        want_pct = (want_spend / total_spend * 100) if total_spend > 0 else 0
        need_pct = (need_spend / total_spend * 100) if total_spend > 0 else 0

        # Calculate savings gap
        monthly_savings = budget_config['income'] - total_spend
        savings_goal = budget_config['saving_goal_monthly']
        savings_gap = max(0, savings_goal - monthly_savings)

        efficiency_data.append({
            'month': str(month),
            'total_spend': total_spend,
            'need_spend': need_spend,
            'want_spend': want_spend,
            'need_pct': need_pct,
            'want_pct': want_pct,
            'monthly_savings': monthly_savings,
            'savings_gap': savings_gap,
            'flagged': want_pct > 40
        })

    efficiency_df = pd.DataFrame(efficiency_data)

    # Stacked bar chart: Need / Want / Gap
    fig_efficiency = go.Figure()

    fig_efficiency.add_trace(go.Bar(
        x=efficiency_df['month'],
        y=efficiency_df['need_spend'],
        name='Need (Essential)',
        marker=dict(color='#EF553B')
    ))

    fig_efficiency.add_trace(go.Bar(
        x=efficiency_df['month'],
        y=efficiency_df['want_spend'],
        name='Want (Discretionary)',
        marker=dict(color='#636EFA')
    ))

    fig_efficiency.add_trace(go.Bar(
        x=efficiency_df['month'],
        y=efficiency_df['savings_gap'],
        name='Gap to ¥600 Savings Goal',
        marker=dict(color='#FFA15A', opacity=0.6)
    ))

    fig_efficiency.update_layout(
        barmode='stack',
        title='Monthly Need/Want Breakdown + Savings Gap',
        xaxis_title='Month',
        yaxis_title='Amount (¥)',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_efficiency, use_container_width=True)

    # Efficiency table
    st.markdown("### Monthly Efficiency Summary")
    efficiency_display = efficiency_df[[
        'month', 'total_spend', 'need_pct', 'want_pct', 'monthly_savings', 'savings_gap'
    ]].copy()
    efficiency_display.columns = ['Month', 'Total Spend', 'Need %', 'Want %', 'Savings', 'Gap to Goal']
    efficiency_display['Flag'] = efficiency_df['flagged'].apply(lambda x: '🚩 >40% Want' if x else '✅')

    for col in ['Total Spend', 'Savings', 'Gap to Goal']:
        efficiency_display[col] = efficiency_display[col].apply(lambda x: f"¥{x:.0f}")

    for col in ['Need %', 'Want %']:
        efficiency_display[col] = efficiency_display[col].apply(lambda x: f"{x:.0f}%")

    st.dataframe(efficiency_display, use_container_width=True, hide_index=True)

    st.divider()

    # Feature 2: Top 10 Cuttable Transactions
    st.markdown("## 2️⃣ Top 10 Cuttable Merchants (by Monthly Impact)")
    st.markdown("Ranked by recurring/high-spend discretionary merchants you could reduce without losing essentials.")

    want_df = df_filtered[df_filtered['category'].isin(want_categories)].copy()

    # Calculate monthly impact and recurring pattern for each merchant
    if len(want_df) > 0:
        months_in_data = (df_filtered['timestamp'].max() - df_filtered['timestamp'].min()).days / 30

        merchant_impact = []
        for merchant in want_df['merchant'].unique():
            merchant_txns = want_df[want_df['merchant'] == merchant]
            total_spend = merchant_txns['amount'].sum()
            visit_count = len(merchant_txns)
            avg_per_visit = merchant_txns['amount'].mean()
            monthly_impact = total_spend / max(months_in_data, 1)

            # Check if recurring (3+ visits with consistent amounts)
            is_recurring = False
            if visit_count >= 3:
                amount_std = merchant_txns['amount'].std()
                cv = amount_std / avg_per_visit if avg_per_visit > 0 else 0
                is_recurring = cv < 0.20

            merchant_impact.append({
                'merchant': merchant,
                'total_spend': total_spend,
                'visit_count': visit_count,
                'avg_per_visit': avg_per_visit,
                'monthly_impact': monthly_impact,
                'is_recurring': is_recurring
            })

        cuttable_df = pd.DataFrame(merchant_impact).sort_values('monthly_impact', ascending=False).head(10)

        cuttable_display = cuttable_df[[
            'merchant', 'monthly_impact', 'total_spend', 'visit_count', 'avg_per_visit', 'is_recurring'
        ]].copy()
        cuttable_display.columns = ['Merchant', 'Monthly Impact (¥)', 'Total Spend (¥)', 'Visits', 'Avg per Visit (¥)', 'Recurring?']

        for col in ['Monthly Impact (¥)', 'Total Spend (¥)', 'Avg per Visit (¥)']:
            cuttable_display[col] = cuttable_display[col].apply(lambda x: f"¥{x:.0f}")

        cuttable_display['Recurring?'] = cuttable_display['Recurring?'].apply(lambda x: '🔁 Yes' if x else '—')

        st.dataframe(cuttable_display, use_container_width=True, hide_index=True)

        cumulative_impact = cuttable_df['monthly_impact'].sum()
        st.markdown(f"**Top 10 combined monthly impact:** ¥{cumulative_impact:.0f}/month ({cumulative_impact*12:.0f}/year)")
    else:
        st.info("No Want category transactions in current date range.")

    st.divider()

    # Feature 3: Savings Gap Calculator (Interactive)
    st.markdown("## 3️⃣ Savings Gap Calculator: What-If Scenarios")
    st.markdown("Adjust discretionary spending below to see impact on year-end savings projection.")

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown("### Cut by Category")

        # Get current monthly spend by Want category
        want_monthly_spend = {}
        for cat in want_categories:
            cat_spend = df_monthly[df_monthly['category'] == cat]['amount'].sum()
            cat_months = len(df_monthly['month'].unique())
            want_monthly_spend[cat] = cat_spend / max(cat_months, 1) if cat_months > 0 else 0

        # Sliders for each Want category
        cut_fractions = {}
        for cat in sorted(want_categories):
            current_avg = want_monthly_spend[cat]
            st.markdown(f"**{cat}** (avg ¥{current_avg:.0f}/mo)")
            cut_pct = st.slider(
                f"Cut {cat}",
                min_value=0,
                max_value=50,
                value=0,
                step=5,
                label_visibility='collapsed',
                key=f"slider_{cat}"
            )
            cut_fractions[cat] = cut_pct / 100.0

    with col2:
        st.markdown("### Projected Year-End Savings")

        # Baseline savings (from calculate_savings_projection)
        baseline_savings = calculate_savings_projection(df_filtered, budget_config)
        baseline_projected = baseline_savings['projected_year_end_savings']

        # Calculate adjusted savings with cuts applied
        ytd_spend = df_filtered['amount'].sum()
        ytd_income = baseline_savings['ytd_income']
        months_passed = baseline_savings['months_passed']
        remaining_months = 12 - months_passed

        # Apply cuts proportionally
        total_want_monthly = sum(want_monthly_spend.values())
        adjusted_monthly_spend = 0

        for cat in df_filtered['category'].unique():
            if cat in want_categories:
                cut_fraction = cut_fractions.get(cat, 0)
                cat_monthly = want_monthly_spend.get(cat, 0)
                adjusted_monthly_spend += cat_monthly * (1 - cut_fraction)
            else:
                cat_monthly = df_monthly[df_monthly['category'] == cat]['amount'].sum()
                cat_months = len(df_monthly['month'].unique())
                adjusted_monthly_spend += (cat_monthly / max(cat_months, 1)) if cat_months > 0 else 0

        adjusted_projected_spend = ytd_spend + (adjusted_monthly_spend * remaining_months)
        annual_income = budget_config['income'] * 12
        adjusted_projected_savings = annual_income - adjusted_projected_spend

        # Difference from goal
        savings_goal = budget_config['saving_goal_annual']

        # Display bars
        fig_savings_calc = go.Figure()

        fig_savings_calc.add_trace(go.Bar(
            y=['Current\nTrajectory'],
            x=[baseline_projected],
            orientation='h',
            marker=dict(color='#636EFA'),
            name='Current',
            text=f"¥{baseline_projected:.0f}",
            textposition='auto',
            showlegend=False
        ))

        fig_savings_calc.add_trace(go.Bar(
            y=['With Cuts\nApplied'],
            x=[adjusted_projected_savings],
            orientation='h',
            marker=dict(color='#00CC96'),
            name='Adjusted',
            text=f"¥{adjusted_projected_savings:.0f}",
            textposition='auto',
            showlegend=False
        ))

        fig_savings_calc.add_vline(
            x=savings_goal,
            line_dash='dash',
            line_color='#FFA15A',
            annotation_text=f"Goal: ¥{savings_goal:.0f}",
            annotation_position='top right'
        )

        fig_savings_calc.update_layout(
            title='Year-End Savings Projection',
            xaxis_title='Savings (¥)',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig_savings_calc, use_container_width=True)

        # Calculate total cut needed
        total_cut_needed = max(0, savings_goal - adjusted_projected_savings)
        total_cut_monthly = total_cut_needed / remaining_months if remaining_months > 0 else 0

        if total_cut_needed > 0:
            st.warning(f"**To hit your ¥{savings_goal:.0f} goal:** Need to cut ¥{total_cut_needed:.0f} total (¥{total_cut_monthly:.0f}/month more)")
        else:
            st.success(f"✅ **On track!** Projected to exceed goal by ¥{-total_cut_needed:.0f}")

    st.divider()

    # Feature 4: Investment Readiness Indicator
    st.markdown("## 4️⃣ Investment Readiness Indicator")
    st.markdown("Have you consistently hit your ¥600/month savings goal?")

    # Check last 3 months
    last_3_months = sorted(df_monthly['month'].unique())[-3:]
    months_met_goal = 0
    month_details = []

    for month in last_3_months:
        month_df = df_monthly[df_monthly['month'] == month]
        month_spend = month_df['amount'].sum()
        month_savings = budget_config['income'] - month_spend
        goal_met = month_savings >= budget_config['saving_goal_monthly']

        months_met_goal += int(goal_met)
        month_details.append({
            'month': str(month),
            'savings': month_savings,
            'met_goal': '✅' if goal_met else '❌'
        })

    months_df = pd.DataFrame(month_details)
    st.dataframe(months_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        if months_met_goal == 3:
            st.success(f"### 🎯 Ready to Invest!")
            avg_surplus = (sum([budget_config['income'] - df_monthly[df_monthly['month'] == m]['amount'].sum() for m in last_3_months]) / 3)
            st.markdown(f"**You've met your ¥600 savings goal for 3 consecutive months.**\n\n"
                       f"Average monthly surplus: **¥{avg_surplus:.0f}**\n\n"
                       f"You may want to consider investing this surplus to build long-term wealth. "
                       f"(Consult with a financial advisor for guidance on investment options.)")
        else:
            st.info(f"### ⏳ Keep Going")
            st.markdown(f"**Progress: {months_met_goal} of 3 months met ¥600 goal**\n\n"
                       f"You're on a good path. Keep cutting unnecessary expenses to consistently hit your savings target.")

    with col2:
        st.markdown("### Why This Matters")
        st.markdown(
            "Investing allows your money to grow through compound returns. Once you've proven you can "
            "consistently save ¥600/month, those surpluses become capital for long-term investments like:\n\n"
            "- Index funds (diversified, low-cost)\n"
            "- Emergency fund expansion (3-6 months expenses)\n"
            "- Retirement accounts (if available)\n\n"
            "_This is NOT financial advice — consult a professional._"
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
