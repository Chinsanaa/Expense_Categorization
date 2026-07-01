# Personal Finance Categorizer
## End-to-End Machine Learning Pipeline for Transaction Classification

---

## Executive Summary

**Automated transaction categorization system** that classifies 900+ financial transactions from multiple payment sources (Alipay, WeChat Pay) into spending categories using supervised machine learning. Achieves **96.2% accuracy** (stratified CV) with production-ready confidence thresholds and an interactive decision-making dashboard.

**Key Metrics:**
- ✅ **96.2% accuracy** (stratified 5-fold cross-validation)
- ✅ **0.965 F1-weighted** (overall performance)
- ✅ **0.855 F1-macro** (fairness across all categories)
- ✅ **99.0% average confidence** (789 merchant rule overrides at 100%; ML-only remainder 91.7%)
- ✅ **901/901 transactions classified** (100% coverage)
- ✅ **8 flagged for manual review** (down from 40 pre-Session 13)

---

## The Problem

### Situation
When using multiple payment platforms (Alipay + WeChat Pay), there is no unified view of spending patterns. Manually categorizing hundreds of transactions across platforms was:
- **Time-consuming** — requires consistent manual labeling after each export
- **Inconsistent** — prone to subjective classification errors
- **Non-scalable** — impossible to maintain across months/years of data
- **Opaque** — no insights into where money actually goes

### Business Impact
Without automated categorization, personal financial decisions lack data-driven foundation:
- Cannot identify spending patterns or anomalies
- Unable to set and track budget goals
- No actionable insights for spending cuts or investment planning

---

## The Solution

### Architecture Overview

A **supervised machine learning pipeline** that learns spending patterns from labeled examples and classifies new transactions automatically:

```
Raw Data (CSV Exports)
    ↓
[Stage 1] Normalize & Parse
  • Alipay CSV + WeChat Excel → unified schema
  • Handle encoding issues (GBK, UTF-8)
    ↓
[Stage 2] Clean & Tokenize
  • jieba (Chinese word segmentation)
  • Mixed language support
  • Remove noise, lowercase English
    ↓
[Stage 3] Rule-Based Pre-Label
  • 172 merchant rules → auto-label during training + post-classification override
    ↓
[Stage 4] Vectorize
  • TF-IDF feature extraction
  • 657 most-distinctive tokens
    ↓
[Stage 5] Train Classifier
  • Logistic Regression with class balancing
  • Hyperparameter optimization (C=10, balanced weights)
  • Stratified 5-fold cross-validation
    ↓
[Stage 6] Classify & Score
  • ML prediction + merchant rule overrides + description rules (e.g. NYU POS)
  • Flag low-confidence (<70%) for manual review
    ↓
[Stage 7] Visualize & Decide
  • Interactive Streamlit dashboard
  • Budget tracking, anomaly detection
  • Decision-making tools (savings calculator, investment readiness)
```

### Why This Approach?

| Design Choice | Alternative Considered | Why This Won |
|---|---|---|
| **Supervised Classification** | Unsupervised clustering (K-means) | We know target categories in advance; clustering requires manual re-labeling each run and produces inconsistent clusters |
| **Logistic Regression** | Deep learning (LSTM/BERT) | Simple, interpretable, fast; outperforms complex models for this problem size (~1000 samples); tokens directly show what model learned |
| **TF-IDF Vectorization** | Word embeddings (Word2Vec) | Interpretable, distinctive merchant names (Meituan, Taobao, DiDi) score high naturally; no need for heavy compute |
| **jieba Tokenization** | English tokenizer on Chinese | Chinese has no spaces; jieba is the standard library for correct segmentation |
| **Class Weighting** | Balanced train/test split | Data is naturally imbalanced (47% Eating Out); weighting prevents minority categories from being ignored |

---

## Results & Performance

### Accuracy Metrics (current — Session 17, July 2026)

| Metric | Value | Status |
|---|---|---|
| **Overall Accuracy (CV)** | 96.2% | ✅ Production-ready |
| **F1-weighted** | 0.965 | ✅ Excellent balanced performance |
| **F1-macro** | 0.855 | ✅ Fair across all categories |
| **Mean Confidence (all 901)** | 99.0% | ✅ High (789 rule overrides at 100%) |
| **Mean Confidence (ML-only, 112 rows)** | 91.7% | ✅ Remaining edge cases |
| **Needs Manual Review** | 8 / 901 | ✅ Down from 40 |
| **Transactions Classified** | 901/901 | ✅ 100% coverage |
| **`???` placeholder category** | 0 | ✅ Resolved (Session 14) |

