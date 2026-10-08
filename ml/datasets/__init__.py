"""
ml/datasets package.
Provides dataset downloading, cleaning, and pairing pipelines for SMS and URL datasets.
"""

from ml.datasets.clean_sms import clean_sms_dataset
from ml.datasets.clean_url import clean_url_dataset
from ml.datasets.pairing import build_merged_dataset

__all__ = ["clean_sms_dataset", "clean_url_dataset", "build_merged_dataset"]
