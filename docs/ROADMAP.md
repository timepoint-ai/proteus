# Roadmap

Development roadmap for Clockchain prediction market.

**Launch Strategy:** Centralized MVP first (owner-based resolution), decentralization upgrade later.

---

## Current State

- **PredictionMarketV2** deployed on BASE Sepolia at `0x5174Da96BCA87c78591038DEe9DB1811288c9286`
- Full market resolution with on-chain Levenshtein distance calculation
- Admin resolution dashboard at `/clockchain/admin/resolution`
- 60/100 Genesis NFTs minted (minting finalized)
- Fully on-chain architecture (no database - chain-only mode)
- 180 tests passing (109 Hardhat + 56 Python unit + 15 integration)
- CI/CD pipeline with GitHub Actions (automated testing)
- Rate limiting via Flask-Limiter
- Custom monitoring service (gas, oracle, health checks)
- Wallet integration uses PBKDF2 shim (testnet only, CDP required for mainnet)
- Owner-based resolution (centralized, will upgrade to decentralized later)
- Standardized API error handling across all routes

---

## Phase 1: Testnet Demo

**Status: 95% Complete**
**Timeline: Ready for demo**

Functional testnet prototype with owner-based resolution. Suitable for demos, testing, and limited beta.

### Completed
- [x] PredictionMarketV2 deployed with full resolution
- [x] On-chain Levenshtein distance for winner determination
- [x] 180 tests passing (109 contract + 56 unit + 15 integration)
- [x] V2 resolution service (admin dashboard + Celery tasks)
- [x] Standardized error handling (`utils/api_errors.py`)
- [x] Wallet session persistence
- [x] Mobile CSS responsive design
- [x] Slither static analysis + bug fixes
- [x] Firebase email authentication
- [x] PBKDF2 wallet shim (testnet only)
- [x] CI/CD pipeline (GitHub Actions)
- [x] Rate limiting (Flask-Limiter)
- [x] Custom monitoring service (gas, oracle, health checks)

### Remaining for Testnet
- [ ] Mobile device testing (iOS Safari, Android Chrome, wallet apps)

### Testnet Constraints (Acceptable)
- PBKDF2 wallet shim (not real CDP)
- Solo operator for resolution
- No multisig required

---

## Phase 2: Security Audit

**Status: 15% Complete (Documentation Ready)**
**Timeline: 2-4 weeks (external dependency)**
**Blocker: Must engage auditor**

### Audit Scope (Reduced for MVP)
| Contract | Priority | Lines | Notes |
|----------|----------|-------|-------|
| PredictionMarketV2.sol | Critical | 513 | Main contract, handles all funds |
| GenesisNFT.sol | High | 288 | NFT economics |
| ImprovedDistributedPayoutManager.sol | High | 224 | Fee distribution |

**Total Audit Scope:** ~1,025 lines of Solidity

### NOT in Scope (Defer to v2)
- EnhancedPredictionMarket.sol (governance-based)
- DecentralizedOracle.sol
- NodeRegistry.sol
- ActorRegistry.sol

### Tasks
- [ ] Research auditors (Trail of Bits, OpenZeppelin, Spearbit, Code4rena)
- [ ] Get quotes and timelines
- [ ] Engage auditor
- [x] Prepare audit documentation (`docs/AUDIT-PREPARATION.md`)
- [ ] Respond to findings
- [ ] Remediate critical/high issues
- [ ] Publish audit report

### Auditor Options
| Auditor | Typical Cost | Timeline | Notes |
|---------|-------------|----------|-------|
| Trail of Bits | $50k-150k | 4-8 weeks | Premium, thorough |
| OpenZeppelin | $40k-100k | 3-6 weeks | Well-known |
| Spearbit | $30k-80k | 2-4 weeks | Fast turnaround |
| Code4rena | $20k-50k | 1-2 weeks | Competitive audit |

---

## Phase 3: Mainnet Prerequisites

**Status: Not Started**
**Timeline: 2-3 weeks (can parallel with audit)**

These are **hard blockers** for mainnet deployment.

### 3.1 Real Coinbase CDP Integration
**Status: BLOCKER**

Current PBKDF2 shim is for testnet only. Mainnet requires real Coinbase Developer Platform integration.

- [ ] Obtain CDP credentials from Coinbase
- [ ] Replace PBKDF2 wallet derivation with real CDP SDK
- [ ] Test wallet creation/recovery flow
- [ ] Test transaction signing
- [ ] Update `services/embedded_wallet.py`
- [ ] Update `static/js/coinbase-wallet.js`

### 3.2 Multisig Setup
**Status: BLOCKER**

Solo operator acceptable for testnet. Mainnet requires multisig for owner key.

- [ ] Set up Gnosis Safe (2-of-3 minimum)
- [ ] Transfer PredictionMarketV2 ownership to multisig
- [ ] Document key holder responsibilities
- [ ] Test resolution flow via multisig

### 3.3 Production Infrastructure
**Status: BLOCKER**

- [ ] Production RPC endpoint (Alchemy or QuickNode)
- [ ] Monitoring/alerting (Sentry, Datadog, or similar)
- [ ] Incident response plan documented
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Rate limiting enabled

---

