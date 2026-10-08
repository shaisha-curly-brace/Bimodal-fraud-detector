"""
backend/api/routes.py

FastAPI router exposing all bimodal fraud analysis endpoints (Text + URL).
"""

import datetime
import json
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Response

from backend.api.schemas import (
    AnalyzeRequest,
    TextAnalyzeRequest,
    URLAnalyzeRequest,
    FullAnalysisResponse,
    HealthResponse,
    ReportRequest,
    ComplaintReportRequest
)
from backend.services.fraud_service import FraudService
from backend.services.pdf_service import generate_complaint_report, generate_analysis_report
from backend.config import settings

router = APIRouter()
fraud_service = FraudService()


@router.post("/analyze", response_model=FullAnalysisResponse)
async def analyze(payload: AnalyzeRequest):
    """
    Main unified endpoint: executes master fraud detection pipeline on message text and/or URL.
    """
    try:
        text_val = payload.text or ""
        if len(text_val) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text length exceeds maximum allowed length of {settings.MAX_TEXT_LENGTH} characters."
            )
        result = fraud_service.run_pipeline(text=text_val, url=payload.url)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/analyze/text", response_model=FullAnalysisResponse)
async def analyze_text(payload: TextAnalyzeRequest):
    """
    Analyzes message text, automatically extracting URLs and evaluating text + URL + contradiction.
    """
    try:
        if len(payload.text) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text length exceeds maximum allowed length of {settings.MAX_TEXT_LENGTH} characters."
            )
        result = fraud_service.analyze_message(text=payload.text, url=payload.url)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text analysis error: {str(e)}")


@router.post("/analyze/url", response_model=FullAnalysisResponse)
async def analyze_url(payload: URLAnalyzeRequest):
    """
    Analyzes a URL string directly using the real-time lexical classifier.
    """
    try:
        result = fraud_service.analyze_url_only(url=payload.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"URL analysis error: {str(e)}")


@router.post("/analyze/multimodal", response_model=FullAnalysisResponse)
async def analyze_multimodal(payload: TextAnalyzeRequest):
    """
    Analyzes explicit bimodal pair (text + url) with joint decision fusion.
    """
    try:
        result = fraud_service.analyze_message(text=payload.text, url=payload.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bimodal analysis error: {str(e)}")


@router.post("/report")
async def generate_pdf_report(payload: ReportRequest):
    """
    Generates a conditional downloadable PDF report:
    - If risk_score >= RISK_THRESHOLD_HIGH: requires reporter_name and reporter_email, returns a formal submission-ready complaint document (Fraud_Complaint_{ref}.pdf).
    - If risk_score < RISK_THRESHOLD_HIGH: returns a concise technical analysis reference record (Fraud_Analysis_{date}.pdf).
    """
    try:
        text_val = payload.text or ""
        if len(text_val) > settings.MAX_TEXT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Text length exceeds maximum allowed length of {settings.MAX_TEXT_LENGTH} characters."
            )

        # Run analysis pipeline
        result = fraud_service.run_pipeline(text=text_val, url=payload.url)
        risk_score = result.get("risk_score", 0.0)

        high_threshold = getattr(settings, "RISK_THRESHOLD_HIGH", 50.0)

        if risk_score >= high_threshold:
            # Hazardous / Complaint path
            if not payload.reporter_name or not str(payload.reporter_name).strip():
                raise HTTPException(
                    status_code=422,
                    detail="Complainant full name is required for high-risk incident complaint reports."
                )
            if not payload.reporter_email or not str(payload.reporter_email).strip():
                raise HTTPException(
                    status_code=422,
                    detail="Complainant email address is required for high-risk incident complaint reports."
                )

            reporter_details = {
                "reporter_name": str(payload.reporter_name).strip(),
                "reporter_email": str(payload.reporter_email).strip(),
                "reporter_phone": payload.reporter_phone,
                "channel": payload.channel or "SMS",
                "notes": payload.notes,
                "text": text_val,
                "url": payload.url,
            }

            pdf_bytes, ref_num = generate_complaint_report(result, reporter_details)
            filename = f"Fraud_Complaint_{ref_num}.pdf"
        else:
            # Low / Medium risk path
            pdf_bytes, date_str = generate_analysis_report(result)
            filename = f"Fraud_Analysis_{date_str}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF report generation error: {str(e)}")


@router.get("/test-cases")
async def get_test_cases():
    """
    Returns curated organic and adversarial test cases for demonstration and testing.
    """
    test_cases_dir = settings.DATA_DIR / "test_cases"
    data = {}
    for filename in ["organic_positive.json", "organic_negative.json", "adversarial_mismatch.json"]:
        path = test_cases_dir / filename
        key = filename.replace(".json", "")
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
        else:
            data[key] = []
    return data


@router.get("/metrics")
async def get_system_metrics():
    """
    Returns benchmark metrics, ablation results, and confusion matrices.
    """
    report_path = settings.RESULTS_DIR / "evaluation_summary.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)

    ablation_path = settings.RESULTS_DIR / "ablation_comparison.json"
    if ablation_path.exists():
        with open(ablation_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {"message": "Metrics report generating. Run ml/evaluation/evaluate.py to update."}


@router.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse)
async def health_check():
    """
    System status and model availability health check.
    """
    return {
        "status": "ok",
        "version": settings.VERSION,
        "models_loaded": {
            "text_model": fraud_service.text_analyzer.classifier.is_loaded,
            "url_model": fraud_service.url_analyzer.classifier.is_loaded,
            "fusion_model": fraud_service.fusion_service.fusion_classifier.is_loaded,
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
