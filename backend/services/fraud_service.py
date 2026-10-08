"""
backend/services/fraud_service.py

Master Fraud Detection Service (Text + URL):
Orchestrates text analysis, URL lexical inspection, contradiction analysis,
bimodal fusion, and explainability generation for end-to-end evaluation.
"""

from typing import Dict, Any, Optional
from backend.analyzers.text_analyzer import TextAnalyzer
from backend.analyzers.url_analyzer import URLAnalyzer
from backend.analyzers.contradiction_analyzer import ContradictionAnalyzer
from backend.services.fusion_service import FusionService
from backend.services.explanation_service import ExplanationService
from backend.utils.logger import logger


class FraudService:
    def __init__(self):
        logger.info("Initializing Bimodal Fraud Service components (Text + URL)...")
        self.text_analyzer = TextAnalyzer()
        self.url_analyzer = URLAnalyzer()
        self.contradiction_analyzer = ContradictionAnalyzer()
        self.fusion_service = FusionService()
        self.explanation_service = ExplanationService()
        logger.info("Bimodal Fraud Service ready.")

    def run_pipeline(self, text: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Master bimodal pipeline execution:
        1. Text analysis & token highlighting
        2. Target URL resolution
        3. Lexical URL analysis
        4. Cross-modal contradiction & brand mismatch detection
        5. Multimodal decision fusion
        6. Explainability and evidence synthesis
        """
        return self.analyze_message(text=text, url=url)

    def analyze_message(self, text: str, url: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes an incoming message text and/or explicit URL.
        If URL is not explicitly passed, extracts it from the text automatically.
        """
        # 1. Text Analysis
        text_result = self.text_analyzer.analyze(text)

        # 2. Determine target URL (explicitly provided or auto-extracted from text)
        target_url = url.strip() if (url and url.strip()) else text_result.get("extracted_url")

        # 3. URL Lexical Analysis
        url_result = self.url_analyzer.analyze(target_url)

        # 4. Cross-Modal Contradiction Analysis
        contradiction_result = self.contradiction_analyzer.analyze(
            text=text_result.get("cleaned_text", ""),
            url=target_url
        )

        # 5. Bimodal Decision Fusion Evaluation
        risk_result = self.fusion_service.evaluate_fusion(
            text_result=text_result,
            url_result=url_result,
            contradiction_result=contradiction_result
        )

        # 6. Generate Explainability and Actionable Recommendations
        explanation = self.explanation_service.generate_explanation(
            risk_result=risk_result,
            text_result=text_result,
            url_result=url_result,
            contradiction_result=contradiction_result
        )

        return {
            "risk_score": risk_result["risk_score"],
            "risk_tier": risk_result["risk_tier"],
            "risk_color": risk_result["risk_color"],
            "verdict": risk_result["verdict"],
            "modality_breakdown": risk_result["modality_breakdown"],
            "text_analysis": text_result,
            "url_analysis": url_result,
            "contradiction_analysis": contradiction_result,
            "explanation": explanation,
            "input_metadata": {
                "has_text": bool(text and text.strip()),
                "has_url": bool(target_url),
                "url_source": "explicit" if (url and url.strip()) else ("extracted" if text_result.get("extracted_url") else "none")
            }
        }

    def analyze_url_only(self, url: str) -> Dict[str, Any]:
        """Direct analysis of a URL string."""
        return self.analyze_message(text="", url=url)
