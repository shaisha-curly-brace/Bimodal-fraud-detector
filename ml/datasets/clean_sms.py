"""
ml/datasets/clean_sms.py

Cleans and preprocesses the Mendeley SMS dataset (5,971 messages).
Schema: LABEL, TEXT, URL, EMAIL, PHONE
- Normalizes LABEL to lowercase: ham / spam / smishing.
- Normalizes URL, EMAIL, PHONE flags to boolean.
- Extracts inline URLs via regex, keeping tokens like <#> intact.
- Uses encoding="utf-8-sig" to properly handle BOM headers.

Output: ml/datasets/processed/cleaned_sms.csv
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

from backend.utils.preprocessing import (
    clean_sms_text,
    extract_url_from_text,
    has_email_address,
    has_phone_number,
)

RAW_DIR = DATASETS_DIR / "raw" / "sms"
OUT_PATH = DATASETS_DIR / "processed" / "cleaned_sms.csv"


def find_raw_csv(raw_dir: Path) -> Path:
    matches = sorted(raw_dir.glob("*.csv"))
    if not matches:
        raise FileNotFoundError(f"No CSV found in {raw_dir}. Place SMS dataset CSV there.")
    if len(matches) > 1:
        for m in matches:
            if "5971" in m.name or "mendeley" in m.name.lower() or "sms" in m.name.lower():
                return m
        print(f"[clean_sms] Multiple CSVs found, using: {matches[0].name}")
    return matches[0]


def normalize_label(raw_label) -> str:
    if not isinstance(raw_label, str):
        return "unknown"
    l = raw_label.strip().lower()
    if l in ("ham", "legitimate", "normal", "benign"):
        return "ham"
    if l in ("spam",):
        return "spam"
    if l in ("smishing", "smish", "phish", "phishing", "fraud"):
        return "smishing"
    return l


def normalize_flag(raw_flag) -> bool:
    if isinstance(raw_flag, bool):
        return raw_flag
    if not isinstance(raw_flag, str):
        return False
    return raw_flag.strip().lower() in ("yes", "y", "true", "1")


def clean_sms_dataset(raw_dir: Path = RAW_DIR, out_path: Path = OUT_PATH, force_recompute: bool = False) -> pd.DataFrame:
    if not force_recompute and out_path.exists():
        print(f"[clean_sms] Found preprocessed cleaned SMS dataset at: {out_path}")
        df = pd.read_csv(out_path)
        print(f"[clean_sms] Loaded {len(df)} cleaned SMS rows.")
        return df

    raw_path = find_raw_csv(raw_dir)
    print(f"[clean_sms] Reading raw SMS dataset from: {raw_path}")
    df = pd.read_csv(raw_path, encoding="utf-8-sig")

    # Column mapping tolerance
    col_map = {c.upper().strip(): c for c in df.columns}
    text_col = col_map.get("TEXT", "TEXT")
    label_col = col_map.get("LABEL", "LABEL")
    url_col = col_map.get("URL", "URL")
    email_col = col_map.get("EMAIL", "EMAIL")
    phone_col = col_map.get("PHONE", "PHONE")

    print(f"[clean_sms] Initial row count: {len(df)}")

    df["message_text"] = df[text_col].apply(clean_sms_text)
    df["label"] = df[label_col].apply(normalize_label)
    df["url_flag"] = df[url_col].apply(normalize_flag) if url_col in df.columns else False
    df["email_flag"] = df[email_col].apply(normalize_flag) if email_col in df.columns else False
    df["phone_flag"] = df[phone_col].apply(normalize_flag) if phone_col in df.columns else False

    # Extract actual inline URL from text
    df["extracted_url"] = df["message_text"].apply(extract_url_from_text)

    # Dedup & non-empty filter
    before = len(df)
    df = df[df["message_text"].str.len() > 0]
    df = df.drop_duplicates(subset=["message_text"])
    after = len(df)
    print(f"[clean_sms] Filtered non-empty & deduplicated: {before} -> {after} rows")

    # Mismatch check
    df["flag_regex_mismatch"] = df["url_flag"] & df["extracted_url"].isna()
    n_mismatch = df["flag_regex_mismatch"].sum()
    if n_mismatch > 0:
        print(f"[clean_sms] Notice: {n_mismatch} rows have url_flag=True but no standard URL string extracted.")

    print("\n--- Cleaned SMS Label Distribution ---")
    for cls, group in df.groupby("label"):
        n = len(group)
        n_flag = group["url_flag"].sum()
        n_regex = group["extracted_url"].notna().sum()
        print(f"  {cls:10s}: {n:5d} messages | URL Flag=Yes: {n_flag:4d} | Extracted URL: {n_regex:4d}")
    print("---------------------------------------\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cols_to_save = ["message_text", "label", "url_flag", "email_flag", "phone_flag", "extracted_url", "flag_regex_mismatch"]
    df[cols_to_save].to_csv(out_path, index=False, encoding="utf-8")
    print(f"[clean_sms] Wrote {len(df)} cleaned rows to {out_path}")
    return df


if __name__ == "__main__":
    clean_sms_dataset()
