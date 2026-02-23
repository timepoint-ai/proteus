# Architecture

**v0 Alpha** -- This documents the prototype architecture. Everything below the smart contract layer is scaffolding.

## Core Primitive

The novel piece is on-chain Levenshtein distance as a scoring function for prediction markets. Everything else (Flask backend, wallet auth, admin dashboard) exists to make that primitive testable on BASE Sepolia.

```
                    The thing that matters
                    ──────────────────────
                    PredictionMarketV2.sol
                    - createSubmission(marketId, predictedText) payable
                    - resolveMarket(marketId, actualText) onlyOwner
                    - levenshteinDistance(a, b) pure → uint256
                    - claimPayout(submissionId)

                    Prototype scaffolding
                    ─────────────────────
                    Flask + Web3.py backend
                    Vanilla JS frontend
                    Firebase email OTP
                    Redis caching
                    Celery workers
```

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                            │
│  (Web3.js, Coinbase Wallet SDK, Firebase Auth)           │
│  Status: Functional prototype, not production-ready      │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│              Flask Backend (Railway)                      │
│  (gunicorn, API Routes, Wallet Auth, Redis Cache)        │
│  proteus-production-6213.up.railway.app                  │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 BASE Blockchain                           │
│  (Smart Contracts, All Data Storage)                     │
│  Status: Deployed on Sepolia, contracts work             │
└─────────────────────────────────────────────────────────┘
```

## Smart Contract Stack

| Contract | Purpose | Status |
|----------|---------|--------|
| **PredictionMarketV2** | Full market lifecycle with Levenshtein resolution | **Active** |
| GenesisNFT | 100 founder NFTs with on-chain SVG art | 60 minted, finalized |
| PayoutManager | Fee distribution to stakeholders | Deployed |
| DecentralizedOracle | Text validation and Levenshtein calculation | Deployed (future use) |
| ActorRegistry | X.com actor registration (governance) | Deployed (future use) |
| NodeRegistry | Node operator staking | Deployed (future use) |
| PredictionMarket (V1) | Simple market, no resolution | **Deprecated** |
| EnhancedPredictionMarket | Full governance market logic | Future (requires active nodes) |

**PredictionMarketV2** is the only contract that matters right now. Everything else is either supporting infrastructure or planned for a future decentralization upgrade.

## Data Flow

```
Market Creation (actor handle, description, end time)
    │
    ▼
User Submissions (predicted text + ETH stake)
    │
    ▼
Market Ends (time-based)
    │
    ▼
Oracle Resolution (fetch actual text from X.com)
    │
    ▼
On-chain Levenshtein Distance (O(m*n) string comparison)
    │
    ▼
Winner = lowest edit distance (first submitter wins ties)
    │
    ▼
Payout: winner gets 93% of pool, 7% platform fee
```

## Resolution Model (Centralized MVP)

Currently: single EOA calls `resolveMarket(marketId, actualText)`. This is the biggest centralization risk and the most important thing to fix before any real deployment.

**Planned upgrade path:**
1. Commit-reveal oracle consensus (multiple oracles submit, majority wins)
2. Slashing for dishonest oracles
3. Screenshot proof required (IPFS-pinned)

## Backend Services (Prototype)

```
services/
├── blockchain_base.py      # Web3 contract interactions
├── v2_resolution.py        # Market resolution service (owner-based)
├── auth_store.py           # Redis-backed nonce/OTP storage
├── oracle.py               # X.com API + Playwright screenshots
├── text_analysis.py        # Levenshtein distance (Python side)
├── cache_manager.py        # Redis caching for RPC responses
├── firebase_auth.py        # Email OTP authentication
├── embedded_wallet.py      # Coinbase wallet shim (PBKDF2, NOT production-safe)
└── monitoring.py           # Health checks

utils/
├── api_errors.py           # Standardized error responses
├── logging_config.py       # Structured logging (structlog)
└── request_context.py      # Request ID middleware
```

## API Routes

All data is fetched from blockchain. Zero database.

```
routes/
├── api_chain.py            # /api/chain/* - blockchain queries
├── auth.py                 # /auth/* - JWT wallet auth + OTP (Redis-backed)
├── proteus.py              # /proteus/* - market operations + admin resolution
├── embedded_auth.py        # /api/embedded/* - Coinbase wallet auth
├── admin.py                # /admin/* - resolution dashboard
├── error_handlers.py       # Standardized error handling
└── ...                     # Other route modules (marketing, docs, oracles, etc.)
```

## Gas Considerations

Levenshtein distance is the expensive operation:

| String Length | Approximate Gas |
|---------------|-----------------|
| 50 chars each | ~400,000 |
| 100 chars each | ~1,500,000 |
| 280 chars each | ~9,000,000 |

Capped at 280 characters (tweet length) to prevent block gas limit DoS.

## Caching (Redis)

| Data | TTL |
|------|-----|
| Actors | 5 min |
| Markets | 30 sec |
| Stats | 10 sec |
| Auth nonces | 5 min |
| OTP codes | 5 min |
| Gas price | 5 sec |

## Security Posture (Honest Assessment)

### Smart Contracts
- Reentrancy guards on all payment functions (OpenZeppelin)
- No upgradeable proxies (immutable deployments)
- Slither static analysis complete (1 real bug found and fixed)
- **No external audit** -- this is the biggest gap

### Backend
- JWT wallet authentication
- Redis-backed nonce/OTP storage with TTL expiry
- OTP rate limiting (3 per 15 min) and brute-force protection (5 attempts)
- Rate limiting (Flask-Limiter)
- **Embedded wallet uses PBKDF2 shim** -- testnet only, not production-safe

### Known Centralization Risks
- Single EOA resolves markets (owner-based resolution)
- No multisig on contract owner key
- Backend is a single Flask instance

## Network Configuration

### BASE Sepolia (Testnet) -- Current
- Chain ID: 84532
- RPC: https://sepolia.base.org
- Explorer: https://sepolia.basescan.org

### BASE Mainnet -- Not deployed, blocked on audit + prerequisites
- Chain ID: 8453
- RPC: Requires Alchemy/QuickNode (config supports both)
- Explorer: https://basescan.org
