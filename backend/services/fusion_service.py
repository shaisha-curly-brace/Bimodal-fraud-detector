"""
backend/services/fusion_service.py

Fusion Service:
Encapsulates multimodal decision making and combines text, URL, and contradiction scores.
"""

from typing import Dict, Any, Optional
from backend.architectures.fusion_model import MultimodalFusionClassifier


class FusionService:
    def __init__(self):
        self.fusion_classifier = MultimodalFusionClassifier()

    def evaluate_fusion(
        self,
        text_result: Dict[str, Any],
        url_result: Dict[str, Any],
        contradiction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        p_text = text_result.get("fraud_probability", 0.0)
        p_url = url_result.get("fraud_probability") if url_result and url_result.get("is_evaluated") else None
        urgency_info = text_result.get("urgency_analysis", {})
        url_features = url_result.get("lexical_features") if url_result else None

        return self.fusion_classifier.predict(
            p_text=p_text,
            p_url=p_url,
            contradiction_info=contradiction_result,
            urgency_info=urgency_info,
            url_features=url_features
        )
