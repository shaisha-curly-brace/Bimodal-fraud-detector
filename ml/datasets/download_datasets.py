"""
ml/datasets/download_datasets.py

Ensures raw datasets exist in ml/datasets/raw/sms and ml/datasets/raw/url.
- Mendeley SMS Phishing Corpus (5,971 messages)
- PhiUSIIL Phishing URL Dataset (235,795 URLs)
"""

import sys
from pathlib import Path

DATASETS_DIR = Path(__file__).resolve().parent
RAW_SMS_DIR = DATASETS_DIR / "raw" / "sms"
RAW_URL_DIR = DATASETS_DIR / "raw" / "url"

SMS_DATASET_INFO = {
    "name": "Mendeley SMS Phishing Corpus",
    "filename": "sms_mendeley.csv",
    "expected_rows": 5971,
    "description": "5,971 SMS messages tagged as ham, spam, and smishing."
}

URL_DATASET_INFO = {
    "name": "PhiUSIIL Phishing URL Dataset",
    "filename": "Dataset_5971.csv",
    "expected_rows": 235795,
    "description": "235,795 URLs with 28 dense lexical and structural features."
}


def verify_or_prepare_datasets() -> dict:
    RAW_SMS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_URL_DIR.mkdir(parents=True, exist_ok=True)

    status = {"sms": False, "url": False}

    sms_csvs = list(RAW_SMS_DIR.glob("*.csv"))
    if sms_csvs:
        status["sms"] = True
        print(f"[datasets] Found SMS dataset: {sms_csvs[0].name} ({sms_csvs[0].stat().st_size / 1024:.1f} KB)")
    else:
        print(f"[datasets] WARNING: No SMS CSV found in {RAW_SMS_DIR}")
        print("Please place the Mendeley SMS Phishing Corpus (sms_mendeley.csv) into ml/datasets/raw/sms/")

    url_csvs = list(RAW_URL_DIR.glob("*.csv"))
    if url_csvs:
        status["url"] = True
        print(f"[datasets] Found URL dataset: {url_csvs[0].name} ({url_csvs[0].stat().st_size / (1024*1024):.1f} MB)")
    else:
        print(f"[datasets] WARNING: No URL CSV found in {RAW_URL_DIR}")
        print("Please place the PhiUSIIL Phishing URL Dataset (Dataset_5971.csv) into ml/datasets/raw/url/")

    return status


if __name__ == "__main__":
    verify_or_prepare_datasets()
