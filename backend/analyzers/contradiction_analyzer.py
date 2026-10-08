"""
backend/analyzers/contradiction_analyzer.py

Contradiction Analyzer:
Detects cross-modal discrepancies between SMS message text and inline URL:
1. Brand Impersonation: Text mentions Brand A (e.g. PayPal, Chase, Netflix) while URL domain is NOT Brand A.
2. Urgency Mismatch: High threat urgency in text with attempt to mask/divert.
3. Subdomain Spoofing: Brand name placed in subdomain of a different root domain.
4. Shortener / Redirection Masking: Use of link shorteners (bit.ly, is.gd, tinyurl) combined with urgent account verification.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import tldextract

BRAND_REF_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "samples" / "brand_domains.json"

KNOWN_SHORTENERS = {
    "bit.ly", "bit.do", "tinyurl.com", "is.gd", "t.co", "goo.gl", "ow.ly",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at"
}


class ContradictionAnalyzer:
    def __init__(self, brand_ref_path: Path = BRAND_REF_PATH):
        self.brand_ref = {}
        if brand_ref_path.exists():
            with open(brand_ref_path, "r", encoding="utf-8") as f:
                self.brand_ref = json.load(f)

    def analyze(self, text: str, url: Optional[str]) -> Dict[str, Any]:
        """
        Evaluates contradiction signals and returns contradiction score, flags, and details.
        """
        if not text or not url:
            return {
                "contradiction_score": 0.0,
                "is_contradiction_detected": False,
                "brand_mismatch_detected": False,
                "detected_brand": None,
                "official_domains": [],
                "actual_domain": None,
                "flags": [],
                "reasoning": "Single modality provided, no cross-modal contradiction possible."
            }

        lower_text = text.lower()
        ext = tldextract.extract(url)
        actual_domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        subdomain = ext.subdomain.lower() if ext.subdomain else ""
        root_domain = ext.domain.lower() if ext.domain else ""

        detected_brand = None
        official_domains = []
        brand_mismatch_detected = False
        flags = []
        contradiction_score = 0.0

        # 1. Check if text explicitly mentions a known brand
        for brand, domains in self.brand_ref.items():
            # Check brand mention in text (as word boundary)
            if re.search(rf"\b{re.escape(brand)}\b", lower_text):
                detected_brand = brand
                official_domains = domains
                
                # Check if the actual domain matches any of the official domains
                is_official = any(actual_domain.endswith(dom) or root_domain == dom.split(".")[0] for dom in domains)
                
                if not is_official:
                    brand_mismatch_detected = True
                    flags.append(f"Brand Impersonation: Message claims to be from '{brand.upper()}', but URL leads to '{actual_domain}'.")
                    contradiction_score += 0.65
                break

        # 2. Check for Subdomain Spoofing (e.g. paypal.com.evil-site.com)
        for brand, domains in self.brand_ref.items():
            if brand in subdomain and brand not in root_domain:
                flags.append(f"Subdomain Spoofing: Brand name '{brand.upper()}' is deceitfully used in subdomain '{subdomain}' of root domain '{actual_domain}'.")
                contradiction_score += 0.45
                break

        # 3. Check for Link Shortener with urgent security message
        if actual_domain in KNOWN_SHORTENERS:
            has_urgency = any(kw in lower_text for kw in ["urgent", "suspended", "verify", "locked", "fraud", "otp"])
            if has_urgency:
                flags.append("URL Masking: High-urgency security alert uses an obfuscated URL shortener.")
                contradiction_score += 0.35

        # 4. Check for IP address with financial claims
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", actual_domain.split(":")[0]):
            flags.append("Direct IP Link: Security/Banking notification links directly to an raw IP address rather than a verified domain.")
            contradiction_score += 0.50

        contradiction_score = min(1.0, contradiction_score)
        is_contradiction = contradiction_score > 0.3 or brand_mismatch_detected

        reasoning = "; ".join(flags) if flags else "No cross-modal contradictions or brand mismatches detected."

        return {
            "contradiction_score": round(contradiction_score, 3),
            "is_contradiction_detected": is_contradiction,
            "brand_mismatch_detected": brand_mismatch_detected,
            "detected_brand": detected_brand,
            "official_domains": official_domains,
            "actual_domain": actual_domain,
            "flags": flags,
            "reasoning": reasoning
        }
