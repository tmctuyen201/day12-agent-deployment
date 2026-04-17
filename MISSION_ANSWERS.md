# Day 12 Lab - Mission Answers

# VinFast Car Assistant — Deploy to Production

---

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns in `01-localhost-vs-production/develop/app.py`

Found 5+ issues:

1. **Hardcoded API key** — `openai.api_key = "sk-..."` directly in code. If code is pushed to GitHub, the key is leaked. Fix: use environment variable `os.getenv("OPENAI_API_KEY")`.

2. **Hardcoded port** — `uvicorn.run(app, host="127.0.0.1", port=8000)`. Port is fixed, can't change via environment. Fix: read from `os.getenv("PORT", "8000")`.

3. **Debug mode on in production** — `debug=True` exposes internal errors and stack traces to users. Fix: set `debug=False` in production.

4. **No health check endpoint** — The app has no `/health` or `/ready` endpoint. Cloud platforms (Railway, Render, Cloud Run) rely on health checks to know when to restart a container. Without it, a crashed app keeps receiving traffic.

5. **No graceful shutdown** — When the container is stopped (SIGTERM), requests in progress are dropped immediately. In production, the server should finish processing in-flight requests before shutting down.

6. **No structured logging** — Using `print()` statements instead of structured JSON logs. Hard to search/parse in production log aggregation tools.

7. **No environment variable separation** — All config is hardcoded. Different environments (dev/staging/prod) need different configs.

### Exercise 1.3: Comparison table

| Feature        | Basic (develop)     | Advanced (production)          | Why Important?                                                        |
| -------------- | ------------------- | ------------------------------ | --------------------------------------------------------------------- |
| Config         | Hardcoded values    | Env variables (`os.getenv`)    | Different configs per environment; no secrets in code                 |
| Health check   | None                | `/health` + `/ready` endpoints | Platform knows when to restart; load balancer routes traffic properly |
| Logging        | `print()`           | JSON structured logging        | Machine-readable; searchable; aggregatable in monitoring tools        |
| Shutdown       | Instant (`Ctrl+C`)  | Graceful (SIGTERM handler)     | Complete in-flight requests; don't drop user data                     |
| Error handling | Expose stack traces | Return JSON errors             | Don't leak internal info to end users                                 |
| CORS           | `*` or none         | Specific allowed origins       | Prevent unauthorized cross-site requests                              |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image:** `python:3.11-slim` — includes OS (Debian) and Python 3.11 runtime. Slim variant is smaller (~45MB vs ~900MB for full).

2. **Working directory:** `/app` — the directory inside the container where the application code lives.

3. **COPY requirements.txt first:** Docker caches layers. If requirements.txt hasn't changed, the pip install layer is reused even if code changed. If you copy code before requirements.txt, any code change invalidates the pip cache.

4. **CMD vs ENTRYPOINT:**
   - `CMD` — default arguments that CAN be overridden at `docker run` time
   - `ENTRYPOINT` — fixed command that the container ALWAYS runs; args from CMD are appended
   - In practice: `ENTRYPOINT ["python"]` + `CMD ["app.py"]` means "always run Python, with app.py as default"

### Exercise 2.2: Build and run container

```bash
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .
docker run -p 8000:8000 my-agent:develop
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

Image size was checked: `docker images my-agent:develop` — develop image is large (~900MB) because it uses full Python image.

### Exercise 2.3: Multi-stage build

- **Stage 1 (builder):** Installs all dependencies including build tools (gcc, libpq-dev for psycopg)
- **Stage 2 (runtime):** Copies only the installed packages and application code from builder
- **Result:** Final image is slim (~150-200MB vs ~900MB for single-stage). No build tools in final image = smaller attack surface.

Image size comparison:

- Single-stage (develop): ~900 MB
- Multi-stage (production): ~150-200 MB
- Reduction: ~75-80%

### Exercise 2.4: Architecture diagram

```
Client (Browser/App)
        │
        ▼
┌──────────────────┐
│  Nginx (port 80) │   ← Reverse proxy + load balancer
└────────┬─────────┘
         │
    ┌────┴────┬────────────┐
    ▼         ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐
│Agent 1 │ │Agent 2 │ │Agent 3 │  ← FastAPI agent (replicas)
│ :8000  │ │ :8000  │ │ :8000  │
└───┬────┘ └───┬────┘ └───┬────┘
    └──────────┼──────────┘
                ▼
         ┌──────────┐
         │  Redis   │   ← Session storage, rate limiting
         │  :6379   │
         └──────────┘
```

Stack command: `docker compose up`

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

**Steps taken:**

```bash
npm i -g @railway/cli
railway login
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
railway variables set REDIS_URL=redis://...
railway up
railway domain
```

**Result:** Public URL obtained (e.g., `https://vinfast-agent.up.railway.app`)

