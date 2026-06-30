"""One-off script to fix data quality issues: relabel ??? and Travel, add NaN labels."""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8')


def fix_labels():
    """Fix labeled_transactions.csv by relabeling ??? and Travel rows, and ~30 NaN rows."""

    # Load data
    df = pd.read_csv('data/labeled/labeled_transactions.csv', encoding='utf-8')
    print(f"Loaded {len(df)} rows")
    print(f"Before: category value counts:")
    print(df['category'].value_counts(dropna=False).to_string())
    print()

    # ========================================================================
    # PHASE 1: Relabel 12 "???" rows with their correct categories
    # ========================================================================
    print("PHASE 1: Relabeling ??? rows")
    print("-" * 70)

    remap_dict = {
        '上海公共交通卡股份有限公司': 'Transportation',
        '宁波市轨道交通集团有限公司线网调度分公司': 'Transportation',
        '卓联（上海）餐饮服务有限公司': 'Eating Out',
        '上海饱猫餐饮管理有限公司': 'Eating Out',
        'floating kitchen': 'Eating Out',
        'LA BARAKA UV': 'Eating Out',
        '上海优悠生活商业管理有限公司': 'Shopping',
        'ao**店': 'Shopping',
        'ws**1': 'Shopping',
    }

    q_rows = df[df['category'] == '???'].copy()
    print(f"Found {len(q_rows)} rows with category='???'")

    for idx, row in q_rows.iterrows():
        merchant = row['merchant']
        if merchant in remap_dict:
            new_cat = remap_dict[merchant]
            print(f"  {merchant[:40]:40s} ??? → {new_cat}")
            df.loc[idx, 'category'] = new_cat
            df.loc[idx, 'labeled'] = True
        else:
            print(f"  {merchant[:40]:40s} ??? → (NO MAPPING, skipped)")

    print(f"\nAfter Phase 1: {len(df[df['category'] == '???'])} ??? rows remaining")
    print()

    # ========================================================================
    # PHASE 2: Relabel 2 Travel rows as "Other"
    # ========================================================================
    print("PHASE 2: Relabeling Travel rows")
    print("-" * 70)

    travel_rows = df[df['category'] == 'Travel'].copy()
    print(f"Found {len(travel_rows)} Travel rows")

    for idx, row in travel_rows.iterrows():
        merchant = row['merchant']
        print(f"  {merchant[:40]:40s} Travel → Other")
        df.loc[idx, 'category'] = 'Other'
        df.loc[idx, 'labeled'] = True

    print(f"\nAfter Phase 2: {len(df[df['category'] == 'Travel'])} Travel rows remaining")
    print()

    # ========================================================================
    # PHASE 3: Label ~30 NaN rows with high-confidence categories
    # ========================================================================
    print("PHASE 3: Labeling obvious NaN rows")
    print("-" * 70)

    # Mapping of merchants → categories for obvious NaN rows
    nan_remap = {
        '上海蕤盛工贸': 'Groceries',  # Vending machines (12+ rows, fixed at 0.683 conf)
        '济明路蘭州牛肉面（百热客）': 'Eating Out',  # Noodle shop (misclassified as Travel)
        'K-MART': 'Groceries',  # Supermarket
        '达美乐': 'Eating Out',  # Domino's Pizza
        '美淑家·韩国料理·石锅拌饭': 'Eating Out',  # Korean restaurant
        '饿梨酱Hey Guac·美洲活力西餐': 'Eating Out',  # Western restaurant
        '小满手工粉': 'Eating Out',  # Handmade noodles
        '广州市玩客游乐设备有限公司': 'Other',  # Amusement arcade
        '上海国际旅行卫生保健中心': 'Other',  # Health clinic
        '🔥战🙏狼🔥': 'Transfers & Gifts',  # Personal QR payment
    }

    nan_rows = df[df['category'].isna()]
    print(f"Found {len(nan_rows)} NaN rows")

    labeled_count = 0
    for idx, row in nan_rows.iterrows():
        merchant = row['merchant']
        if merchant in nan_remap:
            new_cat = nan_remap[merchant]
            df.loc[idx, 'category'] = new_cat
            df.loc[idx, 'labeled'] = True
            labeled_count += 1
            print(f"  {merchant[:40]:40s} NaN → {new_cat}")

    print(f"\nPhase 3: Labeled {labeled_count} NaN rows")
    print(f"Remaining NaN rows: {df['category'].isna().sum()}")
    print()

    # ========================================================================
    # SAVE AND REPORT
    # ========================================================================
    print("FINAL CATEGORY DISTRIBUTION")
    print("-" * 70)
    print(df['category'].value_counts(dropna=False).to_string())
    print()

    print("SUMMARY:")
    print(f"  Relabeled ??? rows: {len(q_rows)} → Eating Out/Transportation/Shopping")
    print(f"  Relabeled Travel rows: 2 → Other")
    print(f"  Labeled obvious NaN rows: {labeled_count} → Groceries/Eating Out/Other/Transfers&Gifts")
    print(f"  Other category: 9 → {(df['category'] == 'Other').sum()} (includes 2 Travel + new Amusement/Health)")
    print(f"  Groceries category: 204 → {(df['category'] == 'Groceries').sum()} (includes vending machines)")
    print(f"  Eating Out category: 307 → {(df['category'] == 'Eating Out').sum()} (includes noodles + restaurants)")
    print()

    # Save
    output_path = 'data/labeled/labeled_transactions.csv'
    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"✓ Saved to {output_path}")
    print()

    # Verify
    print("VERIFICATION:")
    print(f"  ??? rows remaining: {(df['category'] == '???').sum()} (should be 0)")
    print(f"  Travel rows remaining: {(df['category'] == 'Travel').sum()} (should be 0)")
    print(f"  NaN rows remaining: {df['category'].isna().sum()} (was 121, now fewer)")
    print(f"  labeled=True rows: {(df['labeled'] == True).sum()}")
    print()

    if (df['category'] == '???').sum() == 0 and (df['category'] == 'Travel').sum() == 0:
        print("✓ SUCCESS: ??? and Travel categories eliminated")
    else:
        print("✗ WARNING: Some ??? or Travel rows remain")


if __name__ == '__main__':
    fix_labels()
