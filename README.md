# VinFast Car Assistant - Production Deployment

A production-ready AI assistant for VinFast vehicles with comprehensive security, monitoring, and scaling features.

## 🚀 Quick Start

### Deploy to Railway (Recommended)

1. **Fork this repository** to your GitHub account
2. **Connect to Railway**:
   - Go to [Railway.app](https://railway.app)
   - Connect your GitHub repository
   - Railway auto-detects `railway.toml` and deploys
3. **Set environment variables** in Railway dashboard:
   ```
   API_KEY_SECRET=your-secure-api-key-here
   ENVIRONMENT=production
   DAILY_BUDGET_USD=5.0
   ```
4. **Your app is live!** 🎉

### Local Development

#### Prerequisites
- Python 3.11+
- pip
- Docker (optional)

#### Setup
```bash
# Clone repository
git clone <your-repo-url>
cd vinfast-deployment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your values

# Run the application
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### With Docker
```bash
# Build and run
docker compose up --build

# Access at http://localhost:8000
```

## 📋 API Endpoints

### Public Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /ready` - Readiness check

### Protected Endpoints (Require X-API-Key header)
- `POST /ask` - Main agent endpoint
- `GET /metrics` - Usage metrics

### Example Usage
```bash
# Health check
curl http://localhost:8000/health

# Ask a question (with API key)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I find charging stations?", "user_id": "user123"}'
```

## 🔒 Security Features

- **API Key Authentication** - Required for all agent endpoints
- **Rate Limiting** - 20 requests per minute per API key
- **Cost Guard** - Daily budget tracking ($5/day default)
- **Input Validation** - Pydantic models for all requests
- **No Hardcoded Secrets** - All config from environment variables

## 🏗️ Architecture

```
vinfast-deployment/
├── app/                    # Main application
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration management
│   ├── auth.py            # Authentication logic
│   ├── rate_limiter.py    # Rate limiting
│   └── cost_guard.py      # Budget protection
├── utils/                 # Utilities
│   └── mock_llm.py        # Mock LLM responses
├── screenshots/           # Deployment screenshots
├── Dockerfile             # Multi-stage container build
├── docker-compose.yml     # Local development stack
├── requirements.txt       # Python dependencies
├── railway.toml          # Railway deployment config
├── .env.example          # Environment template
├── .dockerignore         # Docker exclusions
├── MISSION_ANSWERS.md    # Lab answers
├── DEPLOYMENT.md         # Deployment documentation
└── README.md             # This file
```

## 🧪 Testing

### Automated Tests
```bash
# Run health checks
curl http://localhost:8000/health
curl http://localhost:8000/ready

# Test authentication (should fail without API key)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'

# Test with API key (should work)
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "test"}'
```

### Rate Limiting Test
```bash
# Run this multiple times quickly
for i in {1..25}; do
  curl -X POST http://localhost:8000/ask \
    -H "X-API-Key: your-api-key" \
    -H "Content-Type: application/json" \
    -d '{"question": "test"}'
done
# Should see 429 errors after 20 requests
```

## 📊 Monitoring

### Health Checks
- **Liveness**: `/health` - Application is running
- **Readiness**: `/ready` - Application can handle requests

### Metrics (Protected)
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/metrics
```

Returns:
```json
{
  "daily_cost_usd": 0.02,
  "daily_budget_usd": 5.0,
  "remaining_budget_usd": 4.98,
  "budget_used_percent": 0.4,
  "active_rate_limits": 1,
  "environment": "production"
}
```

## 🚀 Deployment Options

### Railway (Recommended)
- ✅ Automatic scaling
- ✅ Built-in health checks
- ✅ Environment variable management
- ✅ Zero-config deployment

### Docker
- ✅ Multi-stage build (< 200MB)
- ✅ Production-ready container
- ✅ Health checks included

### Other Platforms
- **Render**: Use `render.yaml` (included)
- **Google Cloud Run**: Use `service.yaml` and `cloudbuild.yaml`
- **AWS/Heroku**: Standard Python deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is part of Day 12 Lab submission.

## 📞 Support

For issues or questions:
- Check `DEPLOYMENT.md` for detailed deployment info
- Review Railway build logs for deployment issues
- Test locally first before deploying

---

**Built with FastAPI, deployed on Railway 🚀**