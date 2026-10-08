"""
ml/clean_sms.py (Compatibility shim -> ml/datasets/clean_sms.py)
"""
from ml.datasets.clean_sms import clean_sms_dataset, RAW_DIR, OUT_PATH, find_raw_csv, normalize_label, normalize_flag

__all__ = ["clean_sms_dataset", "RAW_DIR", "OUT_PATH", "find_raw_csv", "normalize_label", "normalize_flag"]

if __name__ == "__main__":
    clean_sms_dataset()
