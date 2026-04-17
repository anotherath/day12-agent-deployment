# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found in basic app.py

1. **API key hardcoded**: `OPENAI_API_KEY = "sk-..."` trong code — nguy hiểm vì lộ secret khi push lên Git
2. **Port cố định**: `app.run(port=5000)` — không linh hoạt, cloud platform thường cấp port qua env var
3. **Debug mode bật**: `debug=True` — lộ stack trace, thông tin nhạy cảm cho attacker
4. **Không có health check**: Platform không biết app còn sống hay đã crash
5. **Không xử lý shutdown**: Container bị kill đột ngột, requests đang xử lý bị mất

### Exercise 1.3: Comparison table

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars | Dễ thay đổi, không lộ secret, linh hoạt theo môi trường |
| Health check | Không có | `/health` endpoint | Platform biết khi nào restart container |
| Logging | `print()` | JSON structured | Dễ parse, tích hợp với monitoring tools |
| Shutdown | Đột ngột | Graceful (SIGTERM) | Hoàn thành requests đang xử lý trước khi tắt |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions

1. **Base image**: `python:3.11-slim` — phiên bản Python 3.11, dùng Debian slim (nhẹ)
2. **Working directory**: `/app` — nơi code được copy vào trong container
3. **COPY requirements.txt trước**: Tận dụng Docker layer cache — nếu requirements không đổi, không cần reinstall dependencies
4. **CMD vs ENTRYPOINT**:
   - `CMD`: Default command, có thể override khi run container
   - `ENTRYPOINT`: Command cố định, arguments được append vào

### Exercise 2.3: Multi-stage build

- **Stage 1 (Builder)**: Cài dependencies, compile — cần gcc, build tools
- **Stage 2 (Runtime)**: Chỉ copy packages đã build, bỏ build tools → image nhỏ hơn
- **Image nhỏ hơn vì**: Không chứa gcc, headers, cache — chỉ giữ runtime cần thiết

### Exercise 2.4: Docker Compose

Architecture:
```
Client → Nginx (port 80) → Agent (port 8000)
                                ↓
                            Redis (port 6379)
```

Services: agent + redis. Agent connect Redis qua hostname `redis` trong Docker network.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment

```bash
railway login
railway init
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
railway up
railway domain
```

### Exercise 3.2: Render vs Railway

| | Render | Railway |
|--|--------|---------|
| Config file | `render.yaml` | `railway.toml` |
| Deploy | Blueprint / Manual | CLI |
| Free tier | 750h/month | $5 credit |
| Region | Singapore, US | US, EU |

---

## Part 4: API Security

### Exercise 4.1: API Key authentication

- **Check ở đâu**: `verify_api_key()` trong `app/auth.py` — so sánh `X-API-Key` header với `AGENT_API_KEY` env var
- **Sai key**: Trả về HTTP 401 Unauthorized
- **Rotate key**: Đổi giá trị `AGENT_API_KEY` env var, restart container

### Exercise 4.3: Rate limiting

- **Algorithm**: Sliding window — theo dõi timestamps trong 60 giây qua
- **Limit**: 10 requests/minute per user
- **Bypass admin**: Có thể thêm whitelist key hoặc role-based check

### Exercise 4.4: Cost guard implementation

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(redis.get(key) or 0)
    if current + estimated_cost > 10:
        return False
    
    redis.incrbyfloat(key, estimated_cost)
    redis.expire(key, 32 * 24 * 3600)
    return True
```

---

## Part 5: Scaling & Reliability

### Exercise 5.1: Health checks

```python
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    return {"ready": True}
```

### Exercise 5.2: Graceful shutdown

```python
def _handle_signal(signum, _frame):
    logger.info(f"Received signal {signum}, shutting down gracefully...")

signal.signal(signal.SIGTERM, _handle_signal)
```

### Exercise 5.3: Stateless design

**Trước (anti-pattern)**:
```python
SESSIONS = {}  # In-memory, mất khi restart
```

**Sau (stateless)**:
```python
# Dùng Redis hoặc external storage
redis.set(f"session:{session_id}", json.dumps(history))
```

Lý do: Khi scale ra nhiều instances, mỗi instance có memory riêng. Request 1 đến instance A, request 2 đến instance B → mất context nếu lưu in-memory.

### Exercise 5.4: Load balancing

```bash
docker compose up --scale agent=3
```

Nginx phân tán requests round-robin đến 3 agent instances. Nếu 1 instance die, health check fail → Nginx ngừng gửi traffic đến instance đó.
