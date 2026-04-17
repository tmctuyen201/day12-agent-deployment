"""
VinFast Car Assistant - Production Ready API
FastAPI application with comprehensive security and monitoring.
"""

import signal
import sys
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from app.auth import verify_api_key
from app.rate_limiter import rate_limiter
from app.cost_guard import cost_guard
from utils.mock_llm import ask

# Configure logging
import logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
APP_VERSION = "2.0.0"
START_TIME = time.time()

# ── Graceful shutdown ─────────────────────────────────────────────────────────
shutdown_requested = False


def handle_sigterm(signum, frame):
    global shutdown_requested
    logger.info("SIGTERM received — initiating graceful shutdown")
    shutdown_requested = True


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"VinFast Assistant starting (env={ENVIRONMENT})")
    yield
    logger.info("VinFast Assistant shutting down — all requests drained")


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="VinFast Car Assistant API",
    version=APP_VERSION,
    description="Production-ready AI assistant for VinFast vehicles",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ENVIRONMENT == "development" else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ───────────────────────────────────────────────────────────
class AgentRequest(BaseModel):
    question: str
    user_id: str = "anonymous"
    car_model: Optional[str] = "VF8"


class AgentResponse(BaseModel):
    answer: str
    confidence: float
    sources: list = []
    timestamp: str


# ── Public endpoints ───────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "VinFast Car Assistant API",
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "GET /health",
            "ready":  "GET /ready",
            "ask":    "POST /ask (requires X-API-Key)",
        },
    }


@app.get("/health")
def health():
    """Liveness probe — always returns 200 if process is alive."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "version": APP_VERSION,
    }


@app.get("/ready")
def ready():
    """Readiness probe — returns 200 when app is ready to serve traffic."""
    if shutdown_requested:
        raise HTTPException(status_code=503, detail="Shutting down")
    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Protected endpoints ────────────────────────────────────────────────────────
@app.post("/ask", response_model=AgentResponse)
def ask_agent(req: AgentRequest, api_key: str = Depends(verify_api_key)):
    """Main agent endpoint — auth + rate-limit + cost-guard + LLM."""

    # 1. Rate limiting (keyed by first 8 chars of API key)
    client_key = api_key[:8]
    if not rate_limiter.is_allowed(client_key):
        reset_in = rate_limiter.get_reset_time(client_key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(reset_in),
            },
        )

    # 2. Cost guard
    if not cost_guard.check_budget():
        raise HTTPException(status_code=503, detail="Daily budget exceeded")

    # 3. Log
    logger.info(f"[{req.user_id}] question={req.question[:60]!r}")

    # 4. Call LLM
    answer = ask(req.question)

    # 5. Record cost
    cost_guard.record_cost()

    return AgentResponse(
        answer=answer,
        confidence=0.90,
        sources=["vehicle_manual", "vinfast_kb"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/metrics")
def metrics(api_key: str = Depends(verify_api_key)):
    """Protected metrics endpoint."""
    budget = cost_guard.get_budget_status()
    return {
        **budget,
        "active_rate_limit_keys": rate_limiter.active_keys_count(),
        "environment": ENVIRONMENT,
    }


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
