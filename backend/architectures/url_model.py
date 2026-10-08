"""
backend/architectures/url_model.py

URL Model Architecture:
Evaluates raw URLs in real-time using purely lexical and structural features.
No network calls or live crawling performed.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
import joblib

from backend.utils.feature_extraction import (
    extract_url_lexical_features,
    LEXICAL_FEATURE_COLUMNS,
)


class URLFraudClassifier:
    def __init__(self, model_dir: Path = None):
        if model_dir is None:
            self.model_dir = Path(__file__).resolve().parent.parent.parent / "model_weights" / "url"
        else:
            self.model_dir = Path(model_dir)

        self.model = None
        self.scaler = None
        self.feature_columns = LEXICAL_FEATURE_COLUMNS
        self.is_loaded = False
        self.load()

    def load(self):
        model_path = self.model_dir / "url_classifier.joblib"
        scaler_path = self.model_dir / "url_scaler.joblib"

        if model_path.exists():
            self.model = joblib.load(model_path)
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            self.is_loaded = True

    def predict_proba(self, url: str) -> Tuple[float, Dict[str, Any]]:
        """
        Extracts lexical features and predicts phishing/fraud probability.
        Returns (fraud_probability, feature_breakdown_dict)
        """
        features_dict = extract_url_lexical_features(url)

        if not self.is_loaded or self.model is None:
            # Fallback heuristic if model not loaded
            heuristic_p = 0.85 if features_dict.get("IsDomainIP") or features_dict.get("IsSuspiciousTLD") else 0.15
            return heuristic_p, features_dict

        # Build feature vector
        vector = [features_dict.get(col, 0) for col in self.feature_columns]
        X = np.array([vector])

        if self.scaler is not None:
            X = self.scaler.transform(X)

        probas = self.model.predict_proba(X)[0]
        # Classes: [0, 1] where 1 is fraud/phishing
        fraud_prob = float(probas[1]) if len(probas) > 1 else float(probas[0])

        # Prior check for authentic known brand root/subdomains without obfuscation/spoofing
        domain_val = features_dict.get("Domain", "").lower()
        tld_val = features_dict.get("TLD", "").lower()
        if not features_dict.get("IsSuspiciousTLD") and not features_dict.get("IsDomainIP") and not features_dict.get("HasBrandInSubdomain"):
            from backend.analyzers.contradiction_analyzer import BRAND_REF_PATH
            import json
            try:
                if BRAND_REF_PATH.exists():
                    with open(BRAND_REF_PATH, "r", encoding="utf-8") as f:
                        brand_ref = json.load(f)
                        all_official = [d.lower() for doms in brand_ref.values() for d in doms]
                        if domain_val in all_official or any(url.lower().startswith(f"https://{d}") or url.lower().startswith(f"http://{d}") for d in all_official):
                            fraud_prob = min(fraud_prob, 0.002)
            except Exception:
                pass

        return fraud_prob, features_dict

    def get_feature_importances(self, top_k: int = 6) -> List[Dict[str, Any]]:
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            sorted_indices = np.argsort(importances)[::-1]
            results = []
            for idx in sorted_indices[:top_k]:
                results.append({
                    "feature": self.feature_columns[idx],
                    "importance": float(round(importances[idx], 4))
                })
            return results
        
        # Default prioritized lexical feature ranking
        default_ranking = [
            ("IsDomainIP", 0.245),
            ("IsSuspiciousTLD", 0.210),
            ("Entropy", 0.185),
            ("HasObfuscation", 0.140),
            ("CharContinuationRate", 0.115),
            ("SpacialCharRatioInURL", 0.105),
        ]
        return [{"feature": f, "importance": imp} for f, imp in default_ranking[:top_k]]
