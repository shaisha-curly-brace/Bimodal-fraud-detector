"""
ml/datasets/clean_url.py

Cleans the PhiUSIIL Phishing URL Dataset and extracts instantaneous lexical and structural features.

IMPORTANT CONSTRAINT:
- Label mapping in PhiUSIIL: 1 = legitimate, 0 = phishing (fraud).
- Features engineered: Strictly lexical/structural only (no live crawler features).

Output: ml/datasets/processed/cleaned_url.csv
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to sys.path
DATASETS_DIR = Path(__file__).resolve().parent       # ml/datasets/
ML_DIR = DATASETS_DIR.parent                         # ml/
PROJECT_ROOT = ML_DIR.parent                         # project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils.feature_extraction import (
    extract_url_lexical_features,
    LEXICAL_FEATURE_COLUMNS,
)

RAW_DIR = DATASETS_DIR / "raw" / "url"
OUT_PATH = DATASETS_DIR / "processed" / "cleaned_url.csv"


def find_raw_csv(raw_dir: Path) -> Path:
    matches = sorted(raw_dir.glob("*.csv"))
    if not matches:
        raise FileNotFoundError(f"No CSV found in {raw_dir}. Place URL dataset CSV there.")
    if len(matches) > 1:
        for m in matches:
            if "phiusiil" in m.name.lower() or "5971" in m.name or "url" in m.name.lower():
                return m
        print(f"[clean_url] Multiple CSVs found, using: {matches[0].name}")
    return matches[0]


def normalize_url_label(raw_label) -> str:
    """
    PhiUSIIL dataset ground truth:
    1 = Legitimate (benign)
    0 = Phishing (fraud)
    """
    if isinstance(raw_label, (int, float)):
        return "legitimate" if int(raw_label) == 1 else "fraud"
    if isinstance(raw_label, str):
        l = raw_label.strip().lower()
        if l in ("1", "legitimate", "benign", "good", "ham"):
            return "legitimate"
        if l in ("0", "phishing", "fraud", "malicious", "bad", "spam"):
            return "fraud"
    return "unknown"


def clean_url_dataset(raw_dir: Path = RAW_DIR, out_path: Path = OUT_PATH, sample_size: int = None, force_recompute: bool = False) -> pd.DataFrame:
    if not force_recompute and out_path.exists():
        print(f"[clean_url] Found preprocessed cleaned URL dataset at: {out_path}")
        df = pd.read_csv(out_path)
        print(f"[clean_url] Loaded {len(df)} cleaned URL rows.")
        return df

    raw_path = find_raw_csv(raw_dir)
    print(f"[clean_url] Reading raw URL dataset from: {raw_path}")
    df = pd.read_csv(raw_path, encoding="utf-8-sig")

    # Locate URL and label columns
    url_col = "URL" if "URL" in df.columns else "url"
    label_col = "label" if "label" in df.columns else "Label"

    print(f"[clean_url] Loaded raw rows: {len(df)}")

    # Map binary/string label to 'legitimate' or 'fraud'
    df["label_str"] = df[label_col].apply(normalize_url_label)
    # Binary numeric target: 1 for fraud (phishing), 0 for legitimate
    df["is_fraud"] = (df["label_str"] == "fraud").astype(int)

    # Normalize URL string
    df["url_clean"] = df[url_col].astype(str).str.strip()
    df = df[df["url_clean"].str.len() > 0]
    df = df.drop_duplicates(subset=["url_clean"])

    if sample_size and len(df) > sample_size:
        print(f"[clean_url] Sampling {sample_size} rows for rapid development...")
        df = df.sample(sample_size, random_state=42).reset_index(drop=True)

    print(f"[clean_url] Extracting lexical and structural features across {len(df)} URLs...")

    # Extract lexical features
    features_list = [extract_url_lexical_features(u) for u in df["url_clean"].tolist()]
    feat_df = pd.DataFrame(features_list)

    result_df = pd.DataFrame({
        "url": df["url_clean"].to_numpy(),
        "label": df["label_str"].to_numpy(),
        "is_fraud": df["is_fraud"].to_numpy(),
    })

    # Merge feature columns
    for col in LEXICAL_FEATURE_COLUMNS:
        result_df[col] = feat_df[col].to_numpy()

    result_df["Domain"] = feat_df["Domain"].to_numpy()
    result_df["TLD"] = feat_df["TLD"].to_numpy()

    print("\n--- Cleaned URL Label Distribution ---")
    print(result_df["label"].value_counts().to_string())
    print("--------------------------------------\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(out_path, index=False, encoding="utf-8")
    print(f"[clean_url] Wrote {len(result_df)} rows to {out_path}")
    return result_df


if __name__ == "__main__":
    clean_url_dataset()
