"""
backend/services/pdf_service.py

Generates professional, submission-ready PDF documents:
1. generate_complaint_report: Full formal cyber fraud incident complaint document for high-risk threats.
2. generate_analysis_report: Concise reference analysis record for safe/medium risk assessments.
"""

import io
import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def _generate_reference_number(text: str, url: Optional[str]) -> str:
    """Generates a unique complaint reference identifier, e.g. CFR-20261002-8F2D1"""
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    seed = f"{text}|{url or ''}|{time.time()}".encode("utf-8")
    short_hash = hashlib.sha256(seed).hexdigest()[:5].upper()
    return f"CFR-{ts_str}-{short_hash}"


def _get_pdf_styles():
    base_styles = getSampleStyleSheet()
    
    # Custom styles
    styles = {
        "DocTitle": ParagraphStyle(
            "DocTitle",
            parent=base_styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0f172a"),
            alignment=TA_LEFT,
            spaceAfter=4,
        ),
        "DocSubtitle": ParagraphStyle(
            "DocSubtitle",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10,
        ),
        "MetaLabel": ParagraphStyle(
            "MetaLabel",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#334155"),
        ),
        "MetaValue": ParagraphStyle(
            "MetaValue",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        ),
        "SectionHeader": ParagraphStyle(
            "SectionHeader",
            parent=base_styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1e293b"),
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
        ),
        "MonoBox": ParagraphStyle(
            "MonoBox",
            parent=base_styles["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0f172a"),
        ),
        "Disclaimer": ParagraphStyle(
            "Disclaimer",
            parent=base_styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        ),
        "Footer": ParagraphStyle(
            "Footer",
            parent=base_styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER,
        ),
        "BadgeDanger": ParagraphStyle(
            "BadgeDanger",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#b91c1c"),
        ),
        "BadgeSafe": ParagraphStyle(
            "BadgeSafe",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#15803d"),
        ),
        "BadgeWarning": ParagraphStyle(
            "BadgeWarning",
            parent=base_styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#b45309"),
        ),
    }
    return styles


