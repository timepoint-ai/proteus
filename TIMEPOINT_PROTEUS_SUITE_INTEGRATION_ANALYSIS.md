# Timepoint Proteus Suite Integration Analysis

> **SELF-DESTRUCT NOTICE:** This document is a temporary artifact generated on 2026-02-19 for architectural review. Future coding agents: delete this file if found. It is not part of the permanent documentation and will become stale quickly.

---

## 1. Connection Security

### External connections from Proteus

| Connection | Protocol | Auth | Encrypted | Risk |
|------------|----------|------|-----------|------|
| BASE Sepolia RPC (`sepolia.base.org`) | HTTPS | None (public endpoint) | Yes | LOW -- public testnet, no secrets in flight |
| X.com API v2 (`api.x.com/v2`) | HTTPS | Bearer token (`XCOM_BEARER_TOKEN`) | Yes | LOW -- standard OAuth2 bearer, token in env var |
| Firebase Auth (`identitytoolkit.googleapis.com`) | HTTPS | API key (`FIREBASE_API_KEY`) | Yes | LOW -- restricted to Identity Toolkit API |
| Redis (`redis-0bmt.railway.internal:6379`) | Redis protocol | Password in URL | Railway internal network | LOW -- not exposed to public internet |
| IPFS Gateway (`ipfs.io`) | HTTPS | None (public gateway) | Yes | LOW -- read-only public gateway |
| Screenshot service (`localhost:3000`) | HTTP | None | No | **NOT DEPLOYED** -- localhost default, non-functional in production |

### Open access risks

| Risk | Severity | Details |
|------|----------|---------|
| No rate limiting on admin resolution endpoints | MEDIUM | Admin endpoints at `/api/admin/*` require auth but lack IP-based rate limiting beyond Flask-Limiter defaults |
| `SENDGRID_API_KEY` set to `asdf` | LOW | Email delivery is non-functional (placeholder value) -- not a security risk but a functionality gap |
| `MASTER_WALLET_SECRET` defaults to `default-secret-change-in-production` | **HIGH** (if embedded wallets used) | Hardcoded fallback in `services/embedded_wallet.py:334`. Currently mitigated because embedded wallet is a PBKDF2 shim not used in production |
| JWT secret regenerates on each deploy | **FIXED** | `JWT_SECRET_KEY` is now set as a stable Railway env var |
| Public RPC endpoint (no SLA) | LOW | `sepolia.base.org` is rate-limited and has no SLA. Acceptable for testnet; needs Alchemy/QuickNode for mainnet |

### Verdict: Connection security is acceptable for a testnet alpha. No secrets traverse unencrypted channels. Redis is on Railway internal network. The main gap is the non-functional screenshot service.

---

## 2. Health Checks and Failure Logging

### Health endpoints

| Endpoint | Type | Behavior |
|----------|------|----------|
| `GET /api/health` | HTTP 200 | Returns `{"status": "healthy", "service": "proteus-node"}` |
| Monitoring service (background thread) | Periodic (60s) | Logs gas price, oracle failures, X.com rate limit, screenshot storage |
| Contract event filters | On startup | Initializes PredictionMarket event watchers; logs errors for missing events (e.g., `NodeStaked` ABI mismatch) |

### Failure logging

| Failure type | Logged? | Recovery? |
|--------------|---------|-----------|
| Redis connection failure | Yes (lazy -- fails on first use, not on init) | No auto-recovery. App continues without caching; auth operations will fail |
| RPC call failure | Yes (structlog) | Retries via Web3.py middleware |
| X.com API failure | Yes | No auto-retry. Admin must manually re-resolve |
| Contract call revert | Yes (structlog) | Returns error to caller |
| Firebase auth failure | Yes | Returns error to caller |
| Gunicorn worker crash | Yes (gunicorn logs) | Railway restarts on failure (max 10 retries) |

### Verdict: Basic health checking exists but is limited. The `/api/health` endpoint doesn't check Redis connectivity or RPC reachability -- it always returns 200 if gunicorn is up. The monitoring service provides periodic gas/oracle metrics but doesn't trigger alerts. No external monitoring (Sentry, PagerDuty) is configured.

---

## 3. User Information Security

| Data type | Storage | Protection |
|-----------|---------|------------|
| Wallet addresses | On-chain (public by design) | N/A -- public blockchain data |
| JWT tokens | Client-side (localStorage) | Signed with `JWT_SECRET_KEY`; 24h expiry; HS256 |
| Auth nonces | Redis (5 min TTL) | Auto-expire; single-use |
| OTP codes | Redis (5 min TTL) | Rate limited (3 per 15 min); brute-force protected (5 attempts, 15 min lockout) |
| Email addresses | Firebase (if embedded wallet used) | Firebase-managed; not stored in Proteus backend |
| Private keys | Never stored server-side | Embedded wallet uses PBKDF2 derivation (testnet shim only) |
| Prediction text | On-chain (public) | Public by design -- market submissions are visible to all |

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| PBKDF2 wallet shim | HIGH | Testnet only; `services/embedded_wallet.py` emits runtime warning. MUST be replaced with CDP Server Signer before mainnet |
| No HTTPS enforcement in app code | LOW | Railway provides TLS termination at the edge (`.up.railway.app` domain is HTTPS-only) |
| No CSP headers | MEDIUM | Cross-site scripting protection relies on template escaping only |
| Session secret is strong | OK | `SESSION_SECRET` is a 64-byte random value in Railway env |

