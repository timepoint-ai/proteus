# Load Testing

Load tests for Clockchain Prediction Market API using [Locust](https://locust.io/).

## Installation

```bash
# Install test dependencies
pip install -e ".[test]"

# Or install locust directly
pip install locust
```

## Quick Start

```bash
# Start the Flask server first
python main.py

# Run load tests with web UI (http://localhost:8089)
locust -f tests/load/locustfile.py --host=http://localhost:5000

# Run headless (no UI)
locust -f tests/load/locustfile.py --host=http://localhost:5000 --headless -u 50 -r 5 -t 60s
```

## Test Scenarios

### User Types

| User Type | Weight | Wait Time | Description |
|-----------|--------|-----------|-------------|
| APIUser | 3 | 1-3s | Typical API consumer |
| AuthenticatedUser | 1 | 2-5s | Tests auth flows |
| HeavyUser | 1 | 0.5-1.5s | Stress tests rate limiting |
| BrowsingUser | 2 | 3-8s | Web page browsing |

### Endpoints Tested

**Health & Status:**
- `GET /api/base/health` - API health check
- `GET /api/chain/stats` - Platform statistics

**Markets:**
- `GET /api/chain/markets` - List all markets
- `GET /api/chain/markets?status=active` - Filtered markets

**Actors:**
- `GET /api/chain/actors` - List actors

**Genesis NFT:**
- `GET /api/chain/genesis/holders` - NFT holders

**Authentication:**
- `GET /auth/nonce/{address}` - Request nonce
- `GET /auth/jwt-status` - Check JWT status
- `POST /auth/verify` - Verify signature
- `POST /auth/refresh` - Refresh token
- `GET /api/embedded/auth/status` - Embedded wallet status
- `POST /api/embedded/auth/send-otp` - Send OTP

**Pages:**
- `GET /` - Homepage
- `GET /dashboard` - User dashboard
- `GET /clockchain/` - Markets list
- `GET /actors/` - Actors list

## Configuration Presets

```bash
# View all presets
python tests/load/config.py
```

| Preset | Users | Spawn Rate | Duration | Use Case |
|--------|-------|------------|----------|----------|
| smoke | 10 | 2/s | 30s | Quick validation |
| default | 50 | 5/s | 60s | Standard test |
| medium | 100 | 10/s | 120s | Typical load |
| stress | 500 | 25/s | 300s | Stress testing |
| spike | 200 | 50/s | 60s | Traffic surge |

## Running Specific Tests

Use tags to run specific test categories:

```bash
# Read-only endpoints only
locust -f tests/load/locustfile.py --host=http://localhost:5000 --tags read

# Authentication tests only
locust -f tests/load/locustfile.py --host=http://localhost:5000 --tags auth

# Health checks only
locust -f tests/load/locustfile.py --host=http://localhost:5000 --tags health

# Multiple tags
locust -f tests/load/locustfile.py --host=http://localhost:5000 --tags markets,read
```

## Output & Reports

### Web UI

Access `http://localhost:8089` when running without `--headless` for:
- Real-time charts
- Request statistics
- Failure tracking
- Download CSV reports

### Headless Output

```bash
# Save HTML report
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
  --headless -u 50 -r 5 -t 60s --html=report.html

# Save CSV statistics
locust -f tests/load/locustfile.py --host=http://localhost:5000 \
  --headless -u 50 -r 5 -t 60s --csv=results
```

## Performance Targets

| Endpoint | Target P95 | Max Failures |
|----------|-----------|--------------|
| /api/base/health | < 100ms | 0% |
| /api/chain/markets | < 500ms | < 1% |
| /api/chain/stats | < 500ms | < 1% |
| /auth/nonce/* | < 200ms | < 1% |
| Page loads | < 1000ms | < 2% |

## Troubleshooting

### Rate Limiting

The app uses Flask-Limiter. If you see 429 errors:
- This is expected behavior for HeavyUser tests
- Check rate limit configuration in `config.py`

### Connection Errors

If you see connection refused errors:
1. Ensure Flask server is running
2. Check the host URL is correct
3. Verify firewall settings

### High Latency

If latency is high:
1. Check if blockchain RPC is responding
2. Monitor Redis cache hit rates
3. Check database connection pool

## CI/CD Integration

```yaml
# Example GitHub Actions step
- name: Run Load Tests
  run: |
    locust -f tests/load/locustfile.py \
      --host=http://localhost:5000 \
      --headless -u 10 -r 2 -t 30s \
      --exit-code-on-error 1
```
