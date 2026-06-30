# Quick Start Guide

## 🚀 One-Time Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (First time only) Place your transaction files in data/raw/
# - Alipay: CSV export (English headers)
# - WeChat: Excel export (.xlsx)
```

## 📊 Run the Complete Pipeline (One-Off)

```bash
# Parse & clean transactions
python src/parse.py

# Label transactions (uses merchant rules)
python src/label.py

# Train classifier
python src/train.py

# Classify all transactions
python src/classify.py

# Generate visualizations
python src/visualize.py

# Launch interactive dashboard
streamlit run src/dashboard.py
```

## 🔄 Monthly Improvement Workflow (5 minutes + labeling time)

```bash
# Step 1: Find the most ambiguous unlabeled transactions
python src/find_other_candidates.py
# Creates: OTHER_CANDIDATES_TO_LABEL.csv

# Step 2: Review the candidates (30-45 minutes)
# - Open OTHER_CANDIDATES_TO_LABEL.csv in Excel
# - Mark ones that belong to "Other" category
# - Save the file

# Step 3: Add labels to training data
# - Copy your labeled rows
# - Paste into data/labeled/labeled_transactions.csv
# - Save

# Step 4: Retrain model (automatic evaluation)
python src/retrain.py
# Creates: TRAINING_REPORT.txt

# Step 5: Classify new transactions
python src/classify.py
# Creates: 
#   - data/processed/transactions_classified.csv
#   - data/processed/needs_manual_review.csv (low-confidence items)
```

## 📈 Monitor Model Performance

After each retraining, check `TRAINING_REPORT.txt`:
- **Accuracy** — should stay 95%+
- **F1-macro** — should be improving (target: > 0.80)
- **Per-category F1** — all categories should be > 0.90

## 🎯 Key Commands Reference

| Task | Command |
|------|---------|
| Find labeling candidates | `python src/find_other_candidates.py` |
| Retrain model | `python src/retrain.py` |
| Classify transactions | `python src/classify.py` |
| View performance | `cat TRAINING_REPORT.txt` |
| Launch dashboard | `streamlit run src/dashboard.py` |

## 📁 Key Files

| File | Purpose |
|------|---------|
| `data/labeled/labeled_transactions.csv` | Your labeled training data (add rows here) |
| `data/processed/transactions_classified.csv` | Final classified output |
| `data/processed/needs_manual_review.csv` | Low-confidence predictions (< 0.70) |
| `TRAINING_REPORT.txt` | Latest model performance metrics |
| `OTHER_CANDIDATES_TO_LABEL.csv` | Candidates for "Other" category labeling |

## 🔧 Troubleshooting

**Model accuracy dropped after retraining?**
- Check `TRAINING_REPORT.txt` — which category got worse?
- Review the transactions you just labeled — might have inconsistent labels
- Add more examples of that category to clarify patterns

**Getting low-confidence warnings?**
- Review `needs_manual_review.csv` — these are edge cases
- Consider adding them to training data if they're a recurring pattern

**Dashboard not loading?**
- Ensure you've run `python src/classify.py` first
- Try: `streamlit run src/dashboard.py --logger.level=debug`

## 📚 Documentation

- **`RETRAINING_WORKFLOW.md`** — Detailed step-by-step guide
- **`CHECKLIST_COMPLETE.md`** — What was built and why
- **`context.md`** — Complete project history
- **`README.md`** — Full architecture and metrics
