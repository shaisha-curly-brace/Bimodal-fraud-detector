"""
ml/datasets/pairing.py

Builds ml/datasets/processed/merged_pairs.csv by combining organic SMS-URL pairs
with brand-consistent synthetic augmentation pairs.

CRITICAL RULE:
- The evaluation/test split must be 100% pair_type == "organic".
- Synthetic pairs are for TRAINING AUGMENTATION ONLY, never for evaluation/benchmarks.

Output: ml/datasets/processed/merged_pairs.csv
"""

import json
import random
import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
DATASETS_DIR = Path(__file__).resolve().parent       # ml/datasets/
ML_DIR = DATASETS_DIR.parent                         # ml/
PROJECT_ROOT = ML_DIR.parent                         # project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.datasets.clean_sms import clean_sms_dataset, OUT_PATH as SMS_CLEAN_PATH
from ml.datasets.clean_url import clean_url_dataset, OUT_PATH as URL_CLEAN_PATH
from backend.utils.feature_extraction import (
    extract_url_lexical_features,
    LEXICAL_FEATURE_COLUMNS,
)

PROCESSED_DIR = DATASETS_DIR / "processed"
BRAND_REF_PATH = PROJECT_ROOT / "data" / "samples" / "brand_domains.json"
OUTPUT_PATH = PROCESSED_DIR / "merged_pairs.csv"

LEGITIMATE_TEMPLATES = [
    "Your OTP for {brand} net banking login is {otp}. Valid for 10 minutes. Do not share.",
    "Your {brand} account statement for this month is ready to view: {url}",
    "Thank you for using {brand}. Your transaction of ${amount} was successful. Details: {url}",
    "Your {brand} card ending {last4} was used for a purchase of ${amount}. View receipt: {url}",
    "Your {brand} package #{otp} has been delivered. Track your parcel here: {url}",
    "Security notice from {brand}: Your recent password change was successful.",
    "Dear customer, your {brand} monthly bill is generated. Pay online: {url}",
]


def extract_organic_pairs(cleaned_sms: pd.DataFrame) -> pd.DataFrame:
    """Extracts all organic SMS messages that contain an inline URL."""
    organic = cleaned_sms[cleaned_sms["extracted_url"].notna()].copy()
    organic["fraud_category"] = organic["label"]
    organic["label"] = organic["label"].apply(
        lambda l: "fraud" if l in ("smishing", "spam", "fraud") else "legitimate"
    )
    organic = organic.rename(columns={"extracted_url": "url"})
    organic["pair_type"] = "organic"

    cols = ["message_text", "url", "label", "fraud_category", "pair_type"]
    return organic[cols].reset_index(drop=True)


build_organic_pairs = extract_organic_pairs


def generate_synthetic_augment_pairs(brand_reference_path: Path, n_per_brand: int = 25) -> pd.DataFrame:
    """
    Generates synthetic brand-consistent legitimate SMS-URL pairs for training augmentation.
    Teaches the model that official brand domains combined with banking/auth SMS are legitimate.
    """
    if not brand_reference_path.exists():
        print(f"[pairing] WARN: Brand reference not found at {brand_reference_path}, skipping synthetic pairs")
        return pd.DataFrame()

    with open(brand_reference_path, "r", encoding="utf-8") as f:
        brand_reference = json.load(f)

    rows = []
    random.seed(42)
    for brand, domains in brand_reference.items():
        official_domain = domains[0]
        url = f"https://{official_domain}"
        for _ in range(n_per_brand):
            template = random.choice(LEGITIMATE_TEMPLATES)
            text = template.format(
                brand=brand.upper(),
                otp=random.randint(100000, 999999),
                amount=random.randint(10, 5000),
                last4=random.randint(1000, 9999),
                url=url
            )
            rows.append({
                "message_text": text,
                "url": url,
                "label": "legitimate",
                "fraud_category": "ham",
                "pair_type": "synthetic_augment",
            })

    synth_df = pd.DataFrame(rows)
    print(f"[pairing] Generated {len(synth_df)} legitimate augmentation pairs (TRAINING-ONLY, never for eval).")
    return synth_df


def enrich_with_url_features(merged_df: pd.DataFrame) -> pd.DataFrame:
    """Enriches dataframe with lexical URL features."""
    features_list = [extract_url_lexical_features(u) for u in merged_df["url"].tolist()]
    feat_df = pd.DataFrame(features_list)

    for col in LEXICAL_FEATURE_COLUMNS:
        merged_df[col] = feat_df[col].to_numpy()
    merged_df["Domain"] = feat_df["Domain"].to_numpy()
    merged_df["TLD"] = feat_df["TLD"].to_numpy()
    return merged_df


def build_merged_dataset() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Step 1: Clean SMS Dataset ===")
    if SMS_CLEAN_PATH.exists():
        cleaned_sms = pd.read_csv(SMS_CLEAN_PATH)
    else:
        cleaned_sms = clean_sms_dataset()

    print("\n=== Step 2: Clean URL Dataset ===")
    if not URL_CLEAN_PATH.exists():
        clean_url_dataset()

    print("\n=== Step 3: Build Organic Pairs ===")
    organic = build_organic_pairs(cleaned_sms)
    print(f"Organic SMS-URL pairs count: {len(organic)}")

    print("\n=== Step 4: Generate Synthetic Augmentation Pairs ===")
    synthetic = generate_synthetic_augment_pairs(BRAND_REF_PATH, n_per_brand=25)

    print("\n=== Step 5: Merge and Extract URL Features ===")
    merged = pd.concat([organic, synthetic], ignore_index=True)
    merged = enrich_with_url_features(merged)

    merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\n[pairing] Successfully wrote {len(merged)} rows to {OUTPUT_PATH}")
    print(f"  - Organic pairs (Evaluation & Train): {(merged['pair_type'] == 'organic').sum()}")
    print(f"  - Synthetic pairs (Training only):    {(merged['pair_type'] == 'synthetic_augment').sum()}")
    print(f"  - Fraud pairs:                        {(merged['label'] == 'fraud').sum()}")
    print(f"  - Legitimate pairs:                   {(merged['label'] == 'legitimate').sum()}")
    return merged


if __name__ == "__main__":
    build_merged_dataset()
