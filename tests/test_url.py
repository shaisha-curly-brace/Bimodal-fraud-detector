"""
tests/test_url.py

Unit tests for URL lexical feature extraction and URL fraud model inference.
"""

import pytest
from backend.utils.feature_extraction import (
    extract_url_lexical_features,
    calculate_entropy,
    LEXICAL_FEATURE_COLUMNS
)
from backend.architectures.url_model import URLFraudClassifier
from backend.analyzers.url_analyzer import URLAnalyzer


def test_calculate_entropy():
    e1 = calculate_entropy("aaaaaa")
    e2 = calculate_entropy("a8!f9z_2")
    assert e1 == 0.0
    assert e2 > 2.0


def test_lexical_feature_count():
    assert len(LEXICAL_FEATURE_COLUMNS) == 28


def test_extract_url_lexical_features():
    url = "http://194.67.210.15:8080/claim-prize.php?user=123"
    feats = extract_url_lexical_features(url)
    assert feats["IsDomainIP"] == 1
    assert feats["URLLength"] > 20
    assert feats["Entropy"] > 3.0
    assert "NoOfSubDomain" in feats
    assert feats["SlashCount"] >= 1


def test_url_classifier_inference():
    clf = URLFraudClassifier()
    assert clf.is_loaded is True

    # High risk phishing URL with suspicious TLD and keywords
    phish_url = "http://chase-secure-banking-verify.xyz/login.php"
    p_phish, feats = clf.predict_proba(phish_url)
    assert p_phish > 0.6
    assert feats["IsSuspiciousTLD"] == 1

    # Legitimate URL
    legit_url = "https://www.chase.com"
    p_legit, _ = clf.predict_proba(legit_url)
    assert p_legit < 0.2


def test_url_analyzer():
    analyzer = URLAnalyzer()
    res = analyzer.analyze("http://paypal-verification-center.top/auth")
    assert res["is_evaluated"] is True
    assert res["fraud_probability"] > 0.5
    assert len(res["top_features"]) > 0


def test_organic_positive_and_negative_url_cases():
    import json
    from backend.config import settings

    clf = URLFraudClassifier()
    assert clf.is_loaded is True

    pos_path = settings.DATA_DIR / "test_cases" / "organic_positive.json"
    neg_path = settings.DATA_DIR / "test_cases" / "organic_negative.json"

    with open(pos_path, "r", encoding="utf-8") as f:
        pos_cases = json.load(f)
    with open(neg_path, "r", encoding="utf-8") as f:
        neg_cases = json.load(f)

    # Positive URLs should have elevated fraud prob
    for case in pos_cases:
        if case.get("url"):
            p_fraud, feats = clf.predict_proba(case["url"])
            assert p_fraud > 0.40 or feats.get("IsDomainIP") or feats.get("IsSuspiciousTLD"), f"Positive URL {case['id']} should have high fraud score, got {p_fraud}"

    # Negative URLs should have low fraud prob
    for case in neg_cases:
        if case.get("url"):
            p_fraud, feats = clf.predict_proba(case["url"])
            assert p_fraud < 0.35, f"Negative URL {case['id']} should have low fraud score, got {p_fraud}"
