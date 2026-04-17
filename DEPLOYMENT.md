# Deployment Information

## Public URL
https://day12-agent-deployment-production-9137.up.railway.app

## Platform
Railway (via CLI)

## Deploy Steps

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Login
railway login

# 3. Init project (trong thư mục repo)
railway init

# 4. Set environment variables
railway variables set OPENAI_API_KEY=sk-your-key
railway variables set AGENT_API_KEY=your-secret-key

# 5. Deploy
railway up

# 6. Get public URL
railway domain
```

## Test Commands

### Health Check
```bash
curl https://day12-agent-deployment-production-9137.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://day12-agent-deployment-production-9137.up.railway.app/chat \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho tôi biết giá VF 5", "session_id": "test"}'
```

### Swagger UI
https://day12-agent-deployment-production-9137.up.railway.app/docs

## Environment Variables Set
- `PORT`
- `AGENT_API_KEY`
- `OPENAI_API_KEY`
- `RATE_LIMIT_PER_MINUTE`
- `MONTHLY_BUDGET_USD`
- `LOG_LEVEL`

## Screenshots
*(Sẽ bổ sung sau khi deploy)*
- [ ] Deployment dashboard
- [ ] Service running
- [ ] Test results