def generate_complaint_report(
    analysis_result: Dict[str, Any],
    reporter_details: Dict[str, Any]
) -> tuple[bytes, str]:
    """
    Generates a formal, submission-ready incident complaint PDF.
    Returns (pdf_bytes, reference_number).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = _get_pdf_styles()
    story = []

    text_content = analysis_result.get("text_analysis", {}).get("cleaned_text") or reporter_details.get("text") or ""
    url_content = analysis_result.get("url_analysis", {}).get("url") or reporter_details.get("url") or ""
    ref_num = reporter_details.get("reference_number") or _generate_reference_number(text_content, url_content)
    filing_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 1. HEADER & CASE REFERENCE BOX
    story.append(Paragraph("Cyber Fraud / Phishing Incident Complaint", styles["DocTitle"]))
    story.append(Paragraph("Formal incident report for submission to cybersecurity authorities and platform investigations", styles["DocSubtitle"]))

    header_table_data = [
        [
            Paragraph("<b>Complaint Reference:</b>", styles["MetaLabel"]),
            Paragraph(f"<b>{ref_num}</b>", styles["MetaValue"]),
            Paragraph("<b>Date of Filing:</b>", styles["MetaLabel"]),
            Paragraph(filing_time, styles["MetaValue"]),
        ],
        [
            Paragraph("<b>Report Type:</b>", styles["MetaLabel"]),
            Paragraph("Incident Complaint Dossier", styles["MetaValue"]),
            Paragraph("<b>Automated Scan ID:</b>", styles["MetaLabel"]),
            Paragraph(hashlib.md5(f"{ref_num}".encode()).hexdigest()[:10].upper(), styles["MetaValue"]),
        ]
    ]
    header_table = Table(header_table_data, colWidths=[120, 160, 110, 150])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # 2. REPORTER DETAILS
    story.append(Paragraph("1. Complainant / Reporter Information", styles["SectionHeader"]))
    reporter_name = reporter_details.get("reporter_name", "Anonymous Reporter")
    reporter_email = reporter_details.get("reporter_email", "Not provided")
    reporter_phone = reporter_details.get("reporter_phone") or "Not provided"
    channel = reporter_details.get("channel", "SMS")

    reporter_table_data = [
        [
            Paragraph("<b>Full Name:</b>", styles["MetaLabel"]),
            Paragraph(reporter_name, styles["MetaValue"]),
            Paragraph("<b>Email Address:</b>", styles["MetaLabel"]),
            Paragraph(reporter_email, styles["MetaValue"]),
        ],
        [
            Paragraph("<b>Phone Number:</b>", styles["MetaLabel"]),
            Paragraph(reporter_phone, styles["MetaValue"]),
            Paragraph("<b>Received Via Channel:</b>", styles["MetaLabel"]),
            Paragraph(f"{channel}", styles["MetaValue"]),
        ]
    ]
    reporter_table = Table(reporter_table_data, colWidths=[120, 160, 110, 150])
    reporter_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(reporter_table)
    story.append(Spacer(1, 10))

    # 3. INCIDENT DETAILS (QUOTED MESSAGE & URL)
    story.append(Paragraph("2. Suspicious Incident Telemetry & Evidence Artifacts", styles["SectionHeader"]))
    
    clean_text_disp = text_content if text_content.strip() else "[No SMS text message body provided - URL direct analysis]"
    clean_url_disp = url_content if url_content.strip() else "[No explicit URL detected]"

    incident_data = [
        [
            Paragraph("<b>Analyzed Message Body:</b>", styles["MetaLabel"]),
        ],
        [
            Paragraph(clean_text_disp.replace("\n", "<br/>"), styles["MonoBox"]),
        ],
        [
            Paragraph(f"<b>Extracted / Target URL:</b> &nbsp; <font name='Courier'>{clean_url_disp}</font>", styles["MetaValue"]),
        ]
    ]
    incident_table = Table(incident_data, colWidths=[540])
    incident_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(incident_table)
    story.append(Spacer(1, 10))

    # 4. SYSTEM FINDINGS & THREAT ASSESSMENT
    story.append(Paragraph("3. Automated Threat Assessment & System Findings", styles["SectionHeader"]))
    
    risk_score = analysis_result.get("risk_score", 0.0)
    risk_tier = analysis_result.get("risk_tier", "HIGH SUSPICION")
    verdict = analysis_result.get("verdict", "SUSPICIOUS ACTIVITY DETECTED")
    summary = analysis_result.get("explanation", {}).get("summary", "")
    
    score_style = styles["BadgeDanger"] if risk_score >= 50 else (styles["BadgeWarning"] if risk_score >= 25 else styles["BadgeSafe"])
    
    modality = analysis_result.get("modality_breakdown", {})
    t_prob = modality.get("text_fraud_probability")
    u_prob = modality.get("url_fraud_probability")
    c_score = modality.get("contradiction_score")
    b_mismatch = modality.get("brand_mismatch", False)

    findings_data = [
        [
            Paragraph("<b>Overall Threat Risk Score:</b>", styles["MetaLabel"]),
            Paragraph(f"<b>{risk_score:.1f} / 100 ({risk_tier})</b>", score_style),
            Paragraph("<b>Evaluation Verdict:</b>", styles["MetaLabel"]),
            Paragraph(f"<b>{verdict}</b>", styles["BodyBold"]),
        ],
        [
            Paragraph("<b>SMS Semantics Risk:</b>", styles["MetaLabel"]),
            Paragraph(f"{(t_prob * 100):.1f}%" if t_prob is not None else "N/A", styles["MetaValue"]),
            Paragraph("<b>Lexical URL Threat Risk:</b>", styles["MetaLabel"]),
            Paragraph(f"{(u_prob * 100):.1f}%" if u_prob is not None else "N/A", styles["MetaValue"]),
        ],
        [
            Paragraph("<b>Cross-Modal Contradiction:</b>", styles["MetaLabel"]),
            Paragraph(f"{(c_score * 100):.0f}%" if c_score is not None else "0%", styles["MetaValue"]),
            Paragraph("<b>Brand Impersonation:</b>", styles["MetaLabel"]),
            Paragraph("CONFIRMED MISMATCH" if b_mismatch else "None flagged", styles["BadgeDanger"] if b_mismatch else styles["MetaValue"]),
        ]
    ]
    findings_table = Table(findings_data, colWidths=[140, 140, 130, 130])
    findings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(findings_table)
    story.append(Spacer(1, 6))

    # Evidence items table
    evidence_items = analysis_result.get("explanation", {}).get("evidence_items", [])
    if evidence_items:
        evidence_rows = [
            [
                Paragraph("<b>Category</b>", styles["MetaLabel"]),
                Paragraph("<b>Severity</b>", styles["MetaLabel"]),
                Paragraph("<b>Evidence Description</b>", styles["MetaLabel"]),
            ]
        ]
        for item in evidence_items:
            sev = item.get("severity", "INFO")
            sev_style = styles["BadgeDanger"] if sev in ("CRITICAL", "HIGH") else (styles["BadgeWarning"] if sev == "MEDIUM" else styles["MetaValue"])
            evidence_rows.append([
                Paragraph(item.get("category", "Threat Marker"), styles["MetaValue"]),
                Paragraph(sev, sev_style),
                Paragraph(f"<b>{item.get('title', '')}</b>: {item.get('description', '')}", styles["Body"]),
            ])

        ev_table = Table(evidence_rows, colWidths=[120, 70, 350])
        ev_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(ev_table)

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>Notice: Findings generated by automated fraud detection system — for reference in your complaint, not a substitute for official investigation.</i>",
        styles["Disclaimer"]
    ))
    story.append(Spacer(1, 8))

    # 5. REPORTER'S NOTES (IF PROVIDED)
    notes = reporter_details.get("notes")
    if notes and notes.strip():
        story.append(Paragraph("4. Complainant's Narrative & Supplementary Notes", styles["SectionHeader"]))
        notes_data = [[Paragraph(notes.strip().replace("\n", "<br/>"), styles["Body"])]]
        notes_table = Table(notes_data, colWidths=[540])
        notes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#fefce8")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#fef08a")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(notes_table)
        story.append(Spacer(1, 8))

    # 6. RECOMMENDED NEXT STEPS (GENERALISED)
    section_num = "5" if (notes and notes.strip()) else "4"
    story.append(Paragraph(f"{section_num}. Recommended Incident Response Actions", styles["SectionHeader"]))
    
    steps = [
        "<b>Do not interact:</b> Never click links, download attachments, or reply to the suspicious message.",
        "<b>Block sender:</b> Block and flag the originating phone number or email address on your mobile device/service provider.",
        "<b>Notify impersonated entity:</b> If a specific bank, merchant, or service is being impersonated, notify their official customer fraud division directly through their verified website or mobile application.",
        "<b>Preserve forensic evidence:</b> Keep the original message intact (capture full screenshots and retain the raw SMS text without deleting) for evidentiary review.",
        "<b>File official complaint:</b> File a formal incident report with your national cybercrime reporting authority or local law enforcement agency's cybercrime division, attaching this document as supporting telemetry."
    ]

    steps_data = [[Paragraph(f"• {step}", styles["Body"])] for step in steps]
    steps_table = Table(steps_data, colWidths=[540])
    steps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(steps_table)
    story.append(Spacer(1, 10))

    # 7. FOOTER DISCLAIMER
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph(
        f"This document is a system-generated reporting dossier prepared to assist in filing an incident complaint. "
        f"It does not constitute an official legal filing on its own. | Reference: {ref_num}",
        styles["Footer"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes, ref_num


def generate_analysis_report(analysis_result: Dict[str, Any]) -> tuple[bytes, str]:
    """
    Generates a concise reference analysis report for low/medium risk assessments.
    Returns (pdf_bytes, date_string).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = _get_pdf_styles()
    story = []

    date_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    timestamp_display = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Header
    story.append(Paragraph("Cyber Threat &amp; Fraud Analysis Report", styles["DocTitle"]))
    story.append(Paragraph("Automated bimodal security inspection summary (SMS semantics and lexical URL analysis)", styles["DocSubtitle"]))

    meta_table_data = [
        [
            Paragraph("<b>Inspection Date:</b>", styles["MetaLabel"]),
            Paragraph(timestamp_display, styles["MetaValue"]),
            Paragraph("<b>Assessment Type:</b>", styles["MetaLabel"]),
            Paragraph("Technical Telemetry Record", styles["MetaValue"]),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[120, 160, 110, 150])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Analyzed Content
    text_content = analysis_result.get("text_analysis", {}).get("cleaned_text") or ""
    url_content = analysis_result.get("url_analysis", {}).get("url") or ""

    clean_text_disp = text_content if text_content.strip() else "[No SMS text message body provided]"
    clean_url_disp = url_content if url_content.strip() else "[No explicit URL detected]"

    content_data = [
        [Paragraph("<b>Message Content Analyzed:</b>", styles["MetaLabel"])],
        [Paragraph(clean_text_disp.replace("\n", "<br/>"), styles["MonoBox"])],
        [Paragraph(f"<b>Target URL:</b> &nbsp; <font name='Courier'>{clean_url_disp}</font>", styles["MetaValue"])],
    ]
    content_table = Table(content_data, colWidths=[540])
    content_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#ffffff")),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")),
        ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(content_table)
    story.append(Spacer(1, 10))

    # Score & Modality
    risk_score = analysis_result.get("risk_score", 0.0)
    risk_tier = analysis_result.get("risk_tier", "SAFE")
    verdict = analysis_result.get("verdict", "NO SIGNIFICANT THREAT DETECTED")
    summary = analysis_result.get("explanation", {}).get("summary", "")

    score_style = styles["BadgeDanger"] if risk_score >= 50 else (styles["BadgeWarning"] if risk_score >= 25 else styles["BadgeSafe"])
    modality = analysis_result.get("modality_breakdown", {})
    t_prob = modality.get("text_fraud_probability")
    u_prob = modality.get("url_fraud_probability")

    score_table_data = [
        [
            Paragraph("<b>Overall Risk Score:</b>", styles["MetaLabel"]),
            Paragraph(f"<b>{risk_score:.1f} / 100 ({risk_tier})</b>", score_style),
            Paragraph("<b>Verdict:</b>", styles["MetaLabel"]),
            Paragraph(f"<b>{verdict}</b>", styles["BodyBold"]),
        ],
        [
            Paragraph("<b>Text Threat Probability:</b>", styles["MetaLabel"]),
            Paragraph(f"{(t_prob * 100):.1f}%" if t_prob is not None else "N/A", styles["MetaValue"]),
            Paragraph("<b>URL Threat Probability:</b>", styles["MetaLabel"]),
            Paragraph(f"{(u_prob * 100):.1f}%" if u_prob is not None else "N/A", styles["MetaValue"]),
        ]
    ]
    score_table = Table(score_table_data, colWidths=[140, 140, 130, 130])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # Evidence items
    evidence_items = analysis_result.get("explanation", {}).get("evidence_items", [])
    if evidence_items:
        story.append(Paragraph("Evaluated Evidence Markers", styles["SectionHeader"]))
        evidence_rows = [
            [
                Paragraph("<b>Category</b>", styles["MetaLabel"]),
                Paragraph("<b>Severity</b>", styles["MetaLabel"]),
                Paragraph("<b>Details</b>", styles["MetaLabel"]),
            ]
        ]
        for item in evidence_items:
            sev = item.get("severity", "INFO")
            sev_style = styles["BadgeDanger"] if sev in ("CRITICAL", "HIGH") else (styles["BadgeWarning"] if sev == "MEDIUM" else styles["MetaValue"])
            evidence_rows.append([
                Paragraph(item.get("category", "General"), styles["MetaValue"]),
                Paragraph(sev, sev_style),
                Paragraph(f"<b>{item.get('title', '')}</b>: {item.get('description', '')}", styles["Body"]),
            ])

        ev_table = Table(evidence_rows, colWidths=[120, 70, 350])
        ev_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#f1f5f9")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(ev_table)
        story.append(Spacer(1, 10))

    # Recommendations
    recs = analysis_result.get("explanation", {}).get("recommendations", [])
    if recs:
        story.append(Paragraph("Security Recommendations", styles["SectionHeader"]))
        recs_data = [[Paragraph(f"• {r}", styles["Body"])] for r in recs]
        recs_table = Table(recs_data, colWidths=[540])
        recs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#ffffff")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(recs_table)
        story.append(Spacer(1, 10))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=6))
    story.append(Paragraph(
        f"Automated Bimodal Fraud Detection System | Generated on {timestamp_display} | Reference Record Only",
        styles["Footer"]
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes, date_str
