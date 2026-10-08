"""
backend/architectures/text_model.py

Text Model Architecture:
Combines character-level and word-level TF-IDF feature pipelines with a
calibrated classifier to predict fraud probabilities and identify top risk tokens.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import scipy.sparse as sp
import joblib


class TextFraudClassifier:
    def __init__(self, model_dir: Path = None):
        if model_dir is None:
            self.model_dir = Path(__file__).resolve().parent.parent.parent / "model_weights" / "text"
        else:
            self.model_dir = Path(model_dir)
            
        self.model = None
        self.base_model = None
        self.vectorizer = None
        self.char_vectorizer = None
        self.is_loaded = False
        self.load()

    def load(self):
        calibrated_path = self.model_dir / "text_calibrated_model.joblib"
        base_path = self.model_dir / "text_classifier.joblib"
        vec_path = self.model_dir / "text_vectorizer.joblib"
        char_vec_path = self.model_dir / "text_char_vectorizer.joblib"

        if vec_path.exists():
            self.vectorizer = joblib.load(vec_path)
            if char_vec_path.exists():
                self.char_vectorizer = joblib.load(char_vec_path)
            
            if calibrated_path.exists():
                self.model = joblib.load(calibrated_path)
            elif base_path.exists():
                self.model = joblib.load(base_path)

            if base_path.exists():
                self.base_model = joblib.load(base_path)

            if self.model is not None:
                self.is_loaded = True

    def predict_proba(self, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Returns (fraud_probability, class_probabilities_dict)
        """
        if not self.is_loaded or self.model is None or not self.vectorizer:
            return 0.1, {"legitimate": 0.9, "fraud": 0.1}

        cleaned = [text if isinstance(text, str) else ""]
        word_features = self.vectorizer.transform(cleaned)
        
        if self.char_vectorizer is not None:
            char_features = self.char_vectorizer.transform(cleaned)
            features = sp.hstack([word_features, char_features], format="csr")
        else:
            features = word_features

        classes = list(self.model.classes_) if hasattr(self.model, "classes_") else [0, 1]
        probas = self.model.predict_proba(features)[0]
        
        prob_dict = {str(c): float(p) for c, p in zip(classes, probas)}
        fraud_prob = probas[1] if len(probas) > 1 else probas[0]

        return float(fraud_prob), {"legitimate": round(float(1.0 - fraud_prob), 4), "fraud": round(float(fraud_prob), 4)}

    def explain(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Returns top token contributions based on base linear model weights.
        """
        target_model = self.base_model or self.model
        if not self.is_loaded or target_model is None or not hasattr(target_model, "coef_") or not self.vectorizer:
            return []

        tokens = text.lower().split()
        explanations = []
        vocab = self.vectorizer.vocabulary_

        coefs = target_model.coef_[0] if target_model.coef_.ndim > 1 else target_model.coef_

        seen = set()
        for tok in tokens:
            clean_tok = tok.strip(".,;:!?\"'()[]{}<>#")
            if clean_tok in vocab and clean_tok not in seen:
                idx = vocab[clean_tok]
                if idx < len(coefs):
                    weight = float(coefs[idx])
                    if weight > 0.05:
                        explanations.append({
                            "token": clean_tok,
                            "weight": round(weight, 4),
                            "impact": "fraud_indicator" if weight > 0.3 else "suspicious"
                        })
                        seen.add(clean_tok)

        explanations.sort(key=lambda x: x["weight"], reverse=True)
        return explanations[:top_k]
