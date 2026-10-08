"""
backend/utils/preprocessing.py

Text cleaning, tokenization, URL/entity extraction, and keyword analysis.
Preserves tokens like &lt;#&gt; (anonymized numbers) as required.
"""

import re
import html
from typing import Tuple, List, Optional

# Regex to match URLs including http://, https://, and bare www. or bit.do / bit.ly / tinyurl style links
URL_REGEX = re.compile(r"(https?://[^\s<>\"'()]+|www\.[^\s<>\"'()]+|[a-zA-Z0-9-]+\.(?:com|org|net|xyz|me|top|info|co|io|tk|gq|ru|in|uk|app|link|site)/[^\s<>\"'()]*)", re.IGNORECASE)

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE)
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{10,12}\b")

# Urgency, credential harvesting, threat keywords common in smishing
URGENCY_KEYWORDS = [
    "urgent", "immediately", "immediate", "suspended", "suspension", "locked",
    "blocked", "unauthorized", "action required", "verify now", "confirm identity",
    "security alert", "fraudulent", "unusual activity", "compromised", "expires in",
    "24 hours", "48 hours", "10 minutes", "otp", "one time password", "pin",
    "refund", "claim", "won", "prize", "jackpot", "winner", "congratulations",
    "irs", "tax refund", "customs", "delivery fee", "package pending", "overdue",
    "final notice", "court", "legal action", "arrest warrant", "fine", "penalty"
]

FINANCIAL_KEYWORDS = [
    "bank", "banking", "account", "credit card", "debit card", "cvv", "atm",
    "balance", "statement", "transfer", "wire", "deposit", "crypto", "bitcoin",
    "wallet", "paypal", "chase", "wells fargo", "bofa", "citi", "hdfc", "sbi"
]


def clean_sms_text(text: str) -> str:
    """
    Cleans raw SMS message text while preserving special entity placeholders
    such as '&lt;#&gt;' and currency symbols.
    """
    if not isinstance(text, str):
        return ""
    
    # Normalize excessive whitespaces without destroying structure
    cleaned = text.strip()
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned


def extract_url_from_text(text: str) -> Optional[str]:
    """
    Extracts the first valid URL from message text.
    Strips trailing punctuation if captured at the end of a sentence.
    """
    if not isinstance(text, str):
        return None
    match = URL_REGEX.search(text)
    if not match:
        return None
    
    url = match.group(0).strip()
    # Strip trailing punctuation often attached at end of sentence
    url = re.sub(r"[.,;:!?)\]}>'\"]+$", "", url)
    return url if len(url) > 3 else None


def extract_all_urls_from_text(text: str) -> List[str]:
    """Extracts all URLs found in text."""
    if not isinstance(text, str):
        return []
    matches = URL_REGEX.findall(text)
    urls = []
    for m in matches:
        u = re.sub(r"[.,;:!?)\]}>'\"]+$", "", m.strip())
        if len(u) > 3 and u not in urls:
            urls.append(u)
    return urls


def has_email_address(text: str) -> bool:
    return bool(EMAIL_REGEX.search(text)) if isinstance(text, str) else False


def has_phone_number(text: str) -> bool:
    return bool(PHONE_REGEX.search(text)) if isinstance(text, str) else False


def detect_urgency_indicators(text: str) -> dict:
    """
    Scans text for urgent cues, high-risk financial calls to action, and OTP triggers.
    """
    if not isinstance(text, str):
        return {"urgency_score": 0.0, "matched_keywords": [], "has_otp_request": False}
    
    lower_text = text.lower()
    matched = []
    
    for kw in URGENCY_KEYWORDS:
        if kw in lower_text:
            matched.append(kw)
            
    for kw in FINANCIAL_KEYWORDS:
        if kw in lower_text and kw not in matched:
            matched.append(kw)
            
    has_otp = bool(re.search(r"\b(otp|one[-\s]?time[-\s]?password|verification code|pin)\b", lower_text))
    
    score = min(1.0, len(matched) * 0.2 + (0.3 if has_otp else 0.0))
    return {
        "urgency_score": round(score, 3),
        "matched_keywords": matched,
        "has_otp_request": has_otp
    }


def highlight_suspicious_tokens(text: str) -> List[dict]:
    """
    Segments text into tokens with risk tags for frontend UI rendering.
    """
    if not isinstance(text, str) or not text:
        return []
    
    tokens = text.split()
    results = []
    
    url = extract_url_from_text(text)
    
    for token in tokens:
        clean_tok = re.sub(r"[^a-zA-Z0-9]", "", token.lower())
        is_url = url and (token in url or url in token)
        is_urgent = any(kw in clean_tok for kw in ["urgent", "suspended", "locked", "verify", "alert", "otp", "code", "winner", "prize", "refund"])
        is_financial = any(kw in clean_tok for kw in ["bank", "card", "account", "paypal", "pay", "login", "pin"])
        
        tag = "normal"
        if is_url:
            tag = "url"
        elif is_urgent:
            tag = "urgent"
        elif is_financial:
            tag = "financial"
            
        results.append({
            "token": token,
            "type": tag
        })
    return results
