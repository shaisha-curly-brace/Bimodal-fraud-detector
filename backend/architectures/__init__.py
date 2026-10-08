"""backend.architectures package"""
from backend.architectures.text_model import TextFraudClassifier
from backend.architectures.url_model import URLFraudClassifier
from backend.architectures.fusion_model import MultimodalFusionClassifier

__all__ = ["TextFraudClassifier", "URLFraudClassifier", "MultimodalFusionClassifier"]
