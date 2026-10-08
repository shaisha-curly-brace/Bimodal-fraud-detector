"""
tests/test_pdf.py

Unit and integration tests for conditional PDF report generation:
1. Hazardous complaint path (submission-ready complaint dossier with reference number and reporter details).
2. Safe/moderate analysis path (concise reference record without reporter requirements).
3. Validation rules on hazardous reporting.
"""

import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader

from backend.main import app

client = TestClient(app)
TEST_CASES_DIR = Path(__file__).resolve().parent.parent / "data" / "test_cases"


@pytest.fixture
def hazardous_case():
    with open(TEST_CASES_DIR / "adversarial_mismatch.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    # Pick a strong hazardous case
    return cases[0]


@pytest.fixture
def safe_case():
    with open(TEST_CASES_DIR / "organic_negative.json", "r", encoding="utf-8") as f:
        cases = json.load(f)
    return cases[0]


def test_hazardous_complaint_report_generation(hazardous_case):
    """
    Tests hazardous case report generation with reporter details.
    Asserts valid PDF header and extracts text via pypdf to verify reference number,
    reporter name, and complaint sections.
    """
    payload = {
        "text": hazardous_case["text"],
        "url": hazardous_case["url"],
        "reporter_name": "Dr. Alex Morgan",
        "reporter_email": "alex.morgan@cybersec-dept.org",
        "reporter_phone": "+1-555-019-8822",
        "channel": "SMS",
        "notes": "Unsolicited text received on personal mobile during working hours."
    }

    response = client.post("/api/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment;" in response.headers.get("content-disposition", "")
    assert "Fraud_Complaint_CFR-" in response.headers.get("content-disposition", "")

    # Validate PDF binary header
    pdf_bytes = response.content
    assert pdf_bytes.startswith(b"%PDF-")

    # Extract text with pypdf and verify presence of required elements
    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1
    
    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])

    # Assertions on content
    assert "Cyber Fraud / Phishing Incident Complaint" in full_text
    assert "CFR-" in full_text  # Generated reference number pattern
    assert "Dr. Alex Morgan" in full_text  # Reporter name
    assert "alex.morgan@cybersec-dept.org" in full_text  # Reporter email
    assert "+1-555-019-8822" in full_text  # Reporter phone
    assert "Recommended Incident Response Actions" in full_text  # Next steps
    assert "automated fraud detection system" in full_text.lower()  # Automated disclaimer


def test_safe_analysis_report_generation(safe_case):
    """
    Tests safe/moderate case report generation via the simpler single-click path.
    Asserts valid PDF with no reporter fields required.
    """
    payload = {
        "text": safe_case["text"],
        "url": safe_case["url"],
    }

    response = client.post("/api/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "Fraud_Analysis_" in response.headers.get("content-disposition", "")

    pdf_bytes = response.content
    assert pdf_bytes.startswith(b"%PDF-")

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) >= 1

    full_text = "\n".join([page.extract_text() or "" for page in reader.pages])
    assert "Cyber Threat & Fraud Analysis Report" in full_text
    assert "Inspection Date:" in full_text


def test_hazardous_report_missing_reporter_details_validation(hazardous_case):
    """
    Asserts that attempting to generate a report for a hazardous case without
    reporter name/email raises a 422 Unprocessable Entity error.
    """
    payload = {
        "text": hazardous_case["text"],
        "url": hazardous_case["url"],
        "reporter_name": "",  # Missing
        "reporter_email": ""
    }

    response = client.post("/api/report", json=payload)
    assert response.status_code == 422
    assert "required" in response.json().get("detail", "").lower()
