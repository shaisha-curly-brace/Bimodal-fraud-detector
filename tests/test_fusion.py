"""
tests/test_fusion.py

Unit tests for multimodal fusion, contradiction detection, and end-to-end fraud service.
"""

import pytest
from backend.analyzers.contradiction_analyzer import ContradictionAnalyzer
from backend.architectures.fusion_model import MultimodalFusionClassifier
from backend.services.fraud_service import FraudService


def test_contradiction_analyzer_brand_mismatch():
    analyzer = ContradictionAnalyzer()

    # Mismatch: Text claims Bank of America, link goes to evil-site.com
    res = analyzer.analyze(
        text="BANK OF AMERICA: Your account has been compromised. Verify now:",
        url="https://google.com"
    )
    assert res["brand_mismatch_detected"] is True
    assert res["detected_brand"] == "bank of america"
    assert res["contradiction_score"] > 0.5


def test_contradiction_analyzer_brand_match():
    analyzer = ContradictionAnalyzer()

    # Match: Text claims Chase, URL is chase.com
    res = analyzer.analyze(
        text="Your CHASE balance update is ready to view.",
        url="https://chase.com"
    )
    assert res["brand_mismatch_detected"] is False
    assert res["detected_brand"] == "chase"
    assert res["contradiction_score"] == 0.0


def test_contradiction_subdomain_spoofing():
    analyzer = ContradictionAnalyzer()

    res = analyzer.analyze(
        text="Your account update",
        url="https://paypal.com.evil-phish.net/login"
    )
    assert res["is_contradiction_detected"] is True
    assert any("Subdomain" in f for f in res["flags"])


def test_fusion_service_end_to_end_smishing():
    service = FraudService()

    # Smishing positive test
    res_pos = service.analyze_message(
        text="URGENT: Your Netflix membership payment declined. Update now:",
        url="http://netflix-billing-update.xyz/login"
    )
    assert res_pos["risk_score"] > 70.0
    assert res_pos["risk_tier"] in ("HIGH SUSPICION", "CRITICAL FRAUD")
    assert len(res_pos["explanation"]["evidence_items"]) > 0


def test_fusion_service_end_to_end_legitimate():
    service = FraudService()

    # Legitimate negative test
    res_neg = service.analyze_message(
        text="Your Netflix password was recently changed. If this was you, no action needed.",
        url="https://netflix.com"
    )
    assert res_neg["risk_score"] < 25.0
    assert res_neg["risk_tier"] == "SAFE / LEGITIMATE"


def test_adversarial_mismatch_test_cases():
    import json
    from pathlib import Path
    from backend.config import settings

    test_cases_path = settings.DATA_DIR / "test_cases" / "adversarial_mismatch.json"
    assert test_cases_path.exists(), "adversarial_mismatch.json must exist"

    with open(test_cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    assert len(cases) >= 5
    service = FraudService()

    for case in cases:
        text = case.get("text", "")
        url = case.get("url")
        case_id = case.get("id")

        res = service.analyze_message(text=text, url=url)
        assert res["risk_score"] >= 50.0, f"Case {case_id} ({case['description']}) should have high risk score >= 50.0, got {res['risk_score']}"
        assert res["risk_tier"] in ("HIGH SUSPICION", "CRITICAL FRAUD"), f"Case {case_id} should be flagged as high/critical fraud"

        # Check that contradiction or modality threat was caught
        threat = case.get("primary_modality_threat")
        if threat == "contradiction":
            assert res["contradiction_analysis"]["brand_mismatch_detected"] is True, f"Brand mismatch expected for {case_id}"
        elif threat == "url":
            assert res["url_analysis"]["is_evaluated"] is True
            assert (res["url_analysis"]["fraud_probability"] or 0) > 0.4 or res["url_analysis"]["lexical_features"].get("IsDomainIP")
        elif threat == "text":
            assert res["text_analysis"]["fraud_probability"] > 0.5 or res["text_analysis"]["urgency_analysis"]["urgency_score"] > 0.3
