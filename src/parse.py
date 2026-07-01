"""CSV/Excel parsers for Alipay and WeChat transactions."""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple


def _find_alipay_header(csv_path: str) -> Tuple[int, str, bool]:
    """
    Locate the Alipay data header row and encoding.

    Returns:
        (skiprows, encoding, is_chinese_format)
    """
    for encoding in ('utf-8-sig', 'utf-8', 'gbk', 'gb18030'):
        try:
            with open(csv_path, encoding=encoding) as f:
                for i, line in enumerate(f):
                    if 'Transaction Time' in line and 'Type' in line:
                        return i, encoding, False
                    if '交易时间' in line and '收/支' in line:
                        return i, encoding, True
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Cannot detect Alipay CSV format: {csv_path}")


def parse_alipay_english(csv_path: str, encoding: str = 'utf-8', skiprows: int = 0) -> pd.DataFrame:
    """Parse English-translated Alipay export CSV."""
    df = pd.read_csv(csv_path, encoding=encoding, skiprows=skiprows)

    df = df[df['Type'] == 'Expense']
    df = df[df['Transaction Status'].str.contains('Successful|Closed', case=False, na=False)]

    return pd.DataFrame({
        'timestamp': pd.to_datetime(df['Transaction Time']),
        'merchant': df['Transaction Counterparty'].fillna('').str.strip(),
        'description': df['Product Description'].fillna('').str.strip(),
        'amount': df['Amount'].astype(float),
        'source': 'alipay',
    })


def parse_alipay_native(csv_path: str, encoding: str = 'gbk', skiprows: int = 0) -> pd.DataFrame:
    """Parse native Chinese Alipay export CSV (GBK/UTF-8)."""
    df = pd.read_csv(csv_path, encoding=encoding, skiprows=skiprows)

    df = df[df['收/支'] == '支出']
    df = df[df['交易状态'].astype(str).str.contains('交易成功|交易关闭', na=False)]

    amount = df['金额'].astype(str).str.replace(',', '', regex=False).astype(float)

    return pd.DataFrame({
        'timestamp': pd.to_datetime(df['交易时间']),
        'merchant': df['交易对方'].fillna('').astype(str).str.strip(),
        'description': df['商品说明'].fillna('').astype(str).str.strip(),
        'amount': amount,
        'source': 'alipay',
    })


def parse_alipay(csv_path: str) -> pd.DataFrame:
    """Parse Alipay CSV — auto-detects English vs native Chinese export."""
    skiprows, encoding, is_chinese = _find_alipay_header(csv_path)
    if is_chinese:
        return parse_alipay_native(csv_path, encoding=encoding, skiprows=skiprows)
    return parse_alipay_english(csv_path, encoding=encoding, skiprows=skiprows)


def parse_wechat_excel(xlsx_path: str) -> pd.DataFrame:
    """Parse WeChat export Excel file (native Chinese format with original texts)."""
    df = pd.read_excel(xlsx_path, sheet_name=0, skiprows=17)

    expected_cols = [
        '交易时间', '交易类型', '交易对方', '商品', '收/支',
        '金额(元)', '支付方式', '当前状态', '交易单号', '商户单号', '备注',
    ]

    first_val = str(df.iloc[0, 0])
    if '交易时间' in first_val:
        df = df.iloc[1:].reset_index(drop=True)
        df.columns = expected_cols
    else:
        df.columns = expected_cols

    df = df[df['收/支'] == '支出']
    df = df[df['当前状态'].isin(['支付成功', '已转账'])]

    amount_clean = df['金额(元)'].astype(str).str.replace(',', '').astype(float)

    return pd.DataFrame({
        'timestamp': pd.to_datetime(df['交易时间']),
        'merchant': df['交易对方'].fillna('').str.strip(),
        'description': df['商品'].fillna('').str.strip(),
        'amount': amount_clean,
        'source': 'wechat',
    })


