"""CSV/Excel parsers for Alipay and WeChat transactions."""
import pandas as pd
from pathlib import Path
from typing import Optional


def parse_alipay(csv_path: str) -> pd.DataFrame:
    """Parse Alipay export CSV (English-translated version)."""
    df = pd.read_csv(csv_path, encoding='utf-8')

    # Keep only successful completed expenses
    df = df[df['Type'] == 'Expense']
    df = df[df['Transaction Status'].str.contains('Successful|Closed', case=False, na=False)]

    # Normalize to common schema
    normalized = pd.DataFrame({
        'timestamp': pd.to_datetime(df['Transaction Time']),
        'merchant': df['Transaction Counterparty'].fillna('').str.strip(),
        'description': df['Product Description'].fillna('').str.strip(),
        'amount': df['Amount'].astype(float),
        'source': 'alipay'
    })

    return normalized


def parse_wechat_excel(xlsx_path: str) -> pd.DataFrame:
    """Parse WeChat export Excel file (native Chinese format with original texts)."""
    # Excel has 17 header rows before the actual data table
    df = pd.read_excel(xlsx_path, sheet_name=0, skiprows=17)

    # Column names are in Chinese (first row after skip)
    # Rename columns using the actual header values
    # Columns: 交易时间, 交易类型, 交易对方, 商品, 收/支, 金额(元), 支付方式, 当前状态, 交易单号, 商户单号, 备注
    expected_cols = [
        '交易时间', '交易类型', '交易对方', '商品', '收/支',
        '金额(元)', '支付方式', '当前状态', '交易单号', '商户单号', '备注'
    ]

    # If first row is still a header, use it; otherwise infer from position
    first_val = str(df.iloc[0, 0])
    if '交易时间' in first_val:
        # First row contains header labels as values, skip it
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = expected_cols
    else:
        df.columns = expected_cols

    # Keep only completed expenses
    # 收/支: 支出 = Expense
    # 当前状态: 支付成功 = Payment successful
    df = df[df['收/支'] == '支出']
    df = df[df['当前状态'].isin(['支付成功', '已转账'])]

    # Clean amount (remove commas if present)
    amount_clean = df['金额(元)'].astype(str).str.replace(',', '').astype(float)

    # Normalize to common schema
    normalized = pd.DataFrame({
        'timestamp': pd.to_datetime(df['交易时间']),
        'merchant': df['交易对方'].fillna('').str.strip(),
        'description': df['商品'].fillna('').str.strip(),
        'amount': amount_clean,
        'source': 'wechat'
    })

    return normalized


def parse_wechat_csv(csv_path: str) -> pd.DataFrame:
    """Parse WeChat export CSV (English-translated version - fallback)."""
    # WeChat CSV has 17 header rows before data
    df = pd.read_csv(csv_path, encoding='utf-8', skiprows=17)

    # Keep only completed expenses
    df = df[df['Income/Expense'] == 'Expense']
    df = df[df['Current Status'].str.contains('successful|Transferred', case=False, na=False)]

    # Normalize to common schema
    normalized = pd.DataFrame({
        'timestamp': pd.to_datetime(df['Transaction Time']),
        'merchant': df['Counterparty'].fillna('').str.strip(),
        'description': df['Product'].fillna('').str.strip(),
        'amount': df['Amount (CNY)'].astype(float),
        'source': 'wechat'
    })

    return normalized


def load_transactions(alipay_path: Optional[str] = None,
                     wechat_path: Optional[str] = None) -> pd.DataFrame:
    """Load and combine Alipay and WeChat transactions from CSV or Excel."""
    dfs = []

    if alipay_path and Path(alipay_path).exists():
        try:
            print(f"Parsing Alipay CSV...")
            df_alipay = parse_alipay(alipay_path)
            print(f"  OK - Loaded {len(df_alipay)} transactions")
            dfs.append(df_alipay)
        except Exception as e:
            print(f"  FAIL - Error: {e}")

    if wechat_path and Path(wechat_path).exists():
        try:
            wechat_path_obj = Path(wechat_path)
            if wechat_path_obj.suffix.lower() == '.xlsx':
                print(f"Parsing WeChat Excel...")
                df_wechat = parse_wechat_excel(wechat_path)
            else:
                print(f"Parsing WeChat CSV...")
                df_wechat = parse_wechat_csv(wechat_path)
            print(f"  OK - Loaded {len(df_wechat)} transactions")
            dfs.append(df_wechat)
        except Exception as e:
            print(f"  FAIL - Error: {e}")

    if not dfs:
        raise ValueError("Must provide at least one valid file path")

    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values('timestamp').reset_index(drop=True)

    return combined


def save_processed(df: pd.DataFrame, output_path: str) -> None:
    """Save processed transactions to CSV."""
    df.to_csv(output_path, index=False)
    print(f"Saved processed data to {output_path}")


if __name__ == '__main__':
    # Test with both Alipay and WeChat (Excel preferred)
    base_path = Path(__file__).parent.parent

    # Use translated Alipay CSV (raw has GBK encoding issues)
    alipay_path = Path(r'C:\Users\User\Downloads\Finances_1st year\alipay_expenses.csv')

    # Use Excel WeChat first (original texts), fall back to CSV if not available
    wechat_excel = base_path / 'data' / 'raw' / 'raw-wechat.xlsx'
    wechat_csv = Path(r'C:\Users\User\Downloads\Finances_1st year\wechat_expense.csv')

    wechat_path = wechat_excel if wechat_excel.exists() else wechat_csv

    try:
        df = load_transactions(str(alipay_path), str(wechat_path))

        print(f"\n{'='*70}")
        print(f"Successfully loaded {len(df)} total transactions")
        print(f"Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")

        alipay_count = (df['source'] == 'alipay').sum()
        wechat_count = (df['source'] == 'wechat').sum()
        alipay_sum = df[df['source']=='alipay']['amount'].sum()
        wechat_sum = df[df['source']=='wechat']['amount'].sum()

        print(f"Total spend: ¥{df['amount'].sum():,.2f}")
        print(f"  - Alipay: {alipay_count} transactions (¥{alipay_sum:,.2f})")
        print(f"  - WeChat: {wechat_count} transactions (¥{wechat_sum:,.2f})")

        print(f"\n{'='*70}")
        print("Transaction amount statistics:")
        stats = df['amount'].describe()
        print(f"  Count: {int(stats['count'])}")
        print(f"  Mean: ¥{stats['mean']:.2f}")
        print(f"  Median: ¥{df['amount'].median():.2f}")
        print(f"  Min: ¥{stats['min']:.2f}")
        print(f"  Max: ¥{stats['max']:.2f}")

        # Save processed data
        output_file = Path(base_path / 'data' / 'processed' / 'transactions.csv')
        output_file.parent.mkdir(parents=True, exist_ok=True)
        save_processed(df, str(output_file))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
