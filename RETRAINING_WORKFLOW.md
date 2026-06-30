# Automated Retraining Workflow

This guide explains how to use the automated tools for labeling new data and retraining the model.

## Quick Start: 3-Step Workflow

### Step 1: Find candidates for "Other" category
```bash
cd /path/to/financing
python src/find_other_candidates.py
```
This creates `OTHER_CANDIDATES_TO_LABEL.csv` with 30 most-ambiguous transactions.

**What to do:**
- Open `OTHER_CANDIDATES_TO_LABEL.csv` in a spreadsheet
- Review each transaction
- Mark the ones you think belong to "Other" category (edit their `category` column)
- Save changes

### Step 2: Add labeled data to training set
Copy the rows you labeled as "Other" to `data/labeled/labeled_transactions.csv`:

**Option A: Manual (spreadsheet)**
1. Open `OTHER_CANDIDATES_TO_LABEL.csv` 
2. Copy rows you want to add
3. Paste into `data/labeled/labeled_transactions.csv` (keep the same columns)
4. Save

**Option B: Script** (if you mark rows with category="Other" in the candidates file):
```bash
python src/merge_labeled_data.py  # (to be created if needed)
```

### Step 3: Retrain the model
```bash
python src/retrain.py
```

This will:
- Load all labeled data from `data/labeled/labeled_transactions.csv`
- Train Logistic Regression with class weights
- Evaluate via 5-fold stratified cross-validation
- Show per-category F1, Recall, Precision
- Save updated model to `data/processed/classifier.pkl`
- Generate `TRAINING_REPORT.txt` with detailed metrics

## What Gets Saved

After retraining:
- ✅ `data/processed/classifier.pkl` — Updated trained model
- ✅ `data/processed/tfidf_vectorizer.pkl` — Updated TF-IDF vectorizer
- ✅ `TRAINING_REPORT.txt` — Performance metrics and per-category breakdown

## Classifying New Transactions

Once you've retrained, classify new transaction CSVs:

```bash
python src/classify.py
```

This creates:
- `data/processed/transactions_classified.csv` — All classified transactions
- `data/processed/needs_manual_review.csv` — Low-confidence predictions (< 0.70)

## Confidence Thresholds

The classifier now flags low-confidence predictions:
- **Confidence > 0.70:** Auto-classified (safe)
- **Confidence < 0.70:** Flagged for manual review

These are saved to `needs_manual_review.csv` for you to double-check.

## Monitoring Performance

After each retraining, check:
1. **F1-macro** — Overall fairness (target: > 0.70)
2. **Per-category recall** — Make sure no category drops below 80%
3. **needs_manual_review.csv** — Should shrink over time

If performance drops, you may have:
- Labeled ambiguous transactions inconsistently
- Introduced a new category pattern the model hasn't seen

Just review the misclassified items and add more examples of that pattern.

## Common Scenarios

**Scenario 1: "Other" is still 0% F1**
- You need more examples (target: 15-20)
- Review `OTHER_CANDIDATES_TO_LABEL.csv` more carefully
- Look for transactions that don't fit any category

**Scenario 2: F1-macro dropped after labeling**
- Check `TRAINING_REPORT.txt` — which category got worse?
- Review the transactions you just labeled — might have inconsistent labels
- Add a few more examples to clarify that category

**Scenario 3: Confident but wrong classifications**
- These are hard — the model learned a strong but incorrect pattern
- Find 3-5 merchant rules that contradict the model and add them to `merchant_rules.csv`
- Retrain and see if performance improves

## File Structure

```
data/labeled/
  labeled_transactions.csv        ← Add your labeled data here
  merchant_rules.csv              ← Override rules (backup mechanism)
  
data/processed/
  classifier.pkl                  ← Model file (updated on retrain)
  tfidf_vectorizer.pkl            ← Feature vectorizer (updated on retrain)
  transactions_classified.csv      ← Results of classify.py
  needs_manual_review.csv         ← Low-confidence predictions
  
src/
  find_other_candidates.py        ← Find labeling candidates
  retrain.py                      ← Retrain model
  classify.py                     ← Classify new transactions
  
OTHER_CANDIDATES_TO_LABEL.csv    ← Edit this, then merge into labeled_transactions.csv
TRAINING_REPORT.txt              ← Performance metrics after retrain
```

## Tips

- **Batch labeling:** Find 10-15 candidates, label them, retrain once (not one at a time)
- **Consistency matters:** If you label "Lunch at home" as "Eating Out", label similar items the same way
- **Trust the model:** If confidence is > 0.80, it's probably correct
- **Focus on "Other":** That's the weakest category; prioritize labeling those candidates
