"""
backend/architectures/fusion_model.py

Multimodal Fusion Model Architecture:
Combines text probability, URL probability, contradiction signals, and lexical risks
into a unified calibrated multimodal risk score (0-100) and risk tier.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import joblib


class MultimodalFusionClassifier:
    def __init__(self, model_dir: Path = None):
        if model_dir is None:
            self.model_dir = Path(__file__).resolve().parent.parent.parent / "model_weights" / "fusion"
        else:
            self.model_dir = Path(model_dir)

        self.model = None
        self.scaler = None
        self.is_loaded = False
        self.load()

    def load(self):
        model_path = self.model_dir / "fusion_classifier.joblib"
        scaler_path = self.model_dir / "fusion_scaler.joblib"
        if model_path.exists():
            self.model = joblib.load(model_path)
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
            self.is_loaded = True

    def build_fusion_features(
        self,
        p_text: float,
        p_url: Optional[float],
        contradiction_score: float,
        urgency_score: float,
        is_ip: int = 0,
        is_suspicious_tld: int = 0,
        has_obfuscation: int = 0,
    ) -> np.ndarray:
        """Constructs vector of multimodal interaction features."""
        p_u = p_url if p_url is not None else 0.0
        has_url = 1.0 if p_url is not None else 0.0
        
        interaction_mult = p_text * p_u
        interaction_diff = abs(p_text - p_u)
        brand_threat = p_text * contradiction_score
        
        vec = [
            p_text,
            p_u,
            has_url,
            contradiction_score,
            urgency_score,
            interaction_mult,
            interaction_diff,
            brand_threat,
            float(is_ip),
            float(is_suspicious_tld),
            float(has_obfuscation)
        ]
        return np.array([vec])

    def predict(
        self,
        p_text: float,
        p_url: Optional[float],
        contradiction_info: Dict[str, Any],
        urgency_info: Dict[str, Any],
        url_features: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculates calibrated multimodal risk score, risk level, and modality breakdown.
        """
        c_score = contradiction_info.get("contradiction_score", 0.0)
        u_score = urgency_info.get("urgency_score", 0.0)
        
        is_ip = 1 if url_features and url_features.get("IsDomainIP") else 0
        is_tld = 1 if url_features and url_features.get("IsSuspiciousTLD") else 0
        is_obf = 1 if url_features and url_features.get("HasObfuscation") else 0

        X = self.build_fusion_features(
            p_text=p_text,
            p_url=p_url,
            contradiction_score=c_score,
            urgency_score=u_score,
            is_ip=is_ip,
            is_suspicious_tld=is_tld,
            has_obfuscation=is_obf
        )

        if self.is_loaded and self.model is not None:
            if self.scaler is not None:
                X_scaled = self.scaler.transform(X)
            else:
                X_scaled = X
            raw_p = float(self.model.predict_proba(X_scaled)[0][1])
        else:
            # Fallback fusion rule
            if p_url is not None:
                raw_p = (0.45 * p_text) + (0.45 * p_url) + (0.10 * c_score)
            else:
                raw_p = (0.80 * p_text) + (0.20 * u_score)

        # Safety Overrides for critical indicators
        brand_mismatch = contradiction_info.get("brand_mismatch_detected", False)
        detected_brand = contradiction_info.get("detected_brand")
        actual_domain = contradiction_info.get("actual_domain")
        official_domains = contradiction_info.get("official_domains", [])
        
        # High-risk panic/threat keywords that override brand legitimacy
        has_severe_panic = any(kw in urgency_info.get("matched_keywords", []) for kw in ["suspended", "unauthorized", "locked", "compromised", "action required", "fake", "arrest"])
        has_otp = urgency_info.get("has_otp_request", False)

        # 1. Confirmed official brand domain with standard notification (authentic)
        if detected_brand and not brand_mismatch and c_score == 0.0 and (p_url is not None and p_url < 0.15) and not has_severe_panic and not has_otp:
            raw_p = min(raw_p, 0.05)
            
        # 2. Severe brand impersonation cannot be masked by innocuous words
        elif brand_mismatch:
            raw_p = max(raw_p, 0.88)
            
        # 3. High confidence phishing URL cannot be vetoed by benign text
        elif p_url is not None and p_url >= 0.85:
            raw_p = max(raw_p, 0.90)
            
        # 4. High confidence text threat (e.g. Scammer sending urgent alert with fake phone number or OTP demand)
        elif (has_severe_panic or has_otp) and p_text >= 0.60:
            raw_p = max(raw_p, max(p_text, 0.88))
            
        # 5. Raw IP with urgency triggers
        if is_ip and u_score > 0.3:
            raw_p = max(raw_p, 0.92)

        # Convert to 0 - 100 risk score
        risk_score = round(raw_p * 100, 1)

        # Assign Risk Tier
        if risk_score >= 80.0:
            risk_tier = "CRITICAL FRAUD"
            risk_color = "#ef4444"
            verdict = "DANGEROUS PHISHING / FRAUD DETECTED"
        elif risk_score >= 50.0:
            risk_tier = "HIGH SUSPICION"
            risk_color = "#f97316"
            verdict = "SUSPICIOUS ACTIVITY DETECTED"
        elif risk_score >= 25.0:
            risk_tier = "MODERATE RISK"
            risk_color = "#eab308"
            verdict = "POTENTIAL UNVERIFIED THREAT"
        else:
            risk_tier = "SAFE / LEGITIMATE"
            risk_color = "#10b981"
            verdict = "NO SIGNIFICANT THREAT DETECTED"

        return {
            "risk_score": risk_score,
            "raw_probability": round(raw_p, 4),
            "risk_tier": risk_tier,
            "risk_color": risk_color,
            "verdict": verdict,
            "modality_breakdown": {
                "text_fraud_probability": round(p_text, 4),
                "url_fraud_probability": round(p_url, 4) if p_url is not None else None,
                "contradiction_score": round(c_score, 4),
                "urgency_score": round(u_score, 4),
                "brand_mismatch": brand_mismatch
            }
        }
