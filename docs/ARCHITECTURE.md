# Architecture

Technical architecture of the Clockchain prediction market platform.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  (Web3.js, Coinbase Wallet SDK, Firebase Auth)              │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                     Flask Backend                            │
│  (API Routes, Wallet Auth, Redis Cache)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   BASE Blockchain                            │
│  (Smart Contracts, All Data Storage)                        │
└─────────────────────────────────────────────────────────────┘
```

## Smart Contract Stack

| Contract | Purpose | Status |
|----------|---------|--------|
| **PredictionMarketV2** | Full market lifecycle with Levenshtein resolution | **Active - Recommended** |
| PredictionMarket (V1) | Simple market (no resolution mechanism) | Deprecated |
| GenesisNFT | 100 founder NFTs with on-chain SVG art | 60 minted, finalized |
| PayoutManager | Fee distribution to all stakeholders | Deployed |
| EnhancedPredictionMarket | Full governance market logic | Requires active actors |
| DecentralizedOracle | Text validation and Levenshtein calculation | Deployed |
| ActorRegistry | X.com actor registration (3 approvals needed) | 0 active actors |
| NodeRegistry | Node operator staking (100 ETH required) | 0 active nodes |

> **Note:** **PredictionMarketV2** is the recommended contract with complete market lifecycle: create -> submit -> resolve -> claim. V1 is deprecated (lacks resolution).

## Governance Model

EnhancedPredictionMarket implements decentralized governance:

```
┌─────────────────────────────────────────────────────────────┐
│                     NodeRegistry                             │
│  - 100 ETH stake required to register                        │
│  - 24-hour voting period for activation                      │
│  - 51% quorum from existing nodes                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ (active nodes can propose actors)
┌─────────────────────▼───────────────────────────────────────┐
│                    ActorRegistry                             │
│  - Propose X.com usernames                                   │
│  - 3 active node approvals required                          │
│  - 24-hour voting period                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ (active actors enable market creation)
┌─────────────────────▼───────────────────────────────────────┐
│               EnhancedPredictionMarket                       │
│  - Create markets for active actors only                     │
│  - Full on-chain submission/bet tracking                     │
│  - Oracle-based resolution                                   │
└─────────────────────────────────────────────────────────────┘
```

**Current Testnet State:**
- No active nodes (100 ETH stake prohibitive for testnet)
- No active actors (requires node approvals)
- Use `PredictionMarketV2` for all new development

## Data Flow

```
Market Creation
    │
    ▼
User Submissions (predicted text + stake)
    │
    ▼
Secondary Bets (bet on existing submissions)
    │
    ▼
Oracle Resolution (fetch actual text from X.com)
    │
    ▼
Levenshtein Distance Calculation
    │
    ▼
Winner Determination (closest match wins)
    │
    ▼
Payout Distribution (automatic, on-chain)
```

## Backend Services

```
services/
├── blockchain_base.py      # Web3 contract interactions
├── v2_resolution.py        # PredictionMarketV2 resolution service
├── oracle.py               # X.com API + Playwright screenshots
├── consensus.py            # Node voting (66% threshold)
├── text_analysis.py        # Levenshtein distance
├── cache_manager.py        # Redis caching
├── rpc_retry.py            # RPC failover logic
├── firebase_auth.py        # Email OTP authentication
├── embedded_wallet.py      # Coinbase wallet service
├── celery_tasks.py         # Background task processing
└── monitoring.py           # Health checks and alerts

utils/
├── api_errors.py           # Standardized error responses
└── decorators.py           # Route decorators
```

## API Routes

All data is fetched from blockchain. No database.

```
routes/
├── api_chain.py            # /api/chain/* - blockchain queries
├── clockchain.py           # /clockchain/* - market operations + admin resolution
├── embedded_auth.py        # /api/embedded/* - wallet auth
├── auth.py                 # /auth/* - JWT wallet authentication
├── error_handlers.py       # Standardized error handling (400, 401, 403, 404, 500)
└── oracles.py              # Oracle submission endpoints
```

## Performance Optimizations

### Gas Optimization
- Fixed gas price: 1 gwei on BASE
- Gas limits: 500k (markets), 300k (submissions), 200k (bets)
- 20% safety buffer on all transactions

### Caching (Redis)
| Data | TTL |
|------|-----|
| Actors | 5 min |
| Markets | 30 sec |
| Stats | 10 sec |
| Genesis data | 1 min |
| Gas price | 5 sec |

### RPC Resilience
- Exponential backoff with jitter
- Multiple endpoint failover (Alchemy, QuickNode, public)
- Max 3 retry attempts

## Security

### Smart Contracts
- Reentrancy guards on all payment functions
- No upgradeable proxies (immutable)
- No admin functions post-deployment
- Time-locked minting (24-hour window)

### Backend
- JWT-based wallet authentication
- Rate limiting (100 req/min default)
- CORS restricted to approved domains

### Oracle
- 3 oracle minimum for consensus
- Screenshot proof required
- Slashing for false submissions

## Testing Infrastructure

| Suite | Tests | Status |
|-------|-------|--------|
| Python Unit | 26 | Passing |
| Smart Contracts | 109 | Passing |
| Integration | 15 | Passing (2 expected skips) |
| **Total** | **150** | **All passing** |

Integration tests cover:
- Chain API endpoints (actors, markets, stats)
- Wallet authentication flow (nonce, verify, refresh, logout)
- Embedded wallet OTP flow

## Network Configuration

### BASE Sepolia (Testnet)
- Chain ID: 84532
- RPC: https://sepolia.base.org
- Explorer: https://sepolia.basescan.org

### BASE Mainnet (Future)
- Chain ID: 8453
- RPC: https://mainnet.base.org
- Explorer: https://basescan.org
