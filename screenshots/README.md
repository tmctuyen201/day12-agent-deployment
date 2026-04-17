# Screenshots Directory

This directory contains screenshots of the deployment process and application testing.

## Required Screenshots for Day 12 Lab Submission:

1. **Railway Deployment Dashboard**
   - `railway-dashboard.png` - Railway project dashboard showing successful deployment

2. **Application Running**
   - `app-running.png` - Browser showing the API is accessible
   - `swagger-ui.png` - FastAPI Swagger documentation page

3. **Health Check Results**
   - `health-check.png` - Terminal showing successful health check response

4. **API Testing**
   - `api-test-success.png` - Successful API call with authentication
   - `api-test-auth-fail.png` - Failed API call without authentication (401 error)
   - `rate-limit-test.png` - Rate limiting in action (429 error)

5. **Metrics Dashboard**
   - `metrics-endpoint.png` - Metrics endpoint showing usage statistics

## How to Capture Screenshots:

### Railway Dashboard:
1. Go to railway.app
2. Select your project
3. Take screenshot of the deployment status

### API Testing:
```bash
# Health check
curl https://your-app-url/health | jq .

# API test (replace YOUR_API_KEY)
curl -X POST https://your-app-url/ask \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "test"}' | jq .

# Metrics
curl -H "X-API-Key: YOUR_API_KEY" https://your-app-url/metrics | jq .
```

### Swagger UI:
Visit `https://your-app-url/docs` in browser and screenshot

## File Naming Convention:
- Use descriptive names
- Include date if multiple versions
- Format: PNG or JPG
- Max size: 5MB per file

## Submission Requirement:
Include at least 3 screenshots showing:
- Successful deployment
- Working API with authentication
- Health check passing