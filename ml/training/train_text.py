"""
ml/training/train_text.py

Trains the text classification pipeline on cleaned SMS messages:
1. Word-level and character-level TF-IDF feature pipelines.
2. Calibrated classification model with 5-fold cross-validation.
3. Evaluates Precision, Recall, F1-Score, and ROC-AUC.
4. Serializes models and artifacts to model_weights/text/.
"""

import json
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent           # ml/
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = BASE_DIR / "datasets" / "processed" / "cleaned_sms.csv"
MODEL_DIR = PROJECT_ROOT / "model_weights" / "text"
RESULTS_DIR = BASE_DIR / "experiments" / "results"


def train_text_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[train_text] Loading cleaned SMS data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Binary label: 1 = fraud (smishing or spam), 0 = legitimate (ham)
    df["is_fraud"] = df["label"].apply(lambda x: 1 if str(x).lower() in ("smishing", "spam", "fraud") else 0)
    
    texts = np.asarray(df["message_text"].fillna("").astype(str))
    labels = np.asarray(df["is_fraud"], dtype=int)

    print(f"[train_text] Total samples: {len(df)} | Fraud (Spam+Smishing): {int(labels.sum())} | Legitimate (Ham): {int(len(labels) - labels.sum())}")

    # Stratified Train/Test Split (80/20)
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print("[train_text] Fitting Word and Character TF-IDF Vectorizers...")
    word_vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
        strip_accents="unicode"
    )
    X_train_word = word_vec.fit_transform(X_train_raw)
    X_test_word = word_vec.transform(X_test_raw)

    char_vec = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=5000,
        sublinear_tf=True
    )
    X_train_char = char_vec.fit_transform(X_train_raw)
    X_test_char = char_vec.transform(X_test_raw)

    X_train = sp.hstack([X_train_word, X_train_char], format="csr")
    X_test = sp.hstack([X_test_word, X_test_char], format="csr")

    print(f"[train_text] Combined Feature Dimension: {X_train.shape[1]}")

    print("[train_text] Training Calibrated Classifier...")
    base_clf = LogisticRegression(
        C=2.5,
        class_weight="balanced",
        max_iter=1000,
        random_state=42
    )
    
    calibrated_clf = CalibratedClassifierCV(estimator=base_clf, method="sigmoid", cv=5)
    calibrated_clf.fit(X_train, y_train)
    
    # Also fit base_clf directly on full training data to obtain linear coefficients for explainability
    base_clf.fit(X_train, y_train)

    # Evaluation
    y_pred = calibrated_clf.predict(X_test)
    y_proba = calibrated_clf.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_name": "Text Fraud Classifier (Word+Char TF-IDF + Calibrated LR)",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm,
        "classification_report": classification_report(y_test, y_pred, target_names=["Legitimate", "Fraud"], output_dict=True),
        "train_samples": len(X_train_raw),
        "test_samples": len(X_test_raw)
    }

    print("\n=== Text Model Performance on Test Set ===")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")
    print(f"  Confusion Matrix: {cm}")
    print("===========================================\n")

    # Save artifacts
    joblib.dump(base_clf, MODEL_DIR / "text_classifier.joblib")
    joblib.dump(calibrated_clf, MODEL_DIR / "text_calibrated_model.joblib")
    joblib.dump(word_vec, MODEL_DIR / "text_vectorizer.joblib")
    joblib.dump(char_vec, MODEL_DIR / "text_char_vectorizer.joblib")
    
    with open(MODEL_DIR / "text_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(RESULTS_DIR / "text_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[train_text] Saved model and weights to {MODEL_DIR}")
    return metrics


if __name__ == "__main__":
    train_text_model()