def parse_wechat_csv(csv_path: str) -> pd.DataFrame:
    """Parse WeChat export CSV (English-translated version - fallback)."""
    df = pd.read_csv(csv_path, encoding='utf-8', skiprows=17)

    df = df[df['Income/Expense'] == 'Expense']
    df = df[df['Current Status'].str.contains('successful|Transferred', case=False, na=False)]

    return pd.DataFrame({
        'timestamp': pd.to_datetime(df['Transaction Time']),
        'merchant': df['Counterparty'].fillna('').str.strip(),
        'description': df['Product'].fillna('').str.strip(),
        'amount': df['Amount (CNY)'].astype(float),
        'source': 'wechat',
    })


def resolve_raw_paths(base_path: Optional[Path] = None) -> Tuple[Optional[Path], Optional[Path]]:
    """
    Resolve default Alipay and WeChat paths under data/raw/.

    Returns:
        (alipay_path or None, wechat_path or None)
    """
    base = base_path or Path(__file__).parent.parent
    raw_dir = base / 'data' / 'raw'

    alipay_path = None
    for name in ('alipay.csv', 'alipay_expenses.csv'):
        candidate = raw_dir / name
        if candidate.exists():
            alipay_path = candidate
            break

    wechat_path = None
    for name in ('raw-wechat.xlsx', 'wechat.xlsx', 'wechat.csv'):
        candidate = raw_dir / name
        if candidate.exists():
            wechat_path = candidate
            break

    return alipay_path, wechat_path


def load_transactions(alipay_path: Optional[str] = None,
                    wechat_path: Optional[str] = None) -> pd.DataFrame:
    """Load and combine Alipay and WeChat transactions from CSV or Excel."""
    dfs = []

    if alipay_path and Path(alipay_path).exists():
        try:
            print("Parsing Alipay CSV...")
            df_alipay = parse_alipay(alipay_path)
            print(f"  OK - Loaded {len(df_alipay)} transactions")
            dfs.append(df_alipay)
        except Exception as e:
            print(f"  FAIL - Error: {e}")

    if wechat_path and Path(wechat_path).exists():
        try:
            wechat_path_obj = Path(wechat_path)
            if wechat_path_obj.suffix.lower() == '.xlsx':
                print("Parsing WeChat Excel...")
                df_wechat = parse_wechat_excel(wechat_path)
            else:
                print("Parsing WeChat CSV...")
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
    base_path = Path(__file__).parent.parent
    alipay_path, wechat_path = resolve_raw_paths(base_path)

    if not alipay_path and not wechat_path:
        print("Error: No raw files found in data/raw/")
        print("  Expected: alipay.csv and/or raw-wechat.xlsx")
        raise SystemExit(1)

    print(f"Alipay: {alipay_path or '(not found)'}")
    print(f"WeChat: {wechat_path or '(not found)'}")

    try:
        df = load_transactions(
            str(alipay_path) if alipay_path else None,
            str(wechat_path) if wechat_path else None,
        )

        print(f"\n{'='*70}")
        print(f"Successfully loaded {len(df)} total transactions")
        print(f"Date range: {df['timestamp'].min().date()} to {df['timestamp'].max().date()}")

        alipay_count = (df['source'] == 'alipay').sum()
        wechat_count = (df['source'] == 'wechat').sum()
        alipay_sum = df[df['source'] == 'alipay']['amount'].sum()
        wechat_sum = df[df['source'] == 'wechat']['amount'].sum()

        print(f"Total spend: {df['amount'].sum():,.2f}")
        print(f"  - Alipay: {alipay_count} transactions ({alipay_sum:,.2f})")
        print(f"  - WeChat: {wechat_count} transactions ({wechat_sum:,.2f})")

        print(f"\n{'='*70}")
        stats = df['amount'].describe()
        print(f"  Count: {int(stats['count'])}")
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Median: {df['amount'].median():.2f}")

        output_file = base_path / 'data' / 'processed' / 'transactions.csv'
        output_file.parent.mkdir(parents=True, exist_ok=True)
        save_processed(df, str(output_file))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
