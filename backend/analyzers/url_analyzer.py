"""
backend/analyzers/url_analyzer.py

URL Analyzer:
Runs real-time lexical feature extraction and URL fraud model inference.
"""

from typing import Dict, Any, Optional
from backend.architectures.url_model import URLFraudClassifier


class URLAnalyzer:
    def __init__(self):
        self.classifier = URLFraudClassifier()

    def analyze(self, url: Optional[str]) -> Dict[str, Any]:
        if not url or not str(url).strip():
            return {
                "url": None,
                "fraud_probability": None,
                "lexical_features": None,
                "is_evaluated": False,
                "top_features": []
            }

        url_str = str(url).strip()
        fraud_prob, features_dict = self.classifier.predict_proba(url_str)
        top_features = self.classifier.get_feature_importances(top_k=5)

        return {
            "url": url_str,
            "fraud_probability": round(fraud_prob, 4),
            "lexical_features": features_dict,
            "is_evaluated": True,
            "top_features": top_features
        }
