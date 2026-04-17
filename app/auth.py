"""
Authentication module for VinFast Assistant
API key authentication with support for future JWT tokens
"""

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import os

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify API key authentication.
    Accepts AGENT_API_KEY (Railway/Render convention) or API_KEY_SECRET.
    In production, this should validate against a database or auth service.
    """
    expected = os.getenv("AGENT_API_KEY") or os.getenv("API_KEY_SECRET", "dev-api-key-change-in-production")

    if not api_key or api_key != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Include header: X-API-Key: <key>",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


def create_jwt_token(user_id: str) -> str:
    """
    Future JWT token creation (placeholder)
    Would use config.jwt_secret for signing
    """
    # Placeholder for future JWT implementation
    return f"jwt_token_for_{user_id}"


def verify_jwt_token(token: str) -> Optional[str]:
    """
    Future JWT token verification (placeholder)
    """
    # Placeholder for future JWT implementation
    if token.startswith("jwt_token_for_"):
        return token.replace("jwt_token_for_", "")
    return None
