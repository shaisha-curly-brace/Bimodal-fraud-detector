"""
backend/utils/feature_extraction.py

Fast, robust lexical and structural feature extractor for URLs.
Strict constraint: All features are computable instantly from the raw URL string
without making any live network requests or webpage crawling.
"""

import math
import re
from urllib.parse import urlparse, unquote
from collections import Counter
import tldextract

SUSPICIOUS_TLDS = {
    "tk", "xyz", "top", "gq", "ga", "cf", "ml", "work", "buzz", "monster",
    "icu", "country", "stream", "download", "gdn", "racing", "bid", "loan",
    "date", "faith", "accountant", "vip", "fit", "cricket", "science", "party",
    "click", "link", "rest", "kim", "men", "win", "stream", "live"
}

SECURITY_KEYWORDS = {
    "login", "signin", "verify", "secure", "account", "update", "banking",
    "security", "support", "confirm", "wallet", "recover", "authenticate",
    "password", "billing", "invoice", "validate", "suspended", "unlock"
}

COMMON_BRANDS = {
    "paypal", "netflix", "amazon", "apple", "google", "microsoft", "chase",
    "bankofamerica", "wellsfargo", "citi", "citibank", "dhl", "usps", "fedex",
    "ups", "verizon", "att", "tmobile", "hdfc", "icici", "sbi", "barclays",
    "hsbc", "facebook", "instagram", "whatsapp", "telegram", "binance", "coinbase"
}

IP_PATTERN = re.compile(r"^(?:https?://)?(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/.*)?$", re.IGNORECASE)


def calculate_entropy(text: str) -> float:
    """Calculates Shannon entropy of a string."""
    if not text:
        return 0.0
    length = len(text)
    counts = Counter(text)
    entropy = -sum((count / length) * math.log2(count / length) for count in counts.values())
    return round(entropy, 4)


def extract_url_lexical_features(raw_url: str) -> dict:
    """
    Extracts purely lexical/structural features from a URL string.
    Works for any valid or malformed URL.
    """
    url = str(raw_url).strip()
    if not url:
        return _empty_url_features()

    if not (url.startswith("http://") or url.startswith("https://") or "://" in url):
        full_url = "http://" + url
    else:
        full_url = url

    try:
        parsed = urlparse(full_url)
    except Exception:
        parsed = urlparse("http://" + url.split("/")[0])

    ext = tldextract.extract(full_url)
    domain_name = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain or parsed.netloc
    subdomain = ext.subdomain or ""
    tld = ext.suffix or ""

    # Canonicalize naked domain to standard web host (www.) to match training corpus distribution
    if ext.domain and not ext.subdomain and not bool(IP_PATTERN.match(url)):
        if "://" in url:
            proto, rest = url.split("://", 1)
            url = f"{proto}://www.{rest}"
        else:
            url = f"https://www.{url}"
        full_url = url
        try:
            parsed = urlparse(full_url)
        except Exception:
            pass
        ext = tldextract.extract(full_url)
        domain_name = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        subdomain = ext.subdomain or ""
        tld = ext.suffix or ""

    url_len = len(url)
    domain_len = len(domain_name)
    tld_len = len(tld)

    is_domain_ip = 1 if bool(IP_PATTERN.match(url) or re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed.netloc.split(":")[0])) else 0
    is_https = 1 if url.lower().startswith("https://") else 0

    subdomain_parts = [s for s in subdomain.split(".") if s]
    # In dataset corpus, standard domains have at least 1 host/subdomain segment (e.g. www)
    no_of_subdomain = max(1, len(subdomain_parts)) if (ext.domain and not is_domain_ip) else len(subdomain_parts)

    # Letter, Digit, Special char counts
    letters = len(re.findall(r"[a-zA-Z]", url))
    digits = len(re.findall(r"[0-9]", url))
    equals = url.count("=")
    qmarks = url.count("?")
    ampersands = url.count("&")
    slashes = url.count("/")
    hyphens = url.count("-")
    dots = url.count(".")
    at_symbols = url.count("@")
    
    # Obfuscation (percent encoding, unquote differences)
    unquoted = unquote(url)
    obfuscated_chars = len(re.findall(r"%[0-9a-fA-F]{2}", url))
    has_obfuscation = 1 if (obfuscated_chars > 0 or at_symbols > 0 or unquoted != url) else 0

    special_chars = len(re.findall(r"[^a-zA-Z0-9]", url))
    other_special_chars = max(0, special_chars - equals - qmarks - ampersands)

    letter_ratio = round(letters / max(1, url_len), 4)
    digit_ratio = round(digits / max(1, url_len), 4)
    special_char_ratio = round(special_chars / max(1, url_len), 4)
    obfuscation_ratio = round(obfuscated_chars / max(1, url_len), 4)

    # Longest character continuation rate
    max_continuation = 1
    curr_len = 1
    for i in range(1, len(url)):
        if url[i] == url[i - 1]:
            curr_len += 1
            if curr_len > max_continuation:
                max_continuation = curr_len
        else:
            curr_len = 1
    char_continuation_rate = round(max_continuation / max(1, url_len), 4)

    # Entropies
    entropy = calculate_entropy(url)
    domain_entropy = calculate_entropy(domain_name)

    # Suspicious signals
    is_suspicious_tld = 1 if tld.lower() in SUSPICIOUS_TLDS else 0

    # Brand in subdomain while domain is different
    has_brand_in_subdomain = 0
    lower_subdomain = subdomain.lower()
    lower_domain = ext.domain.lower() if ext.domain else ""
    for brand in COMMON_BRANDS:
        if brand in lower_subdomain and brand not in lower_domain:
            has_brand_in_subdomain = 1
            break

    # Security keywords in path or query
    path_and_query = (parsed.path + "?" + parsed.query).lower()
    has_security_keyword = 1 if any(kw in path_and_query for kw in SECURITY_KEYWORDS) else 0

    return {
        "URLLength": url_len,
        "DomainLength": domain_len,
        "IsDomainIP": is_domain_ip,
        "TLDLength": tld_len,
        "NoOfSubDomain": no_of_subdomain,
        "HasObfuscation": has_obfuscation,
        "NoOfObfuscatedChar": obfuscated_chars,
        "ObfuscationRatio": obfuscation_ratio,
        "NoOfLettersInURL": letters,
        "LetterRatioInURL": letter_ratio,
        "NoOfDegitsInURL": digits,
        "DegitRatioInURL": digit_ratio,
        "NoOfEqualsInURL": equals,
        "NoOfQMarkInURL": qmarks,
        "NoOfAmpersandInURL": ampersands,
        "NoOfOtherSpecialCharsInURL": other_special_chars,
        "SpacialCharRatioInURL": special_char_ratio,
        "IsHTTPS": is_https,
        "CharContinuationRate": char_continuation_rate,
        "Entropy": entropy,
        "DomainEntropy": domain_entropy,
        "IsSuspiciousTLD": is_suspicious_tld,
        "HasBrandInSubdomain": has_brand_in_subdomain,
        "HasSecurityKeyword": has_security_keyword,
        "AtSymbolCount": at_symbols,
        "SlashCount": slashes,
        "HyphenCount": hyphens,
        "DotCount": dots,
        "Domain": domain_name,
        "TLD": tld,
    }


