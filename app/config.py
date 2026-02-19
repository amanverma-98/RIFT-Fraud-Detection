from pydantic_settings import BaseSettings # type: ignore
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Fraud Detection System"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # CORS
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/fraud_detection.log"

    # Upload settings
    max_upload_size_mb: int = 100
    allowed_csv_extensions: list = [".csv"]
    upload_path: str = "uploads"

    # Graph detection settings
    fraud_threshold: float = 0.7
    min_transaction_amount: float = 0.0

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
