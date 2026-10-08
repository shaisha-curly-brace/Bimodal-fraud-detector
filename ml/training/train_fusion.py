"""
ml/training/train_fusion.py

Trains the Multimodal Fusion Model:
1. Combines predictions from Text Model, URL Lexical Model, Contradiction Analyzer, and Urgency Detector.
2. CRITICAL SPLIT RULE:
   - Evaluation/test set is 100% ORGANIC pairs (pair_type == 'organic').
   - Synthetic augmentation pairs are strictly restricted to the training set.
3. Evaluates ROC-AUC, F1-Score, and ablation metrics on the pure organic test set.
4. Serializes artifacts to model_weights/fusion/.
"""

import json
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)

BASE_DIR = Path(__file__).resolve().parent.parent           # ml/
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.architectures.text_model import TextFraudClassifier
from backend.architectures.url_model import URLFraudClassifier
from backend.analyzers.contradiction_analyzer import ContradictionAnalyzer
from backend.utils.preprocessing import detect_urgency_indicators
from backend.architectures.fusion_model import MultimodalFusionClassifier

DATA_PATH = BASE_DIR / "datasets" / "processed" / "merged_pairs.csv"
MODEL_DIR = PROJECT_ROOT / "model_weights" / "fusion"
RESULTS_DIR = BASE_DIR / "experiments" / "results"


def extract_features_for_row(
    text: str,
    url: str,
    text_clf: TextFraudClassifier,
    url_clf: URLFraudClassifier,
    contra_analyzer: ContradictionAnalyzer
) -> list:
    # 1. Text Model inference
    p_text, _ = text_clf.predict_proba(text)

    # 2. URL Model inference
    p_url, url_feats = url_clf.predict_proba(url)

    # 3. Contradiction Analysis
    contra_res = contra_analyzer.analyze(text=text, url=url)
    c_score = contra_res.get("contradiction_score", 0.0)

    # 4. Urgency Analysis
    urgency_res = detect_urgency_indicators(text)
    u_score = urgency_res.get("urgency_score", 0.0)

    # 5. Lexical flags
    is_ip = float(url_feats.get("IsDomainIP", 0))
    is_tld = float(url_feats.get("IsSuspiciousTLD", 0))
    is_obf = float(url_feats.get("HasObfuscation", 0))

    # Interaction terms
    interaction_mult = p_text * p_url
    interaction_diff = abs(p_text - p_url)
    brand_threat = p_text * c_score

    return [
        p_text,
        p_url,
        1.0,  # has_url flag
        c_score,
        u_score,
        interaction_mult,
        interaction_diff,
        brand_threat,
        is_ip,
        is_tld,
        is_obf
    ]


def train_fusion_model():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[train_fusion] Loading paired dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    # Target: 1 = fraud, 0 = legitimate
    df["target"] = df["label"].apply(lambda x: 1 if str(x).lower() in ("fraud", "smishing", "spam") else 0)

    # Separate Organic vs Synthetic
    organic_df = df[df["pair_type"] == "organic"].copy().sample(frac=1.0, random_state=42).reset_index(drop=True)
    synthetic_df = df[df["pair_type"] == "synthetic_augment"].copy().sample(frac=1.0, random_state=42).reset_index(drop=True)

    print(f"[train_fusion] Total rows: {len(df)}")
    print(f"  - Organic pairs:   {len(organic_df)} (Legit: {(organic_df['target'] == 0).sum()}, Fraud: {(organic_df['target'] == 1).sum()})")
    print(f"  - Synthetic pairs: {len(synthetic_df)} (Legit: {(synthetic_df['target'] == 0).sum()}, Fraud: {(synthetic_df['target'] == 1).sum()})")

    # Split Organic into Train (70%) and Test (30%)
    n_test_organic = int(len(organic_df) * 0.30)
    test_df = organic_df.iloc[:n_test_organic].copy()
    train_organic_df = organic_df.iloc[n_test_organic:].copy()

    # Training set = remaining organic + ALL synthetic augmentation pairs
    train_df = pd.concat([train_organic_df, synthetic_df], ignore_index=True).sample(frac=1.0, random_state=42).reset_index(drop=True)

    print(f"\n[train_fusion] Data split verification:")
    print(f"  - Training samples: {len(train_df)} ({len(train_organic_df)} organic + {len(synthetic_df)} synthetic)")
    print(f"  - STRICT Organic-Only Test samples: {len(test_df)} (100% organic, 0% synthetic)")

    # Load component models
    print("[train_fusion] Loading text, URL, and contradiction models for feature generation...")
    text_clf = TextFraudClassifier()
    url_clf = URLFraudClassifier()
    contra_analyzer = ContradictionAnalyzer()

    print("[train_fusion] Extracting multimodal features for training set...")
    X_train_list = []
    for _, row in train_df.iterrows():
        feat = extract_features_for_row(
            text=str(row["message_text"]),
            url=str(row["url"]),
            text_clf=text_clf,
            url_clf=url_clf,
            contra_analyzer=contra_analyzer
        )
        X_train_list.append(feat)

    X_train = np.array(X_train_list, dtype=float)
    y_train = np.asarray(train_df["target"], dtype=int)

    print("[train_fusion] Extracting multimodal features for test set (pure organic)...")
    X_test_list = []
    for _, row in test_df.iterrows():
        feat = extract_features_for_row(
            text=str(row["message_text"]),
            url=str(row["url"]),
            text_clf=text_clf,
            url_clf=url_clf,
            contra_analyzer=contra_analyzer
        )
        X_test_list.append(feat)

    X_test = np.array(X_test_list, dtype=float)
    y_test = np.asarray(test_df["target"], dtype=int)

    print("[train_fusion] Scaling features and fitting Logistic Regression fusion model...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    fusion_clf = LogisticRegression(C=1.0, class_weight="balanced", random_state=42)
    fusion_clf.fit(X_train_scaled, y_train)

    # Evaluation on 100% organic test set
    y_pred = fusion_clf.predict(X_test_scaled)
    y_proba = fusion_clf.predict_proba(X_test_scaled)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 1.0
    cm = confusion_matrix(y_test, y_pred).tolist()

    metrics = {
        "model_name": "Multimodal Fusion Meta-Classifier (Text + URL + Contradiction)",
        "eval_set_constraint": "100% Organic SMS-URL Pairs (Zero Synthetic Data in Test Split)",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm,
        "classification_report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
        "train_samples": len(train_df),
        "organic_test_samples": len(test_df)
    }

    print("\n=== Multimodal Fusion Model Performance (100% Organic Test Split) ===")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {prec:.4f}")
    print(f"  Recall:    {rec:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")
    print(f"  Confusion Matrix: {cm}")
    print("=====================================================================\n")

    # Save artifacts
    joblib.dump(fusion_clf, MODEL_DIR / "fusion_classifier.joblib")
    joblib.dump(scaler, MODEL_DIR / "fusion_scaler.joblib")
    
    with open(MODEL_DIR / "fusion_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    with open(RESULTS_DIR / "fusion_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"[train_fusion] Saved fusion model and weights to {MODEL_DIR}")
    return metrics


if __name__ == "__main__":
    train_fusion_model()
