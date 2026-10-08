"""
ml/pairing.py (Compatibility shim -> ml/datasets/pairing.py)
"""
from ml.datasets.pairing import build_merged_dataset, build_organic_pairs, generate_synthetic_augment_pairs, enrich_with_url_features

__all__ = ["build_merged_dataset", "build_organic_pairs", "generate_synthetic_augment_pairs", "enrich_with_url_features"]

if __name__ == "__main__":
    build_merged_dataset()
