"""
backend/services/explanation_service.py

Explainable AI (XAI) Service:
Synthesizes multimodal analysis outputs into actionable human-readable explanations,
evidence breakdown cards, and security recommendations.
"""

from typing import Dict, List, Any, Optional


class ExplanationService:
    def generate_explanation(
        self,
        risk_result: Dict[str, Any],
        text_result: Dict[str, Any],
        url_result: Dict[str, Any],
        contradiction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates comprehensive evidence items and recommendations.
        """
        evidence_items = []
        recommendations = []
        
        risk_score = risk_result.get("risk_score", 0.0)
        risk_tier = risk_result.get("risk_tier", "SAFE")
        
        # 1. Contradiction & Brand Mismatch Evidence
        if contradiction_result.get("brand_mismatch_detected"):
            brand = contradiction_result.get("detected_brand", "Unknown").upper()
            domain = contradiction_result.get("actual_domain", "Unknown")
            evidence_items.append({
                "category": "Brand Impersonation",
                "severity": "CRITICAL",
                "title": f"Discrepancy: Claims {brand} but links to {domain}",
                "description": f"The message attempts to deceive the recipient by invoking brand authority while redirecting to an unauthorized domain ({domain}).",
                "icon": "shield-alert"
            })
            recommendations.append(f"Never log in to {brand} via links received in unsolicited messages. Access {brand} directly through their official app or website.")

        for flag in contradiction_result.get("flags", []):
            if "Subdomain Spoofing" in flag:
                evidence_items.append({
                    "category": "Domain Spoofing",
                    "severity": "HIGH",
                    "title": "Subdomain Deception",
                    "description": flag,
                    "icon": "alert-triangle"
                })
            elif "URL Masking" in flag:
                evidence_items.append({
                    "category": "Evasion Technique",
                    "severity": "MEDIUM",
                    "title": "Shortened Link Masking",
                    "description": flag,
                    "icon": "link"
                })

        # 2. Text Modality Evidence
        text_prob = text_result.get("fraud_probability", 0.0)
        urgency = text_result.get("urgency_analysis", {})
        matched_kws = urgency.get("matched_keywords", [])
        has_otp = urgency.get("has_otp_request", False)

        if has_otp and text_prob > 0.4:
            evidence_items.append({
                "category": "Credential Harvesting",
                "severity": "CRITICAL",
                "title": "OTP / 2FA Code Request",
                "description": "Message prompts for One-Time Password or verification code sharing, a classic vector for account takeover.",
                "icon": "key"
            })
            recommendations.append("Never share One-Time Passwords (OTPs) or PIN codes with anyone over SMS or unverified forms.")

        if matched_kws:
            evidence_items.append({
                "category": "Social Engineering",
                "severity": "HIGH" if len(matched_kws) >= 2 else "MEDIUM",
                "title": f"High Urgency / Coercive Language ({len(matched_kws)} triggers)",
                "description": f"Detected urgency patterns: {', '.join(matched_kws[:4])}.",
                "icon": "clock"
            })
            recommendations.append("Fraudsters use false urgency to induce panic and force hasty decisions. Pause and verify independently.")

        # 3. URL Lexical Evidence
        if url_result and url_result.get("is_evaluated"):
            url_prob = url_result.get("fraud_probability", 0.0)
            lex = url_result.get("lexical_features", {}) or {}
            
            if lex.get("IsDomainIP"):
                evidence_items.append({
                    "category": "Network Risk",
                    "severity": "CRITICAL",
                    "title": "Raw IP Address in URL",
                    "description": "The destination URL uses a direct IP address rather than a domain name, bypassing DNS security filters.",
                    "icon": "server"
                })
            if lex.get("IsSuspiciousTLD"):
                evidence_items.append({
                    "category": "Reputation Risk",
                    "severity": "HIGH",
                    "title": f"Suspicious Top-Level Domain (.{lex.get('TLD')})",
                    "description": f"The TLD .{lex.get('TLD')} is heavily associated with disposable phishing campaigns and cybercrime infrastructure.",
                    "icon": "globe"
                })
            if lex.get("HasObfuscation"):
                evidence_items.append({
                    "category": "Evasion Risk",
                    "severity": "MEDIUM",
                    "title": "Obfuscated URL Characters",
                    "description": "The URL contains unusual hexadecimal percent-encoding or special characters designed to evade automated inspection.",
                    "icon": "code"
                })
            if url_prob >= 0.75:
                evidence_items.append({
                    "category": "Machine Learning Assessment",
                    "severity": "HIGH",
                    "title": f"High Lexical Risk Score ({round(url_prob * 100, 1)}%)",
                    "description": "Structural attributes of the URL closely match signatures of known phishing and smishing domains in the PhiUSIIL corpus.",
                    "icon": "cpu"
                })

        # Fallback benign evidence if low risk
        if not evidence_items:
            evidence_items.append({
                "category": "Safety Profile",
                "severity": "INFO",
                "title": "No Critical Threat Signatures Found",
                "description": "Message structure and URL lexical features align with standard legitimate communications.",
                "icon": "check-circle"
            })
            recommendations.append("Standard safety hygiene: Always ensure your device and software are up to date.")

        if risk_score >= 80.0:
            summary = "CRITICAL THREAT: This message exhibits strong evidence of active phishing, credential harvesting, or brand impersonation. Do not interact with links or provide personal credentials."
        elif risk_score >= 50.0:
            summary = "SUSPICIOUS WARNING: High indicators of deceptive social engineering or high-risk domain attributes detected. Caution is strongly advised."
        elif risk_score >= 25.0:
            summary = "ELEVATED CAUTION: Some unusual patterns or unverified links detected, though definitive fraud markers are moderate."
        else:
            summary = "LOW RISK: The message and embedded links appear legitimate and consistent with standard notifications."

        return {
            "summary": summary,
            "evidence_items": evidence_items,
            "recommendations": list(dict.fromkeys(recommendations)),  # unique preserve order
            "risk_score": risk_score,
            "risk_tier": risk_tier
        }
