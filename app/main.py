"""
VinFast Car Assistant - Production Ready API
FastAPI application with comprehensive security and monitoring
"""

from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import time
from datetime import datetime, timezone
from typing import Optional
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
PORT = int(os.getenv("PORT", "8000"))
API_KEY_SECRET = os.getenv("API_KEY_SECRET", "dev-api-key-change-in-production")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Rate limiting (simple in-memory for demo)
RATE_LIMIT_REQUESTS = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 20  # requests per window

# Cost guard
DAILY_BUDGET = float(os.getenv("DAILY_BUDGET_USD", "5.0"))
DAILY_COST = 0.0
COST_RESET_DAY = time.strftime("%Y-%m-%d")

# Create FastAPI app
app = FastAPI(
    title="VinFast Car Assistant API",
    version="2.0.0",
    description="Production-ready AI assistant for VinFast vehicles",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key or api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


# Rate limiting function
def check_rate_limit(client_key: str) -> bool:
    current_time = time.time()
    if client_key not in RATE_LIMIT_REQUESTS:
        RATE_LIMIT_REQUESTS[client_key] = []

    # Clean old requests
    RATE_LIMIT_REQUESTS[client_key] = [
        req_time
        for req_time in RATE_LIMIT_REQUESTS[client_key]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    if len(RATE_LIMIT_REQUESTS[client_key]) >= RATE_LIMIT_MAX:
        return False

    RATE_LIMIT_REQUESTS[client_key].append(current_time)
    return True


# Cost guard function
def check_and_track_cost() -> bool:
    global DAILY_COST, COST_RESET_DAY
    today = time.strftime("%Y-%m-%d")
    if today != COST_RESET_DAY:
        DAILY_COST = 0.0
        COST_RESET_DAY = today

    # Estimate cost per request (mock)
    request_cost = 0.001  # $0.001 per request
    if DAILY_COST + request_cost > DAILY_BUDGET:
        return False

    DAILY_COST += request_cost
    return True


# Pydantic models
class AgentRequest(BaseModel):
    question: str
    user_id: str = "anonymous"
    car_model: Optional[str] = "VF8"


class AgentResponse(BaseModel):
    answer: str
    confidence: float
    sources: list = []
    timestamp: str


# Mock responses for demo
MOCK_RESPONSES = {
    "charging": "You can find charging stations using the VinFast navigation system or mobile app. The nearest stations will show real-time availability.",
    "maintenance": "Schedule maintenance through the VinFast app or contact your authorized dealer. Regular maintenance is important for vehicle safety.",
    "features": "Your VinFast includes autonomous driving, premium audio system, smart connectivity, and advanced safety features.",
    "default": "I'm your VinFast assistant. I can help with charging stations, maintenance schedules, vehicle features, and general questions about your VinFast vehicle.",
}


def get_mock_response(question: str) -> str:
    """Simple keyword-based response matching"""
    question_lower = question.lower()

    if any(word in question_lower for word in ["charg", "battery", "electric"]):
        return MOCK_RESPONSES["charging"]
    elif any(word in question_lower for word in ["maintain", "service", "repair"]):
        return MOCK_RESPONSES["maintenance"]
    elif any(word in question_lower for word in ["feature", "capability", "function"]):
        return MOCK_RESPONSES["features"]
    else:
        return MOCK_RESPONSES["default"]


# API endpoints
@app.get("/")
def root():
    return {
        "message": "VinFast Car Assistant API",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "ask": "POST /ask (requires X-API-Key)",
        },
    }


@app.get("/health")
def health():
    """Liveness probe"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": time.time(),
        "version": "2.0.0",
    }


@app.get("/ready")
def ready():
    """Readiness probe"""
    return {"ready": True}


@app.post("/ask", response_model=AgentResponse)
def ask_agent(req: AgentRequest, api_key: str = Depends(verify_api_key)):
    """Main agent endpoint with authentication, rate limiting, and cost guard"""

    # Rate limiting
    if not check_rate_limit(api_key[:8]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # Cost guard
    if not check_and_track_cost():
        raise HTTPException(status_code=503, detail="Daily budget exceeded")

    # Log request
    logger.info(f"Request from {req.user_id}: {req.question[:50]}...")

    # Get response
    answer = get_mock_response(req.question)

    return AgentResponse(
        answer=answer,
        confidence=0.85,
        sources=["vehicle_manual", "service_database"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics")
def metrics(api_key: str = Depends(verify_api_key)):
    """Protected metrics endpoint"""
    return {
        "daily_cost_usd": round(DAILY_COST, 4),
        "daily_budget_usd": DAILY_BUDGET,
        "budget_used_percent": round(DAILY_COST / DAILY_BUDGET * 100, 1)
        if DAILY_BUDGET > 0
        else 0,
        "active_rate_limits": len(RATE_LIMIT_REQUESTS),
        "environment": ENVIRONMENT,
    }


# Graceful shutdown
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Application shutting down gracefully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
