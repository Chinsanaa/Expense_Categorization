# Personal Finance Categorizer

An end-to-end machine learning pipeline to automatically categorize personal financial transactions from Alipay and WeChat Pay using supervised text classification.

**Status**: ✅ Complete (Stages 1-7 + Dashboard) | 97.3% Accuracy | 901 transactions classified | 157 merchant rules | 81.4% avg confidence

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (parse → classify → visualize)
python3 src/parse.py          # Stage 1: Parse CSVs
python3 src/classify.py       # Stage 6: Classify all transactions
python3 src/visualize.py      # Stage 7: Generate charts

# Launch interactive dashboard
streamlit run src/dashboard.py
```

## Project Summary

### What It Does
- Parses Alipay CSV + WeChat Excel exports
- Cleans transaction text (handles Chinese + English)
- Auto-labels using merchant rules (748/901 transactions, 157 rules)
- Trains Logistic Regression classifier (97.3% accuracy)
- Classifies all 901 transactions into 5 spending categories
- Generates spending visualizations, dashboards, and summaries
- Detects budget overages and spending anomalies

### Key Results
- **Model Accuracy**: 97.3% on test set (corrected labels)
- **Transactions Classified**: 901/901 (100%)
- **Mean Confidence**: 81.4%
- **Training Data**: 748 labeled transactions (157 merchant rules)
- **Features**: 246 TF-IDF tokens (jieba-segmented)
- **"Other" Category**: Eliminated (0 transactions)

### Spending Breakdown (Refined)
| Category | Count | Pct | Avg Confidence |
|----------|-------|-----|---|
| Eating Out | 426 | 47.3% | 80.0% |
| Groceries | 223 | 24.8% | 85.3% |
| Transportation | 175 | 19.4% | 85.2% |
| Shopping | 50 | 5.5% | 75.0% |
| Transfers & Gifts | 27 | 3.0% | 59.1% |

## Pipeline Architecture

```
Stage 1: Parse
  Alipay CSV + WeChat Excel → normalized transactions.csv

Stage 2: Clean
  merchant + description → single 'text' field (English lowercased, Chinese preserved)

Stage 3: Label
  merchant_rules.csv (136 rules) → auto-label 544 transactions

Stage 4: Vectorize
  jieba tokenization + TF-IDF → 195 features

Stage 5: Train
  Logistic Regression on training set (434 samples)
  → 99.1% test accuracy (109 samples)

Stage 6: Classify
  Apply model to ALL 901 transactions (labeled + unlabeled)

Stage 7: Visualize
  Generate spending charts and statistics
```

## File Structure

```
/data/
  /raw/
    - alipay.csv          (deprecated, GBK encoding issues)
    - raw-wechat.xlsx     (native Chinese format - PREFERRED)
  /processed/
    - transactions.csv                    (normalized, 901 rows)
    - transactions_cleaned.csv            (with 'text' column)
    - transactions_classified.csv         (final classifications)
    - classifier.pkl                      (trained model)
    - tfidf_vectorizer.pkl                (vectorizer)
  /labeled/
    - merchant_rules_expanded.csv         (136 rules)
    - labeled_transactions.csv            (544 training rows)

/src/
  - parse.py                (Stage 1: parsing)
  - segment.py              (Stages 2 & 4: cleaning + vectorization)
  - label.py                (Stage 3: rule-based labeling)
  - train.py                (Stage 5: training)
  - classify.py             (Stage 6: prediction)
  - visualize.py            (Stage 7: charts)
```

## Key Features

- ✅ **Mixed-Language Support**: jieba for Chinese, standard tokenization for English
- ✅ **Dual-Source Normalization**: Handles Alipay CSV + WeChat Excel with different schemas
- ✅ **Smart Labeling**: Rule-based pre-labeling (157 merchant rules, 748 auto-labeled transactions)
- ✅ **Production-Ready**: 97.3% accuracy, 81.4% avg confidence, interpretable Logistic Regression
- ✅ **Full Pipeline**: Parse → Clean → Label → Train → Classify → Visualize
- ✅ **Interactive Dashboard**: Real-time spending analytics, budget alerts, anomaly detection
- ✅ **No "Other" Category**: Every transaction has a meaningful classification

## Technical Highlights

**Why Supervised Classification?**
- Known target categories (10 spending types)
- ~500 transactions needed for good training data
- Interpretability is important for trust

**Why jieba?**
- Chinese has no spaces between words
- Standard tool for Chinese NLP
- Preserves English words as-is

**Why TF-IDF?**
- Simple, fast, interpretable
- Weights distinctive merchant names (Meituan, Taobao, DiDi)
- Outperforms embeddings for this problem size

**Why Logistic Regression?**
- 99.1% accuracy (excellent for category prediction)
- Fast training and inference
- Easy to debug (see which tokens matter)
- Better than complex models for this use case

## Example Usage

```python
import pandas as pd
import joblib
from src.classify import classify_all
from src.segment import clean_text, vectorize

# Load trained models
classifier = joblib.load('data/processed/classifier.pkl')
vectorizer = joblib.load('data/processed/tfidf_vectorizer.pkl')

# Classify new transactions
df_new = pd.read_csv('new_transactions.csv')
df_classified = classify_all(df_new, vectorizer, classifier)

# View results
print(df_classified[['merchant', 'description', 'category', 'confidence']])
```

## Dependencies

```
pandas>=1.5.0
scikit-learn>=1.0.0
jieba>=0.42.1
openpyxl>=3.0.0
matplotlib>=3.5.0
joblib>=1.1.0
```

## Completed Features

- ✅ Rule-based pre-labeling (eliminates manual labeling burden)
- ✅ Streamlit dashboard for real-time spending tracking
- ✅ Budget alerts and spending trends
- ✅ Anomaly detection (unusual merchants/amounts)
- ✅ Monthly spending reports with CSV export

## Future Enhancements

- [ ] Support for other payment platforms (WeChat transfers, Bank exports, etc.)
- [ ] Machine learning model retraining on new labeled data
- [ ] Spending goals and forecasting
- [ ] Multi-year trend analysis
- [ ] Email alerts for budget overages