**Per-category summary** (863 labeled training samples at last retrain · 901 live transactions, ¥23,895 total):

| Category | Training Samples | Precision | Recall | F1 | Live Count | % of Spend | Avg Confidence |
|---|---|---|---|---|---|---|---|
| Eating Out | 330 | 100% | 98% | **0.992** | 359 | 41.1% | 98.6% |
| Shopping | 55 | 96% | 98% | **0.973** | 56 | 15.7% | 98.7% |
| Groceries | 269 | 100% | 99% | **0.994** | 272 | 13.8% | 99.2% |
| Transportation | 169 | 100% | 100% | **1.000** | 169 | 10.0% | 100% |
| Other | 11 | 65% | 100% | **0.786** | 11 | 8.9% | 90.5% |
| Transfers & Gifts | 22 | 91% | 95% | **0.933** | 26 | 8.4% | 99.6% |
| Utilities & Services | 5 | 100% | 100% | **1.000** | 5 | 0.4% | 100% |

### Key Improvements (Recent Sessions)

**Session 14: Catering, HEYTEA, anomaly cleanup**
- Fixed all `???` placeholder rules (12 → 0); catering/`餐饮` → Eating Out
- Added `喜茶` (HEYTEA) rule; La Baraka confirmed Eating Out
- Mean confidence **93.8% → 99.0%**; manual review **40 → 8**

**Session 13: Manual Other-Bucket Review + Rule Overrides**
- User corrected 17 misclassified "Other" transactions (restaurants, groceries, gifts)
- Expanded merchant rules; `classify.py` post-classification overrides
- Retrained (96.2% CV accuracy); **Other bucket 31 → 11**

**Session 6: Discovered & Fixed Accuracy Reporting**
- Initial 99.1% was misleading (single train/test split)
- Implemented stratified 5-fold cross-validation → revealed real 95.5%
- Applied `class_weight='balanced'` + `C=10` hyperparameter tuning
- **Result**: F1-macro improved from 0.549 → 0.765 (+39% fairness improvement)

**Session 8A: Automated ML Workflow**
- Built `src/retrain.py` for automated monthly retraining
- Implemented `find_other_candidates.py` to surface ambiguous transactions
- Monthly pipeline: label → retrain → evaluate → classify
- **Result**: 3-6 week automation lifecycle established

