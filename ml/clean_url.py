"""
ml/clean_url.py (Compatibility shim -> ml/datasets/clean_url.py)
"""
from ml.datasets.clean_url import clean_url_dataset, RAW_DIR, OUT_PATH, find_raw_csv, normalize_url_label

__all__ = ["clean_url_dataset", "RAW_DIR", "OUT_PATH", "find_raw_csv", "normalize_url_label"]

if __name__ == "__main__":
    clean_url_dataset()