def _empty_url_features() -> dict:
    return {
        "URLLength": 0,
        "DomainLength": 0,
        "IsDomainIP": 0,
        "TLDLength": 0,
        "NoOfSubDomain": 0,
        "HasObfuscation": 0,
        "NoOfObfuscatedChar": 0,
        "ObfuscationRatio": 0.0,
        "NoOfLettersInURL": 0,
        "LetterRatioInURL": 0.0,
        "NoOfDegitsInURL": 0,
        "DegitRatioInURL": 0.0,
        "NoOfEqualsInURL": 0,
        "NoOfQMarkInURL": 0,
        "NoOfAmpersandInURL": 0,
        "NoOfOtherSpecialCharsInURL": 0,
        "SpacialCharRatioInURL": 0.0,
        "IsHTTPS": 0,
        "CharContinuationRate": 0.0,
        "Entropy": 0.0,
        "DomainEntropy": 0.0,
        "IsSuspiciousTLD": 0,
        "HasBrandInSubdomain": 0,
        "HasSecurityKeyword": 0,
        "AtSymbolCount": 0,
        "SlashCount": 0,
        "HyphenCount": 0,
        "DotCount": 0,
        "Domain": "",
        "TLD": "",
    }


# Ordered list of numeric feature column names for ML models
LEXICAL_FEATURE_COLUMNS = [
    "URLLength",
    "DomainLength",
    "IsDomainIP",
    "TLDLength",
    "NoOfSubDomain",
    "HasObfuscation",
    "NoOfObfuscatedChar",
    "ObfuscationRatio",
    "NoOfLettersInURL",
    "LetterRatioInURL",
    "NoOfDegitsInURL",
    "DegitRatioInURL",
    "NoOfEqualsInURL",
    "NoOfQMarkInURL",
    "NoOfAmpersandInURL",
    "NoOfOtherSpecialCharsInURL",
    "SpacialCharRatioInURL",
    "IsHTTPS",
    "CharContinuationRate",
    "Entropy",
    "DomainEntropy",
    "IsSuspiciousTLD",
    "HasBrandInSubdomain",
    "HasSecurityKeyword",
    "AtSymbolCount",
    "SlashCount",
    "HyphenCount",
    "DotCount",
]
