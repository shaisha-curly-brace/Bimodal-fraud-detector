"""
backend/api/schemas.py

Pydantic data models for request validation and structured API responses.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field("", description="Raw SMS message text to analyze")
    url: Optional[str] = Field(None, description="Optional explicit URL if separated from text")


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., description="Raw SMS message text to analyze")
    url: Optional[str] = Field(None, description="Optional explicit URL if separated from text")


class URLAnalyzeRequest(BaseModel):
    url: str = Field(..., description="Raw URL to inspect")


class ReportRequest(BaseModel):
    text: Optional[str] = Field("", description="Raw SMS message text analyzed")
    url: Optional[str] = Field(None, description="Optional destination URL analyzed")
    reporter_name: Optional[str] = Field(None, description="Reporter full name (required for complaint report)")
    reporter_email: Optional[str] = Field(None, description="Reporter email address (required for complaint report)")
    reporter_phone: Optional[str] = Field(None, description="Reporter optional phone number")
    channel: Optional[str] = Field("SMS", description="Platform/channel received on (SMS, WhatsApp, Email, Other)")
    notes: Optional[str] = Field(None, description="Supplementary complainant notes")


class ComplaintReportRequest(BaseModel):
    text: Optional[str] = Field("", description="Raw SMS message text analyzed")
    url: Optional[str] = Field(None, description="Optional destination URL analyzed")
    reporter_name: str = Field(..., description="Reporter full name")
    reporter_email: str = Field(..., description="Reporter email address")
    reporter_phone: Optional[str] = Field(None, description="Reporter optional phone number")
    channel: str = Field("SMS", description="Platform/channel received on (SMS, WhatsApp, Email, Other)")
    notes: Optional[str] = Field(None, description="Supplementary complainant notes")


class TokenHighlight(BaseModel):
    token: str
    type: str  # "normal", "urgent", "financial", "url"


class ExplanationItem(BaseModel):
    category: str
    severity: str
    title: str
    description: str
    icon: str


class ExplanationResponse(BaseModel):
    summary: str
    evidence_items: List[ExplanationItem]
    recommendations: List[str]
    risk_score: float
    risk_tier: str


class TextAnalysisResponse(BaseModel):
    cleaned_text: str
    fraud_probability: float
    class_probabilities: Dict[str, float]
    urgency_analysis: Dict[str, Any]
    tokens: List[TokenHighlight]
    explanations: List[Dict[str, Any]]
    extracted_url: Optional[str] = None


class URLAnalysisResponse(BaseModel):
    url: Optional[str] = None
    fraud_probability: Optional[float] = None
    lexical_features: Optional[Dict[str, Any]] = None
    is_evaluated: bool
    top_features: List[Dict[str, Any]] = []


class ContradictionResponse(BaseModel):
    contradiction_score: float
    is_contradiction_detected: bool
    brand_mismatch_detected: bool
    detected_brand: Optional[str] = None
    official_domains: List[str] = []
    actual_domain: Optional[str] = None
    flags: List[str] = []
    reasoning: str


class FullAnalysisResponse(BaseModel):
    risk_score: float
    risk_tier: str
    risk_color: str
    verdict: str
    modality_breakdown: Dict[str, Any]
    text_analysis: TextAnalysisResponse
    url_analysis: URLAnalysisResponse
    contradiction_analysis: ContradictionResponse
    explanation: ExplanationResponse
    input_metadata: Dict[str, Any]


AnalyzeResponse = FullAnalysisResponse


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: Dict[str, bool]
    timestamp: str
