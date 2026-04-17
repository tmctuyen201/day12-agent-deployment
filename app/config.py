"""
Configuration management for VinFast Assistant
12-factor app compliant - all config from environment variables
"""

import os
from dataclasses import dataclass


@dataclass
class Config:
    # Server
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Security
    api_key_secret: str = os.getenv(
        "API_KEY_SECRET", "dev-api-key-change-in-production"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-jwt-secret-change-in-production")

    # Rate limiting
    rate_limit_max: int = int(os.getenv("RATE_LIMIT_MAX", "20"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

    # Cost guard
    daily_budget_usd: float = float(os.getenv("DAILY_BUDGET_USD", "5.0"))

    # Redis (optional for scaling)
    redis_url: str = os.getenv("REDIS_URL", "")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()
