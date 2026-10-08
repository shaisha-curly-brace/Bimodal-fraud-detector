"""
tests/test_text.py

Unit tests for text preprocessing, vectorization, and text model inference.
"""

import pytest
from backend.utils.preprocessing import (
    clean_sms_text,
    extract_url_from_text,
    extract_all_urls_from_text,
    has_email_address,
    has_phone_number,
    detect_urgency_indicators,
    highlight_suspicious_tokens,
)
from backend.architectures.text_model import TextFraudClassifier
from backend.analyzers.text_analyzer import TextAnalyzer


def test_clean_sms_text():
    raw = "  Your account <#> is locked!   Please verify: http://bit.do/123  "
    cleaned = clean_sms_text(raw)
    assert "<#>" in cleaned
    assert "  " not in cleaned
    assert cleaned.startswith("Your")


def test_extract_url_from_text():
    text = "Important update: https://chase-secure.com/auth. Please login."
    url = extract_url_from_text(text)
    assert url == "https://chase-secure.com/auth"

    # Bare www
    text2 = "Visit www.example.org for info."
    url2 = extract_url_from_text(text2)
    assert url2 == "www.example.org"

    # Multiple URLs
    text3 = "Check https://site1.com and https://site2.com for details."
    urls = extract_all_urls_from_text(text3)
    assert len(urls) == 2


def test_entity_flags():
    msg1 = "Email us at support@chase.com for help"
    assert has_email_address(msg1) is True
    assert has_phone_number(msg1) is False

    msg2 = "Call our hotline at +1-800-555-0199 now"
    assert has_phone_number(msg2) is True


def test_urgency_detector():
    urgent_msg = "URGENT: Your account has been suspended! Enter your OTP immediately."
    res = detect_urgency_indicators(urgent_msg)
    assert res["urgency_score"] > 0.4
    assert res["has_otp_request"] is True
    assert "urgent" in res["matched_keywords"] or "suspended" in res["matched_keywords"]


def test_text_classifier_inference():
    clf = TextFraudClassifier()
    assert clf.is_loaded is True

    smishing_text = "WINNER! You have won a $1,000 gift card! Claim your prize now: http://claim.xyz"
    p_fraud, prob_dict = clf.predict_proba(smishing_text)
    assert p_fraud > 0.5
    assert "fraud" in prob_dict or "smishing" in prob_dict or "legitimate" in prob_dict

    ham_text = "Hey are we still meeting for lunch at 1pm?"
    p_ham, _ = clf.predict_proba(ham_text)
    assert p_ham < 0.3


def test_text_analyzer_full():
    analyzer = TextAnalyzer()
    res = analyzer.analyze("Security Alert: Your PayPal account is compromised. http://paypal-fix.top")
    assert res["fraud_probability"] > 0.5
    assert res["extracted_url"] == "http://paypal-fix.top"
    assert len(res["tokens"]) > 0


def test_organic_positive_and_negative_cases():
    import json
    from backend.config import settings

    clf = TextFraudClassifier()
    assert clf.is_loaded is True

    pos_path = settings.DATA_DIR / "test_cases" / "organic_positive.json"
    neg_path = settings.DATA_DIR / "test_cases" / "organic_negative.json"

    with open(pos_path, "r", encoding="utf-8") as f:
        pos_cases = json.load(f)
    with open(neg_path, "r", encoding="utf-8") as f:
        neg_cases = json.load(f)

    # All organic positive cases should trigger high fraud probability in text classifier
    for case in pos_cases:
        p_fraud, _ = clf.predict_proba(case["text"])
        assert p_fraud > 0.50, f"Positive case {case['id']} should have high fraud prob, got {p_fraud}"

    # Pure conversational/benign negative cases (e.g. neg_004) should have low text fraud score
    conversational_cases = [c for c in neg_cases if c.get("url") is None or "lunch" in c["text"].lower()]
    for case in conversational_cases:
        p_fraud, _ = clf.predict_proba(case["text"])
        assert p_fraud < 0.30, f"Conversational case {case['id']} should have low fraud prob, got {p_fraud}"
