"""Train and evaluate Logistic Regression classifier."""
import pandas as pd
import numpy as np
import sys
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import joblib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from segment import vectorize


def train_classifier(X_train, y_train):
    """Train Logistic Regression classifier."""
    clf = LogisticRegression(
        max_iter=1000,
        random_state=42,
        multi_class='multinomial',
        solver='lbfgs'
    )
    clf.fit(X_train, y_train)
    return clf


def evaluate_classifier(clf, X_test, y_test, categories):
    """Evaluate classifier and print metrics."""
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*70}")
    print(f"MODEL EVALUATION")
    print(f"{'='*70}")
    print(f"\nAccuracy: {accuracy:.3f} ({100*accuracy:.1f}%)")

    print(f"\n{'CONFUSION MATRIX':^70}")
    print("-" * 70)
    cm = confusion_matrix(y_test, y_pred, labels=categories)

    # Print confusion matrix
    header = "       " + "".join([f"{cat[:4]:>6s}" for cat in categories])
    print(header)
    for i, cat in enumerate(categories):
        row = f"{cat[:6]:6s}"
        for j in range(len(categories)):
            row += f"{cm[i, j]:6d}"
        print(row)

    print(f"\n{'CLASSIFICATION REPORT':^70}")
    print("-" * 70)
    report = classification_report(y_test, y_pred, target_names=categories, digits=3)
    print(report)

    # Save detailed report to file
    with open('_training_report.txt', 'w', encoding='utf-8') as f:
        f.write("STAGE 5: CLASSIFIER TRAINING & EVALUATION\n")
        f.write("="*80 + "\n\n")
        f.write(f"Model: Logistic Regression\n")
        f.write(f"Accuracy: {accuracy:.3f} ({100*accuracy:.1f}%)\n\n")
        f.write("CONFUSION MATRIX:\n")
        f.write(header + "\n")
        for i, cat in enumerate(categories):
            row = f"{cat[:6]:6s}"
            for j in range(len(categories)):
                row += f"{cm[i, j]:6d}"
            f.write(row + "\n")
        f.write("\n" + report)

    return accuracy, y_pred


def show_predictions(clf, X_test, y_test, categories, n=10):
    """Show sample predictions with confidence."""
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)

    print(f"\n{'='*70}")
    print(f"SAMPLE PREDICTIONS (first {n})")
    print(f"{'='*70}")

    # Get indices where prediction is correct and incorrect
    correct_mask = y_pred == y_test
    incorrect_indices = np.where(~correct_mask)[0]
    correct_indices = np.where(correct_mask)[0]

    # Show some correct and some incorrect
    indices = list(correct_indices[:5]) + list(incorrect_indices[:5])
    indices = indices[:n]

    with open('_sample_predictions.txt', 'w', encoding='utf-8') as f:
        f.write("SAMPLE PREDICTIONS\n")
        f.write("="*80 + "\n\n")

        for idx in indices:
            true_label = y_test.iloc[idx]
            pred_label = y_pred[idx]
            confidence = y_proba[idx].max()
            match = "✓" if true_label == pred_label else "✗"

            f.write(f"{match} True: {true_label:25s} | Pred: {pred_label:25s} | Conf: {confidence:.2%}\n")

    return indices


if __name__ == '__main__':
    print("="*70)
    print("STAGE 5: TRAIN & EVALUATE CLASSIFIER")
    print("="*70)

    # Load data
    df_labeled = pd.read_csv('data/labeled/labeled_transactions.csv')
    vectorizer = joblib.load('data/processed/tfidf_vectorizer.pkl')

    print(f"\n1. Loaded {len(df_labeled)} labeled transactions")

    # Vectorize
    X = vectorize(df_labeled['text'].tolist(), vectorizer)
    y = df_labeled['category']

    print(f"2. Vectorized to shape {X.shape}")

    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"3. Split data: {len(X_train)} train, {len(X_test)} test")

    # Train classifier
    print(f"4. Training Logistic Regression...")
    clf = train_classifier(X_train, y_train)
    print(f"   Done!")

    # Evaluate
    categories = sorted(y.unique())
    accuracy, y_pred = evaluate_classifier(clf, X_test, y_test, categories)

    # Show predictions
    show_predictions(clf, X_test, y_test, categories, n=10)

    # Save classifier
    clf_path = 'data/processed/classifier.pkl'
    joblib.dump(clf, clf_path)
    print(f"\n5. Saved classifier to {clf_path}")

    print(f"\n{'='*70}")
    if accuracy >= 0.80:
        print(f"SUCCESS! Accuracy {100*accuracy:.1f}% - Ready for production")
    elif accuracy >= 0.70:
        print(f"ACCEPTABLE: Accuracy {100*accuracy:.1f}% - Consider data augmentation")
    else:
        print(f"NEEDS WORK: Accuracy {100*accuracy:.1f}% - May need more training data or features")
    print(f"{'='*70}")
