# Personal Finance Categorizer

An end-to-end machine learning pipeline to automatically categorize personal financial transactions from Alipay and WeChat Pay using supervised text classification.

**Status**: ✅ Complete (Stages 1-7 + Dashboard + ML Audit) | 95.5% Accuracy (stratified CV) | 901 transactions classified | 157 merchant rules | 81.4% avg confidence | **Class-weight optimized**

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

### Key Results (After ML Audit & Optimization)
- **Model Accuracy (stratified CV)**: 95.5% (honest metric — was 99.1% on single split, misleading)
- **F1-weighted**: 0.961 ✅ (up from 0.942)
- **F1-macro (fairness)**: 0.729 ✅ (up from 0.549 — minority categories now included)
- **Transactions Classified**: 901/901 (100%)
- **Mean Confidence**: 81.4% (well-calibrated: 0.824 when correct, 0.417 when wrong)
- **Training Data**: 748 labeled transactions (157 merchant rules)
- **Features**: 246 TF-IDF tokens (jieba-segmented)
- **Class Weight Optimization**: Applied `class_weight='balanced'` + `C=10` — pure win, no tradeoff

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

## ML Audit & Optimization (Session 6)

**Discovery**: Initial 99.1% accuracy claim was based on single train/test split (misleading). Proper stratified cross-validation revealed:
- **Real accuracy: 95.5%** (acceptable, but not 99.1%)
- **Problem: 3 minority categories had 0% recall** (Travel, Other, Utilities & Services)
- **Root cause: Massive class imbalance + no class weighting**

**Fix Applied**: `class_weight='balanced'` + `C=10` to Logistic Regression
- ✅ F1-weighted improved: 0.942 → 0.961
- ✅ F1-macro improved: 0.549 → 0.729 (fairness across all categories)
- ✅ Shopping F1: +9% | Transfers & Gifts F1: +12% | Utilities & Services: Fixed (0% → 100%)
- ✅ **No tradeoff** — both overall accuracy and fairness improved simultaneously

**Current Per-Category Performance**:
| Category | Samples | Recall | Precision | F1 | Status |
|---|---|---|---|---|---|
| Eating Out | 426 | 99%+ | 90%+ | 0.94+ | ✅ Excellent |
| Groceries | 223 | 98% | 99% | 0.985 | ✅ Excellent |
| Transportation | 175 | 98%+ | 100% | 0.99+ | ✅ Excellent |
| Shopping | 50 | 90% | 100% | 0.938 | ✅ Good |
| Transfers & Gifts | 27 | 85% | 89% | 0.909 | ✅ Good |
| Travel | 2 | 0% | 0% | 0.000 | ❌ Needs more data |
| Other | 5 | 0% | 0% | 0.000 | ❌ Needs more data |

**Confidence Calibration**: Well-calibrated and reliable for thresholds
- Correct predictions: avg confidence 0.824
- Wrong predictions: avg confidence 0.417
- **Recommendation**: Route predictions < 0.7 to manual review; use 0.8+ for auto-classification

See `docs/AUDIT_REPORT.md` for full audit details, tuning results, rejection tests, and recommendations.

## Key Features

- ✅ **Mixed-Language Support**: jieba for Chinese, standard tokenization for English
- ✅ **Dual-Source Normalization**: Handles Alipay CSV + WeChat Excel with different schemas
- ✅ **Smart Labeling**: Rule-based pre-labeling (157 merchant rules, 748 auto-labeled transactions)
- ✅ **Optimized Model**: Class-weight balanced Logistic Regression (95.5% CV accuracy, 0.961 F1-weighted, 0.729 F1-macro)
- ✅ **Full Pipeline**: Parse → Clean → Label → Train → Classify → Visualize
- ✅ **Interactive Dashboard**: Real-time spending analytics, budget alerts, anomaly detection
- ✅ **Confidence Thresholds**: Well-calibrated confidence scores for safe auto-classification

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

## Next Steps (From Audit)

**🔴 URGENT (Already Done)**
- ✅ Apply `class_weight='balanced'`, `C=10` to production model (done in this session)
- ✅ Fix tuning script to score by F1-macro not F1-weighted (done in this session)

**🟡 HIGH PRIORITY (Do This Month)**
- [ ] Collect 20-30 samples for Travel (currently 2 → completely broken)
- [ ] Collect 20-30 samples for Other (currently 5 → completely broken)
- [ ] Collect 30-50 more samples for Shopping & Transfers & Gifts (currently 50/20 → thin)
- [ ] Implement confidence threshold filter (only auto-classify if confidence > 0.7-0.8)

**🟢 MEDIUM PRIORITY (Next Quarter)**
- [ ] Monthly tracking of F1-macro (fairness metric, not just accuracy)
- [ ] Re-run tuning pipeline (`src/tune.py`) after each batch of new labels
- [ ] Dashboard confidence filter widget (show/hide predictions by confidence)

**🔵 LOW PRIORITY (Future)**
- [ ] Revisit feature engineering once data reaches 2,000+ samples (more data = more features justified)
- [ ] Automated retraining pipeline
- [ ] Active-learning style review queue
- [ ] Support for other payment platforms (WeChat transfers, Bank exports, etc.)
- [ ] Multi-year trend analysis