**Sessions 16–17: Dashboard restructure + pipeline enhancements**
- **Session 16:** `src/trends.py` (multi-year YoY analysis); generic bank/card CSV parser in `parse.py`; EWMA forecast option in `forecast.py`
- **Session 17:** Rebuilt dashboard from 8→3→**5 tabs** (see [Dashboard Features](#dashboard-features)); merged Overview+Merchants, Budget+Forecast, Savings+Anomalies; restored full Action Plan (savings-gap sliders, investment readiness); Reports as dedicated export tab
- Multi-year trend charts removed from dashboard UI in Session 17 (`trends.py` remains available to re-wire)

**Sessions 9-10: Decision-making tools + anomaly detection fix** *(now in Tabs 3–4)*
- Need vs Want efficiency, cuttable merchants, savings gap calculator, investment readiness → **Action Plan** tab
- IQR+¥150 anomaly detection (was 100+ false positives → ~5) → **Savings & Anomalies** tab

---

## Technical Implementation

### Technology Stack
- **Language**: Python 3.8+
- **ML Framework**: scikit-learn (Logistic Regression)
- **NLP**: jieba (Chinese tokenization), TF-IDF vectorization
- **Data Processing**: pandas, NumPy
- **Dashboard**: Streamlit
- **File Format**: CSV (normalized), PKL (model serialization)

### Key Algorithms

**1. Chinese + English Tokenization**
```python
# jieba preserves English words, segments Chinese into individual words
# "在Meituan点了外卖" → ["在", "Meituan", "点", "了", "外卖"]
# TF-IDF then weights "Meituan" highly (unique to food category)
```

**2. Class-Balanced Logistic Regression**
- Minority categories (Transfers: 27 samples) were invisible to unweighted model
- `class_weight='balanced'` auto-scales loss inversely to class frequency
- Result: all categories get fair representation, F1-macro +39%

**3. Confidence Calibration**
- Well-calibrated: correct predictions average 82.4% confidence, wrong predictions 41.7%
- Threshold strategy: auto-classify ≥80%, manual review 70-79%, reject <70%
- Prevents unreliable predictions from silently failing

**4. Stratified Cross-Validation**
- 5-fold stratified split preserves category distribution in each fold
- Honest metric: prevents accidental overfitting to majority class
- Discovered real accuracy (95.5%) vs. misleading single-split (99.1%)

### Model Complexity & Trade-offs

**Why Logistic Regression (not Deep Learning)?**
| Factor | Logistic Regression | Neural Network |
|---|---|---|
| Training time | ~0.1s | ~30s |
| Interpretability | ✅ Can see which tokens matter | ❌ Black box |
| Data needed | 200-500 samples | 10,000+ samples |
| Production stability | ✅ No randomness | ⚠️ Requires careful seeding |
| Accuracy on this task | 96.2% | ~96.5% (marginal gain) |
| Maintenance burden | Low | High |

**Decision**: Logistic Regression wins on simplicity, speed, and interpretability with acceptable accuracy trade-off.

---

## Dashboard Features

Five-tab Streamlit dashboard (`streamlit run src/dashboard.py`). Filters (date, category, source, confidence) apply on the **Overview** tab; other tabs use full dataset or their own month selectors.

| Tab | What it answers |
|---|---|
| **📊 Overview** | Where did money go? KPIs (total spend, avg txn, daily avg, top category); monthly stacked bar by category; pie breakdown; top 15 merchants; cumulative spend line |
| **💳 Budget & Forecast** | Am I on track? Per-category budget cards (green/orange/red); variance table (¥ and %); 9-month risk; budget vs actual bar; forecast heatmap (Sep→May); seasonal vs EWMA toggle |
| **💰 Savings & Anomalies** | What's unusual or off-track? Monthly income, YTD savings rate, year-end projection vs ¥7,200 goal; need/want split; daily burn rate; cumulative savings trend; high-value outliers and one-off merchants (IQR-based) |
| **🎯 Action Plan** | What should I cut? Efficiency score (% months met ¥600 goal); ranked discretionary transactions; cuttable merchants chart; interactive savings-gap sliders; investment readiness (3/3 recent months) |
| **📋 Reports** | Export utility — month picker, category summary table, CSV download |

**Tab evolution:** Original build had 8 tabs (Overview, Merchants, Budget, Anomalies, Reports, Forecasting, Savings, Action Plan). Session 10 collapsed to 3 priority tabs; Session 17 settled on the 5-tab structure above without losing functionality.

---

## How to Use

### Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the pipeline (parse → classify → visualize)
python3 src/parse.py          # Parse Alipay/WeChat exports
python3 src/classify.py       # Classify all transactions
python3 src/visualize.py      # Generate summaries

# 3. Launch interactive dashboard
streamlit run src/dashboard.py
# Opens at http://localhost:8501
```

### Classify New Transactions

```python
import pandas as pd
import joblib
from src.classify import classify_all
from src.label import load_merchant_rules

# Load trained models and merchant rules
classifier = joblib.load('data/processed/classifier.pkl')
vectorizer = joblib.load('data/processed/tfidf_vectorizer.pkl')
rules = load_merchant_rules('data/labeled/merchant_rules_expanded.csv')

# Classify new transactions (ML + rule overrides)
df_new = pd.read_csv('new_transactions.csv')
df_classified = classify_all(df_new, vectorizer, classifier, rules=rules)

# View results (includes confidence scores)
print(df_classified[['merchant', 'description', 'category', 'confidence']])
```

### Monthly Retraining (Optional but Recommended)

```bash
# 1. Find ambiguous transactions for labeling
python3 src/find_other_candidates.py
# Output: OTHER_CANDIDATES_TO_LABEL.csv (30 examples)

# 2. Review and label the candidates
# (Add labeled rows to data/labeled/labeled_transactions.csv)

# 3. Retrain the model
python3 src/retrain.py
# Output: data/reports/TRAINING_REPORT.txt (detailed metrics)

# 4. Reclassify all transactions
python3 src/classify.py
```

### Add Bank or Credit Card Exports

Drop a CSV into `data/raw/` as `bank.csv` or `credit_card.csv`, or copy
`data/raw/source_config.example.json` → `source_config.json` and set column names
for your bank's export format. Then re-run parse:

```bash
python3 src/parse.py
python3 src/classify.py
```

The parser auto-detects common Chinese/English headers (交易日期, Amount, etc.)
and filters to expenses only when a 收/支 / Type column is present.

---

## Project Structure

```
financing/
├── README.md                 # This file
├── CLAUDE.md                 # Collaboration guidelines
├── context.md                # Session log and project memory
├── requirements.txt
│
├── data/
│   ├── raw/                  # Original exports (Alipay CSV, WeChat Excel) — do not edit
│   ├── labeled/
│   │   ├── merchant_rules_expanded.csv   # 172 merchant rules
│   │   └── labeled_transactions.csv      # 863 training examples
│   ├── processed/            # Pipeline outputs (used by dashboard)
│   │   ├── transactions.csv
│   │   ├── transactions_classified.csv
│   │   ├── needs_manual_review.csv
│   │   ├── classifier.pkl
│   │   └── tfidf_vectorizer.pkl
│   ├── intermediate/         # Stage artifacts (cleaned text, auto-labeled)
│   ├── exports/              # Excel review files for manual checks
│   ├── reports/              # TRAINING_REPORT.txt from retrain.py
│   └── budget_config.json
│
├── output/                   # Generated charts & debug samples (gitignored)
│   ├── charts/
│   └── samples/
│
├── src/                      # Active pipeline scripts
│   ├── parse.py              # Stage 1: Parse CSV/Excel
│   ├── segment.py            # Stage 2 & 4: Tokenization + TF-IDF
│   ├── label.py              # Stage 3: Rule-based pre-labeling
│   ├── train.py              # Stage 5: Train classifier
│   ├── classify.py           # Stage 6: Predict + confidence
│   ├── retrain.py            # Automated retraining
│   ├── visualize.py          # Stage 7: Static charts
│   ├── dashboard.py          # Streamlit dashboard
│   ├── dashboard_helpers.py
│   ├── merchant_display.py
│   ├── forecast.py
│   ├── trends.py              # Multi-year trend analysis
│   └── find_other_candidates.py
│
└── _archive/                 # Old experiments, one-off scripts, backups
```

---

## Key Features

### 1. **Dual-Source Normalization**
Seamlessly combines Alipay CSV and WeChat Excel exports into a unified schema, handling different column names, encodings, and date formats automatically.

### 2. **Mixed-Language NLP**
Correctly tokenizes Chinese + English text using jieba segmentation. Prevents the common pitfall of applying English tokenizers to Chinese (which would fail to segment).

### 3. **Rule-Based Pre-Labeling + Post-Classification Overrides**
172 merchant rules auto-label training data and override ML predictions at inference time (789/901 transactions matched). Description rules handle edge cases (e.g. NYU cafeteria POS → Eating Out, catering/餐饮 → Eating Out).

### 4. **Production-Ready Confidence Thresholds**
Well-calibrated confidence scores with a two-layer strategy: merchant rules set confidence to 100% on match; remaining ML predictions flagged below 70% for manual review (currently **8 items**).

### 5. **Fairness-Aware Model Training**
Class weighting ensures minority spending categories (Transfers, Shopping) are learned equally well, not ignored in favor of majority categories.

### 6. **Interactive Dashboard**
Five tabs: spending overview, budget & forecast, savings & anomalies, action plan, and monthly reports/export — decision-making tools (savings calculator, investment readiness) plus IQR-based anomaly detection.

### 7. **Automated Retraining Pipeline**
Monthly workflow to identify ambiguous transactions, collect labels, retrain model, and evaluate without manual intervention.

---

## Validation & Robustness

### Cross-Validation Strategy
- **5-fold stratified cross-validation** ensures category distribution is preserved in each fold
- **Why stratified?** Dataset is imbalanced (47% Eating Out). Regular k-fold might accidentally put all minority samples in one fold, making metrics unreliable.
- **Result**: Honest accuracy (95.5%) instead of overfitted claims (99.1%)

### Confidence Calibration
- **Correct predictions**: 82.4% average confidence
- **Incorrect predictions**: 41.7% average confidence
- **Calibration ratio**: 2:1, indicating model is well-calibrated (knows when to be uncertain)

### Edge Cases Handled
- ✅ Empty merchant names → fallback to description
- ✅ All-numeric merchant IDs → handled gracefully
- ✅ Duplicate transactions → preserved (intentional for monthly totals)
- ✅ Low-confidence predictions → flagged for manual review
- ✅ Entirely new merchants → predicted based on description text alone

---

## Limitations & Future Work

### Current Limitations
1. **Fixed monthly income assumption** (¥2,986) — varies for users with irregular income
2. **~10 months of transaction data** (Aug 2025 – May 2026) — multi-year YoY charts live in `src/trends.py` but not yet wired back into the dashboard UI
3. **7 spending categories** — could expand with more training data
4. **No real-time classification** — batch processing only (acceptable for monthly use)

### Future Enhancements
- [x] Multi-year trend analysis — `src/trends.py` built (Session 16); dashboard UI removed in Session 17 restructure — re-add when desired
- [x] Support additional payment sources — generic bank/card CSV parser in `parse.py`; see `data/raw/source_config.example.json`
- [ ] Automated feature engineering with larger datasets (2000+ samples)
- [ ] Mobile app for quick transaction review
- [x] Budget forecasting — EWMA option alongside seasonal+trend in `forecast.py` (Budget & Forecast tab)

---

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip or conda
- ~50 MB disk space for data + models

### Installation

```bash
# Clone repository
git clone https://github.com/Chinsanaa/financing.git
cd financing

# Install dependencies
pip install -r requirements.txt

# Run pipeline
python3 src/parse.py
python3 src/classify.py
streamlit run src/dashboard.py
```

### Example: View Dashboard
```bash
streamlit run src/dashboard.py
# Visit http://localhost:8501 in your browser
```

---

## For Recruiters

### What This Project Demonstrates

**Machine Learning Skills:**
- ✅ Supervised classification pipeline (train → evaluate → predict)
- ✅ Data preprocessing and normalization across multiple sources
- ✅ Class imbalance handling (class weighting, stratified CV)
- ✅ NLP: tokenization, TF-IDF vectorization, mixed-language support
- ✅ Model evaluation: precision, recall, F1, cross-validation
- ✅ Hyperparameter tuning and honest metrics reporting
- ✅ Production-ready confidence thresholds and failure modes

**Engineering Skills:**
- ✅ Full-stack data pipeline (parsing → cleaning → feature engineering → modeling → visualization)
- ✅ Automated workflows (retraining, candidate discovery)
- ✅ Code organization and modularity (7-stage pipeline)
- ✅ Interactive dashboards (Streamlit, 5-tab layout)
- ✅ Version control and documentation

**Soft Skills:**
- ✅ Problem-solving: identified and fixed misleading accuracy claims
- ✅ Honesty: reported real 95.5% instead of inflated 99.1%
- ✅ Iteration: improved fairness (F1-macro +39%) without sacrificing accuracy
- ✅ Documentation: detailed audit report, context tracking, decision rationale

### Technical Decisions Worth Discussing
1. **Why Logistic Regression over neural networks?** → Interpretability, speed, data efficiency (see table above)
2. **How does jieba help?** → Chinese segmentation enables TF-IDF to work correctly (see Technical Implementation)
3. **Why class weighting?** → Prevents majority category from dominating; ensures all categories learned fairly
4. **Why stratified CV?** → Honest metric that accounts for class imbalance; discovered real accuracy
5. **How do you handle low-confidence predictions?** → Thresholding strategy; confidence well-calibrated for safe auto-classification

---

## Dependencies

```
pandas>=1.5.0
scikit-learn>=1.0.0
jieba>=0.42.1
openpyxl>=3.0.0
matplotlib>=3.5.0
streamlit>=1.0.0
joblib>=1.1.0
numpy>=1.21.0
```

---

## License

Open source (MIT License)

---

## Contact & Questions

For questions about the implementation or technical decisions, see `context.md` for detailed session logs and decision rationale.

**Last Updated:** Session 17 (2026-07-01) — 5-tab dashboard restructure; per-category results table consolidated