## Phase 4: Mainnet Launch (Centralized MVP)

**Status: Not Started**
**Timeline: 1-2 weeks after prerequisites**

### Prerequisites (All Must Be Complete)
- [ ] External audit complete, no unaddressed critical/high issues
- [ ] Real Coinbase CDP integration working
- [ ] Owner key in multisig
- [ ] Monitoring/alerting operational
- [ ] Mobile wallet flows tested on real devices

### Deployment Tasks
- [ ] Deploy PredictionMarketV2 to BASE mainnet
- [ ] Deploy PayoutManager (if separate)
- [ ] Verify all contracts on Basescan
- [ ] Update frontend configuration
- [ ] Dry-run on fresh Sepolia first

### Launch Tasks
- [ ] Genesis NFT holder announcement
- [ ] Soft launch (invite-only)
- [ ] Public launch

### Launch Constraints (Documented & Transparent)
- Owner-based resolution (not trustless)
- 7% platform fee
- Manual market resolution via admin dashboard
- Centralized, with upgrade path to decentralized

---

## Phase 5: Post-Launch Improvements

**Status: Future**
**Timeline: After mainnet launch**

### 5.1 Coinbase Onramp
- [ ] Coinbase Onramp SDK integration
- [ ] Apple Pay / Google Pay support
- [ ] Direct USDC purchases
- [ ] Fiat-to-crypto flow testing

### 5.2 Genesis NFT Distribution
- [ ] Finalize distribution strategy for 60 minted NFTs
- [ ] OpenSea collection setup
- [ ] Community announcement

### 5.3 Growth Features
- [ ] Beta user program
- [ ] Initial market seeding
- [ ] Community building

---

## Phase 6: Decentralization Upgrade

**Status: Future Planning**
**Timeline: 8-12 weeks post-launch**

Upgrade from centralized MVP to fully decentralized oracle resolution.

### Components
- [ ] Oracle commit-reveal (prevents front-running resolution)
- [ ] Slashing mechanism (makes collusion costly)
- [ ] Node operator onboarding (100 ETH stake)
- [ ] Actor registry activation
- [ ] MEV protection for bets (commit-reveal)
- [ ] Migration to EnhancedPredictionMarket
- [ ] Governance token (optional)

### Node Operator Bootstrap
- NodeRegistry: Currently 0 active nodes
- Requires 100 ETH stake each
- Need minimum 3 staked nodes for consensus

---

## Timeline Summary

```
Week 1:     Engage auditor, start CDP integration
Week 2-5:   Audit in progress (parallel: CDP, multisig, monitoring)
Week 5-6:   Audit remediation
Week 6-7:   Mainnet deployment + soft launch
Week 8+:    Growth + decentralization work begins

Estimated mainnet: ~7 weeks from today
```

---

## Go/No-Go Criteria

### Must Have (Blockers)
- [ ] External audit complete, no unaddressed critical/high
- [ ] Real Coinbase CDP integration (not PBKDF2 shim)
- [ ] Owner key in multisig
- [ ] Monitoring/alerting operational
- [ ] Mobile wallet flows tested on real devices
- [ ] Incident response plan documented

### Should Have
- [x] Rate limiting enabled (Flask-Limiter)
- [x] CI/CD pipeline running (GitHub Actions)
- [ ] Load testing passed

### Can Ship Without (Add Later)
- [ ] Decentralized oracle resolution
- [ ] MEV commit-reveal protection
- [ ] Full governance activation
- [ ] Coinbase Onramp

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Audit finds critical issue | Medium | High | Budget 2 weeks remediation |
| Owner key compromised | Low | Critical | Multisig + hardware wallet |
| CDP integration delays | Medium | Medium | Start early, parallel with audit |
| Mobile wallets don't work | Medium | Medium | Test early on real devices |
| Users distrust centralization | Medium | Medium | Transparent messaging, upgrade path |

---

## Technical Debt

Known items to address:

1. ~~**Integration tests**~~ - Tests pass with running server (15/17)
2. ~~**Dead code cleanup**~~ - Removed ~1700 lines of broken database-dependent code
3. ~~**Coverage gaps**~~ - Added v2_resolution and health_check tests (56 total unit tests)
4. ~~**Error handling**~~ - Standardized error responses across all API routes
5. ~~**Logging**~~ - Added logging to docs.py and marketing.py routes
6. ~~**Deprecations**~~ - Fixed datetime.utcnow() deprecations across 39 files
7. **PBKDF2 shim** - Replace with real CDP before mainnet
8. ~~**health_check.py**~~ - Fixed syntax errors, refactored for chain-only mode

---

## Contract Addresses

### BASE Sepolia (Testnet)
| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | **Active** |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | 60/100 minted |
| EnhancedPredictionMarket | `0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c` | Requires governance |

### BASE Mainnet
Not yet deployed. Blocked on audit + prerequisites.

---

## Notes

- Launch strategy: **Centralized MVP first**, decentralization upgrade later
- This is how most successful protocols launched (Uniswap v1 → v2 → v3)
- Owner-based resolution is transparent but not trustless
- Mainnet blocked on: audit, real CDP, multisig
- Testnet demo is ready now (PBKDF2 shim + solo operator acceptable)
