"""
backend/analyzers/text_analyzer.py

Text Analyzer:
Coordinates text cleaning, urgency analysis, token highlighting,
and text model inference.
"""

from typing import Dict, Any, Optional
from backend.architectures.text_model import TextFraudClassifier
from backend.utils.preprocessing import (
    clean_sms_text,
    extract_url_from_text,
    detect_urgency_indicators,
    highlight_suspicious_tokens
)


class TextAnalyzer:
    def __init__(self):
        self.classifier = TextFraudClassifier()

    def analyze(self, text: str) -> Dict[str, Any]:
        cleaned_text = clean_sms_text(text)
        if not cleaned_text:
            return {
                "cleaned_text": "",
                "fraud_probability": 0.0,
                "class_probabilities": {"legitimate": 1.0, "fraud": 0.0},
                "urgency_analysis": {"urgency_score": 0.0, "matched_keywords": [], "has_otp_request": False},
                "tokens": [],
                "explanations": [],
                "extracted_url": None
            }

        extracted_url = extract_url_from_text(cleaned_text)
        urgency_info = detect_urgency_indicators(cleaned_text)
        fraud_prob, class_probs = self.classifier.predict_proba(cleaned_text)
        tokens_highlighted = highlight_suspicious_tokens(cleaned_text)
        explanations = self.classifier.explain(cleaned_text, top_k=5)

        return {
            "cleaned_text": cleaned_text,
            "fraud_probability": round(fraud_prob, 4),
            "class_probabilities": class_probs,
            "urgency_analysis": urgency_info,
            "tokens": tokens_highlighted,
            "explanations": explanations,
            "extracted_url": extracted_url
        }
