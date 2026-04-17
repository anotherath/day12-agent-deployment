# Deployment Information

## Public URL
*(Sẽ cập nhật sau khi deploy lên Render)*

## Platform
Render (via Blueprint)

## Test Commands

### Health Check
```bash
curl https://your-app.onrender.com/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://your-app.onrender.com/chat \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"message": "Cho tôi biết giá VF 5", "session_id": "test"}'
```

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
