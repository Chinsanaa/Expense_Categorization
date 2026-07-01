"""
Helper functions for dashboard: category mapping, budget lookups, etc.
"""
import json
import pandas as pd

# Map classified transaction categories to budget categories
CATEGORY_MAPPING = {
    'Eating Out': 'Eating Out',
    'Groceries': 'Groceries',
    'Transportation': 'Transportation',
    'Shopping': 'Shopping',
    'Transfers & Gifts': 'Transfers & Gifts',
    'Other': 'Other',
    'Utilities & Services': 'Utilities & Services',
    'Saving': 'Saving',
    'Investing': 'Investing',
    # Budget-only until next semester (no payment-app transactions yet):
    # 'Saving', 'Investing'
    # In classified data but not yet mapped to budget:
    # 'Travel', 'Health & Wellness', 'Entertainment'
}

# Color map for category types
TYPE_COLORS = {
    'Need': '#EF553B',  # Red
    'Want': '#636EFA',  # Blue
}

RISK_COLORS = {
    'Low': '#00CC96',   # Green
    'Medium': '#FFA15A',  # Orange
    'High': '#EF553B',   # Red
}

# Dark-theme chart palette
CHART_COLORS = [
    '#7c6af7', '#4fc3f7', '#2ecc71', '#f39c12',
    '#e74c3c', '#9b59b6', '#1abc9c', '#e67e22',
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#c8cdd3', size=13),
    colorway=CHART_COLORS,
    margin=dict(l=16, r=16, t=48, b=16),
    legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0),
    xaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
)


def apply_chart_theme(fig, height=400):
    """Apply consistent dark-theme styling to a Plotly figure."""
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    return fig


def load_budget_config(path='data/budget_config.json'):
    """Load budget configuration from JSON."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Budget config not found at {path}")
        return None


def get_budget_for_category(budget_config, category, month_index=None):
    """
    Get budget target for a category.

    Args:
        budget_config: Budget dict
        category: Category name
        month_index: 0-8 for Sep-May (None = annual)

    Returns:
        float or None
    """
    if not budget_config or 'categories' not in budget_config:
        return None

    cat_budget = budget_config['categories'].get(category)
    if not cat_budget:
        return None

    if month_index is None:
        return cat_budget.get('annual_budget')

    monthly_allocations = cat_budget.get('monthly', [])
    if month_index < len(monthly_allocations):
        return monthly_allocations[month_index]

    return cat_budget.get('monthly_budget')


def get_budget_type(budget_config, category):
    """Get budget type (Need/Want) for a category."""
    if not budget_config or 'categories' not in budget_config:
        return None

    cat_budget = budget_config['categories'].get(category)
    return cat_budget.get('type') if cat_budget else None


def get_type_color(budget_config, category):
    """Get color for category type (Need/Want)."""
    cat_type = get_budget_type(budget_config, category)
    return TYPE_COLORS.get(cat_type, '#999999')


def get_risk_color(risk_level):
    """Get color for risk level."""
    return RISK_COLORS.get(risk_level, '#999999')


def calculate_ytd_vs_budget(df_transactions, budget_config):
    """
    Calculate year-to-date spending vs budget for all categories.

    Returns:
        DataFrame with columns: category, type, ytd_actual, budget, variance, pct_of_budget
    """
    if not budget_config:
        return pd.DataFrame()

    df_trans = df_transactions.copy()
    df_trans['timestamp'] = pd.to_datetime(df_trans['timestamp'])

    # YTD actual by category
    ytd_actual = df_trans.groupby('category')['amount'].sum()

    data = []
    for category, cat_budget in budget_config['categories'].items():
        actual = ytd_actual.get(category, 0)
        budget = cat_budget['annual_budget']
        variance = actual - budget
        pct = (actual / budget * 100) if budget > 0 else 0

        data.append({
            'category': category,
            'type': cat_budget['type'],
            'ytd_actual': actual,
            'budget': budget,
            'variance': variance,
            'pct_of_budget': pct
        })

    return pd.DataFrame(data)


def get_all_categories_from_budget(budget_config):
    """Get list of all categories from budget config."""
    if not budget_config:
        return []
    return list(budget_config['categories'].keys())


def format_currency(value):
    """Format value as currency."""
    return f"¥{value:,.2f}"


def get_status_badge(pct_of_budget, cat_type='Want'):
    """
    Get status badge based on percentage of budget.

    Returns: (emoji, color, status_text)
    """
    if cat_type == 'Need':
        # Need categories: red if >100, orange if >80
        if pct_of_budget >= 100:
            return '🔴', '#EF553B', 'Over Budget'
        elif pct_of_budget >= 80:
            return '🟠', '#FFA15A', 'Caution'
        else:
            return '🟢', '#00CC96', 'On Track'
    else:
        # Want categories: orange if >100, yellow if >80
        if pct_of_budget >= 100:
            return '🟠', '#FFA15A', 'Over Budget'
        elif pct_of_budget >= 80:
            return '🟡', '#FECB52', 'Caution'
        else:
            return '🟢', '#00CC96', 'On Track'


if __name__ == '__main__':
    # Test
    budget = load_budget_config()
    print("Budget config loaded:")
    print(f"  Income: ¥{budget['income']}")
    print(f"  Categories: {len(budget['categories'])}")

    for cat, data in budget['categories'].items():
        print(f"  {cat}: {data['type']} - ¥{data['annual_budget']:.2f}/yr")