**Verification:**

```bash
curl https://vinfast-agent.up.railway.app/api/health
# → {"status":"ok", "provider":"openai", ...}

curl -X POST https://vinfast-agent.up.railway.app/api/agent \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "Cách sạc pin VF8?", "car_model": "VF8"}'
# → {"text": "...", "sources": [...], "confidence": 0.9}
```

### Exercise 3.2: Comparison `railway.toml` vs `render.yaml`

| Aspect           | railway.toml                  | render.yaml                              |
| ---------------- | ----------------------------- | ---------------------------------------- |
| Format           | TOML                          | YAML                                     |
| Build command    | Auto-detected from Dockerfile | Explicit `buildCommand`                  |
| Start command    | Explicit `startCommand`       | Explicit `buildCommand` + `startCommand` |
| Health check     | `healthcheckPath`             | Health check via healthcheck script      |
| Environment vars | Set via CLI or dashboard      | Listed under `envVars`                   |
| Auto-deploy      | `autoDeploy: true`            | Auto-deploy on GitHub push               |

Both support Docker-based deployment. Railway is simpler for quick prototyping; Render integrates better with GitHub for CI/CD.

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

API key is checked in `auth.py`:

- Key sent in header `X-API-Key: <key>` (or `Authorization: Bearer <key>`)
- Server compares against `AGENT_API_KEY` env variable
- Missing or wrong key → 401 Unauthorized
- Correct key → request proceeds

**Test:**

```bash
# Without key → 401
curl http://localhost:8000/api/agent \
  -X POST -d '{"query":"test","car_model":"VF8"}'
# → 401 "API key required"

# With key → 200
curl -H "X-API-Key: secret-key-123" \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     http://localhost:8000/api/agent \
     -X POST -d '{"query":"test","car_model":"VF8"}'
```

### Exercise 4.2: JWT authentication

JWT flow:

1. User logs in → receives JWT token (expires in 60 min)
2. Subsequent requests include `Authorization: Bearer <token>`
3. Server validates signature and expiry
4. Token contains `username` and `role` — no DB lookup needed per request

```bash
# Get token
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"student","password":"demo123"}'

# Use token
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/agent \
     -X POST -d '{"query":"test","car_model":"VF8"}'
```

### Exercise 4.3: Rate limiting

Algorithm: **Sliding Window Counter**

- Each user has a deque of timestamps
- Requests older than 60s are removed (window slides)
- More than 10 requests in window → 429 Too Many Requests
- Headers include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`

**Test:**

```bash
for i in {1..15}; do
  curl -H "Authorization: Bearer $TOKEN" \
       http://localhost:8000/api/agent \
       -X POST -d '{"query":"test '$i'","car_model":"VF8"}'
done
# After 10th request → 429
```

### Exercise 4.4: Cost guard implementation

Budget: $10/month per user, tracked in Redis with key `budget:{user_id}:{YYYY-MM}`.

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    current = float(r.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 24 * 3600)  # 32 days
    return True
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

Two endpoints implemented:

- `/health` (liveness) → Returns 200 if process is alive. Used by container orchestrator to decide restart.
- `/ready` (readiness) → Returns 200 if Redis connection is OK and app is ready to serve traffic. Returns 503 if not ready.

```bash
curl http://localhost:8000/api/health
# → {"status":"ok", "version":"1.0.0", "uptime_seconds": 1234.5}

curl http://localhost:8000/api/ready
# → {"ready": true} or HTTP 503
```

### Exercise 5.2: Graceful shutdown

Implemented via `signal.SIGTERM` handler:

1. Set `_is_ready = False` → load balancer stops routing
2. Wait for in-flight requests to complete (timeout: 30s)
3. Close Redis connection
4. Exit cleanly

```bash
python app.py &
PID=$!
kill -TERM $PID
# Logs show: graceful shutdown message
```

### Exercise 5.3: Stateless design

**Anti-pattern (stateful):**

```python
conversation_history = {}  # ← stored in memory

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])  # ← per-instance
```

**Correct (stateless):**

```python
@app.post("/ask")
def ask(user_id: str, question: str):
    history = r.lrange(f"history:{user_id}", 0, -1)  # ← stored in Redis
    # All instances read from same Redis → consistent state
```

Why: When scaling to 3 instances, each has different memory. If user hits instance 1, then instance 2, they have no shared history. Redis fixes this.

### Exercise 5.4: Load balancing

```bash
docker compose up --scale agent=3
```

Nginx distributes requests across 3 agent instances using round-robin. If one instance dies, Nginx detects and routes to healthy instances.

### Exercise 5.5: Test stateless design

```bash
python test_stateless.py
# → Creates conversation on instance 1
# → Kills instance 1
# → Continues conversation on instance 2
# → History preserved via Redis ✓
```
