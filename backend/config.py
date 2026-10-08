"""
backend/config.py

Global system configuration and environment settings.
Reads configuration from environment variables / .env using Pydantic Settings.
"""

import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    USE_PYDANTIC_SETTINGS = True
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None
    USE_PYDANTIC_SETTINGS = False

BASE_DIR = Path(__file__).resolve().parent           # backend/
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bimodal Fraud Detection (Text + URL)"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Union[List[str], str] = ["*"]
    MAX_TEXT_LENGTH: int = 5000
    RATE_LIMIT: str = "100/minute"

    # Directory Paths
    PROJECT_ROOT_PATH: Path = PROJECT_ROOT
    MODEL_WEIGHTS_DIR: Path = PROJECT_ROOT / "model_weights"
    DATA_DIR: Path = PROJECT_ROOT / "data"
    STATIC_DIR: Path = PROJECT_ROOT / "frontend"
    RESULTS_DIR: Path = PROJECT_ROOT / "ml" / "experiments" / "results"

    # Specific Model Paths
    TEXT_MODEL_DIR: Path = PROJECT_ROOT / "model_weights" / "text"
    URL_MODEL_DIR: Path = PROJECT_ROOT / "model_weights" / "url"
    FUSION_MODEL_DIR: Path = PROJECT_ROOT / "model_weights" / "fusion"

    # Risk Thresholds
    RISK_CRITICAL_THRESHOLD: float = 80.0
    RISK_HIGH_THRESHOLD: float = 50.0
    RISK_MODERATE_THRESHOLD: float = 25.0
    RISK_THRESHOLD_HIGH: float = 50.0
    RISK_THRESHOLD_MEDIUM: float = 25.0

    if USE_PYDANTIC_SETTINGS:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore"
        )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        return ["*"]


# Singleton instance
settings = Settings(
    HOST=os.getenv("HOST", "0.0.0.0"),
    PORT=int(os.getenv("PORT", 8000)),
    ENVIRONMENT=os.getenv("ENVIRONMENT", "development"),
    LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
    CORS_ORIGINS=os.getenv("CORS_ORIGINS", "*"),
    MAX_TEXT_LENGTH=int(os.getenv("MAX_TEXT_LENGTH", 5000)),
    RATE_LIMIT=os.getenv("RATE_LIMIT", "100/minute"),
)