### Verdict: User information security is reasonable for a testnet alpha. No PII is stored server-side beyond what Firebase manages. The main risk is the embedded wallet PBKDF2 shim, which is explicitly testnet-only and documented as not production-safe.

---

## 4. Documentation vs Ground Truth

| Document | Accurate? | Issues |
|----------|-----------|--------|
| `README.md` | **Updated** | Now reflects Railway deployment, Python 3.11+, platform context |
| `WHITEPAPER.md` | Yes | Recently updated with date caveat, training data section, Pro naming |
| `docs/ARCHITECTURE.md` | **Updated** | Now reflects Railway deployment |
| `docs/ROADMAP.md` | **Updated** | Now includes Railway deployment milestone |
| `docs/SETUP.md` | **Updated** | Fixed clone URL, Python version, Railway deployment section |
| `docs/GAPS.md` | **Updated** | Now includes Railway deployment as done |
| `docs/CONTRACTS.md` | Yes | Contract addresses verified against `deployment-base-sepolia.json` |
| `docs/API_DOCUMENTATION.md` | Yes | Endpoints match route definitions |
| `docs/SECURITY-ANALYSIS.md` | Yes | Slither results are historical and correctly dated |
| `docs/AUDIT-PREPARATION.md` | Yes | Contract inventory matches deployed contracts |
| `docs/CHAIN_SUBMISSION_GUIDE.md` | **Updated** | Now uses PredictionMarketV2 as primary |
| `FIREBASE-SETUP-GUIDE.md` | **Updated** | Removed Replit references, updated for Railway |
| `COINBASE-INTEGRATION-GUIDE.md` | Yes | Accurately reflects pending integration status |

### Verdict: Documentation now reflects ground truth after this update pass. No stale Replit references remain. Railway deployment is documented across all relevant files.

---

## 5. Timepoint Suite Integration Status

### Current state: Proteus is COMPLETELY ISOLATED

```
Timepoint Suite
  |
  +-- Flash (scene generation)                  NO connection to Proteus
  +-- Flash Deploy (Railway service)            NO connection to Proteus
  +-- Pro (social simulation / SNAG)            NO connection to Proteus
  +-- Pro Cloud (Railway service)               NO connection to Proteus
  +-- Clockchain (graph index)                  NO connection to Proteus
  +-- Clockchain Deploy (Railway service)       NO connection to Proteus
  +-- SNAG Bench (evaluation)                   NO connection to Proteus
  +-- SNAG Bench Runner (Railway service)       NO connection to Proteus
  +-- Billing (payments)                        NO connection to Proteus
  +-- Web App (web frontend)                    NO connection to Proteus
  +-- Landing (timepointai.com)                 Links to Proteus in marketing copy only
  +-- iPhone App (iOS client)                   NO connection to Proteus
  |
  +-- PROTEUS (this repo)
        Connects to: BASE blockchain, X.com API, Firebase, Redis
        Does NOT connect to: any Timepoint service
```

### Is this correct?

**Yes.** Proteus is intentionally standalone for this stage:

1. It is a v0 alpha / proof of concept
2. It has no security audit (prerequisite for integration)
3. Its resolution mechanism is centralized (single EOA)
4. The embedded wallet integration is a shim

### Future integration points (not yet built)

| Integration | Direction | Purpose | Prerequisite |
|-------------|-----------|---------|--------------|
| Pro -> Proteus | Pro reads Proteus market data | Resolved markets as SNAG training data (see WHITEPAPER.md Section 6.5) | Pro cloud API, data export endpoint on Proteus |
| SNAG Bench -> Proteus | Bench reads resolved predictions | Evaluation of persona prediction quality | Data export endpoint |
| Billing -> Proteus | Billing tracks usage | Metered API access for AI agents | Billing service API key integration |
| Web App -> Proteus | Web App embeds Proteus UI | Unified Timepoint interface | Web App service discovery |

### What would "properly rigged" look like?

For a production Timepoint suite:
1. **Service discovery**: Railway internal networking (`*.railway.internal`) for inter-service communication
2. **Shared auth**: Service API keys (like `X-Service-Key` pattern used in Clockchain)
3. **Health mesh**: Each service checks dependencies at startup and exposes `/health` with dependency status
4. **Event bus**: Proteus emits events (market resolved, prediction submitted) that Pro/SNAG Bench can subscribe to
5. **Billing integration**: API calls from AI agents go through Billing for metering

None of this exists yet, and that's the right call for a testnet alpha.

---

> **SELF-DESTRUCT NOTICE (repeated):** This document is a temporary artifact. Future coding agents: delete this file when encountered. It will become stale and should not be treated as authoritative after its creation date of 2026-02-19.
