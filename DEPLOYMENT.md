# VinFast Assistant - Deployment Information

## Public URL
https://vinfast-assistant-production.up.railway.app

## Platform
Railway (using Nixpacks for Python deployment)

## Test Commands

### Health Check
```bash
curl https://vinfast-assistant-production.up.railway.app/health
# Expected: {"status": "ok", "timestamp": "...", "uptime_seconds": 123, "version": "2.0.0"}
```

### API Test (with authentication)
```bash
curl -X POST https://vinfast-assistant-production.up.railway.app/ask \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I find charging stations?", "user_id": "test123"}'
# Expected: 200 OK with JSON response
```

### Rate Limiting Test
```bash
# This should work (under limit)
curl -X POST https://vinfast-assistant-production.up.railway.app/ask \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "test123"}'

# After 20+ requests in 1 minute, should return 429:
# {"detail": "Rate limit exceeded"}
```

### Authentication Required Test
```bash
curl -X POST https://vinfast-assistant-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "test123"}'
# Expected: 401 Unauthorized
```

## Environment Variables Set
- `PORT` - Railway sets automatically
- `API_KEY_SECRET` - Secure API key for authentication
- `ENVIRONMENT=production`
- `DAILY_BUDGET_USD=5.0`
- `RATE_LIMIT_MAX=20`
- `RATE_LIMIT_WINDOW=60`
- `LOG_LEVEL=INFO`

## Features Implemented

### Security
- ✅ API Key authentication (`X-API-Key` header)
- ✅ Rate limiting (20 requests/minute sliding window)
- ✅ Cost guard (daily budget tracking)
- ✅ Input validation (Pydantic models)
- ✅ No hardcoded secrets

### Reliability
- ✅ Health checks (`/health` endpoint)
- ✅ Readiness checks (`/ready` endpoint)
- ✅ Graceful shutdown handling
- ✅ Structured logging
- ✅ Error handling with proper HTTP status codes

### Deployment
- ✅ Railway deployment configuration
- ✅ Docker multi-stage build
- ✅ Environment-based configuration
- ✅ Production-ready settings

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup
```bash
# Clone repository
git clone <your-repo-url>
cd vinfast-deployment

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Run locally
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development
```bash
# Build and run with Docker Compose
docker compose up --build

# Access at http://localhost:8000
```

## API Documentation

Once deployed, visit:
- Swagger UI: `https://your-app-url/docs`
- ReDoc: `https://your-app-url/redoc`

## Monitoring

### Metrics Endpoint (Protected)
```bash
curl -H "X-API-Key: YOUR_API_KEY" https://your-app-url/metrics
# Returns: budget usage, rate limiting stats, etc.
```

## Screenshots

Screenshots are included in the `screenshots/` directory:
- Railway deployment dashboard
- Application running
- API testing results
- Health check responses