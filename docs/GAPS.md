# Gap Analysis

Last updated: December 3, 2024

A prioritized list of gaps between current state and production-ready launch.

> **Major Update:** PredictionMarketV2 deployed with full resolution mechanism, fixing the critical gap where V1 had no way to determine winners.

> **Launch Strategy:** Centralized MVP first (owner-based resolution), decentralization upgrade later. See [ROADMAP.md](ROADMAP.md) for timeline.

---

## Mainnet Blockers (Must Complete Before Mainnet)

These are **hard blockers** for mainnet. Testnet demo can proceed without them.

### M1. Real Coinbase CDP Integration
**Priority: P0 (MAINNET BLOCKER)**
**Effort: 2-3 weeks**
**Status: NOT STARTED**

Current wallet uses PBKDF2 shim for deterministic wallet derivation. This is acceptable for testnet but **NOT for mainnet**.

**Current state (Testnet OK):**
- PBKDF2-based wallet derivation from email
- Works for demo/testing purposes
- No real Coinbase SDK integration

**Required for Mainnet:**
- [ ] Obtain CDP credentials from Coinbase Developer Platform
- [ ] Replace PBKDF2 derivation with real CDP SDK
- [ ] Implement proper wallet creation via CDP
- [ ] Test wallet recovery flow
- [ ] Update `services/embedded_wallet.py`
- [ ] Update `static/js/coinbase-wallet.js`

**Risk if skipped:** Security vulnerability, users could lose funds, not production-ready.

---

### M2. Multisig for Owner Key
**Priority: P0 (MAINNET BLOCKER)**
**Effort: 1-2 days**
**Status: NOT STARTED**

Solo operator acceptable for testnet. Mainnet requires multisig for contract owner key.

**Current state (Testnet OK):**
- Single owner key controls PredictionMarketV2
- Owner can resolve markets, withdraw fees
- Acceptable for demo/testing

**Required for Mainnet:**
- [ ] Set up Gnosis Safe (2-of-3 minimum)
- [ ] Transfer PredictionMarketV2 ownership to multisig
- [ ] Document key holder responsibilities
- [ ] Test resolution flow via multisig
- [ ] Secure hardware wallets for signers

**Risk if skipped:** Single point of failure, owner key compromise = total fund loss.

---

### M3. External Security Audit
**Priority: P0 (MAINNET BLOCKER)**
**Effort: 2-4 weeks (external dependency)**
**Status: NOT STARTED (need to engage auditor)**

No external security audit has been performed. Slither analysis complete but not sufficient for mainnet.

**Current state:**
- Slither static analysis complete (277 findings triaged)
- 1 real bug found and fixed (AdvancedMarkets locked-ether)
- 180 tests passing
- **No external auditor engaged**

**Audit Scope (MVP):**
| Contract | Priority |
|----------|----------|
| PredictionMarketV2.sol | Critical |
| GenesisNFT.sol | High |
| ImprovedDistributedPayoutManager.sol | High |

**Required:**
- [ ] Research and contact auditors
- [ ] Get quotes and timelines
- [ ] Engage auditor
- [ ] Remediate critical/high findings
- [ ] Publish audit report

**Auditor Options:**
| Auditor | Cost Range | Timeline |
|---------|------------|----------|
| Trail of Bits | $50k-150k | 4-8 weeks |
| OpenZeppelin | $40k-100k | 3-6 weeks |
| Spearbit | $30k-80k | 2-4 weeks |
| Code4rena | $20k-50k | 1-2 weeks |

**Risk if skipped:** Contract exploits, fund loss, reputation damage, legal liability.

---

## Critical (Blockers for Launch)

### 1. Governance Bootstrap
**Priority: P2 (Downgraded - V2 doesn't require governance)**
**Effort: Architecture decision required**
**Status: DEFERRED**

EnhancedPredictionMarket cannot create markets without governance setup.

**Resolution:** PredictionMarketV2 deployed without governance requirements. V2 uses owner-based resolution instead of decentralized oracle consensus.

**Current state:**
- NodeRegistry: 0 active nodes
- ActorRegistry: 0 active actors
- **PredictionMarketV2 deployed and functional without governance**

**V2 Solution:**
- `0x5174Da96BCA87c78591038DEe9DB1811288c9286` - Full market lifecycle without governance
- Owner-based resolution with on-chain Levenshtein distance
- Suitable for testnet and initial production

**Future consideration:** Governance may be added for decentralized resolution in future versions.

---

### 2. UI/Contract Integration
**Priority: P0**
**Effort: 2-3 days**
**Status: COMPLETE (Upgraded to V2)**

Frontend/backend connected to PredictionMarketV2 with full resolution capability.

**Completed:**
- [x] Document the issue in GAPS.md
- [x] Create `deployment-base-sepolia.json` with all contracts
- [x] Update `services/blockchain_base.py` for V2 contract
- [x] Update `routes/clockchain.py` to use PredictionMarketV2
- [x] Update `static/js/market-blockchain.js` addresses and ABIs
- [x] Update `static/js/betting-contract.js` and `market-create.js`
- [x] Test full user flow (15 integration tests passing)
- [x] **V2 Resolution service** (`services/v2_resolution.py`)
- [x] **Admin resolution dashboard** (`/clockchain/admin/resolution`)
- [x] **Celery auto-resolution tasks** (`resolve_v2_pending_markets`)

**Contracts in use:**
- **PredictionMarketV2 (recommended)**: `0x5174Da96BCA87c78591038DEe9DB1811288c9286`
- PredictionMarket V1 (deprecated): `0x667121e8f22570F2c521454D93D6A87e44488d93`

---

### 3. Security Audit
**Priority: P0 (MAINNET BLOCKER)**
**Effort: External dependency (2-4 weeks)**
**Status: Static Analysis Complete, External Audit NOT STARTED**

Slither static analysis complete. External audit required for mainnet.

**Current state:**
- Contracts deployed on BASE Sepolia
- 109 contract tests passing (including 57 V2 tests)
- Slither static analysis complete (see docs/SECURITY-ANALYSIS.md)
- Triage complete - 1 real bug found and fixed
- **No external auditor engaged yet**

**Slither Results:**
- High: 5 (all false positives or by-design)
- Medium: 38 (1 real bug found and fixed)
- Low: 40
- **Real bug:** AdvancedMarkets.sol locks ETH with no withdrawal - **FIXED**

**Triage Summary:**
| Contract | Issue | Status |
|----------|-------|--------|
| AdvancedMarkets | locked-ether | **FIXED** - Added resolution/claim/withdraw |
| TestMarketWithPayouts | locked-ether | False positive |
| BuilderRewardPool | divide-before-multiply | Fix recommended |
| BittensorRewardPool | divide-before-multiply | Acceptable |
| PredictionMarketV2 | None | Safe for use |

**Required:**
- [x] Run Slither static analysis
- [x] Triage and categorize findings
- [x] Fix AdvancedMarkets locked-ether bug
- [ ] Research and contact auditors (Trail of Bits, OpenZeppelin, Spearbit, Code4rena)
- [ ] Get quotes and timelines
- [ ] Engage external auditor
- [ ] Remediate all critical/high findings
- [ ] Publish audit report

**Risk if skipped:** Contract exploits, fund loss, reputation damage, legal liability

> **Note:** See M3 in Mainnet Blockers section above for auditor options and cost estimates.

---

### 4. Wallet Session Persistence
**Priority: P0**
**Effort: 2-3 days**
**Status: COMPLETE**

Users lose wallet connection on page refresh.

**Implementation:**
- [x] Store wallet state in localStorage (address, chainId, walletType, expiry)
- [x] Implement auto-reconnect on page load via `restoreSession()`
- [x] Handle wallet disconnect events with proper cleanup
- [x] Clear session on explicit logout

**Files modified:**
- `static/js/wallet.js` - Main session persistence implementation
- `static/js/coinbase-wallet.js` - Integration with session system

---

### 5. Mobile Responsiveness
**Priority: P0**
**Effort: 3-5 days**
**Status: CSS COMPLETE (Testing Required)**

Mobile wallet experience not tested or optimized.

**Current state:**
- CSS responsive breakpoints added
- Touch-friendly button sizes implemented (min 44px)
- Wallet modals optimized for mobile screens
- Manual device testing still required

**Implemented:**
- [x] Add mobile CSS breakpoints (768px, 480px)
- [x] Touch-friendly button sizes (min 44px targets)
- [x] Responsive wallet modals (full-width on mobile)
- [x] Font size 16px for inputs (prevents iOS zoom)
- [x] Wallet address truncation on small screens

**Still Required (Manual Testing):**
- [ ] Test Coinbase Wallet on iOS/Android
- [ ] Test MetaMask mobile browser
- [ ] Verify touch interactions work correctly
- [ ] Test deep linking for mobile wallets

**Files modified:**
- `static/css/wallet.css` - Added mobile breakpoints and touch targets
- `static/css/coinbase-wallet.css` - Added responsive modal styles

---

## High Priority (Required for Launch)

### 6. Integration Test Coverage
**Priority: P1**
**Effort: 2-3 days**
**Status: Tests Passing**

Integration tests verified and passing.

**Current state:**
- 17 integration tests defined
- 15 passing, 2 skipped (expected - Genesis endpoint and Firebase not configured)
- Requires running Flask server

**Completed:**
- [x] Fixed test assertions to handle API response variations
- [x] Verified all API chain endpoints work
- [x] Verified wallet auth endpoints work

**Remaining:**
- [ ] Set up CI/CD pipeline for integration tests
- [ ] Document manual test procedure

**Files:**
- `tests/integration/test_api_chain.py`
- `tests/integration/test_wallet_auth.py`

---

### 7. Error Handling Standardization
**Priority: P1**
**Effort: 2 days**
**Status: COMPLETE**

Standardized error responses across API endpoints.

**Completed:**
- [x] Created `utils/api_errors.py` with standard error utilities
- [x] Created `routes/error_handlers.py` for Flask error handling
- [x] Updated `routes/clockchain.py` with standard errors
- [x] Updated `routes/api_chain.py` with standard errors
- [x] Updated `routes/embedded_auth.py` with standard errors
- [x] Updated `routes/auth.py` with standard errors
- [x] Documented error codes in API docs

**Standard Format:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

**Error Codes:** `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `BLOCKCHAIN_ERROR`, `CONTRACT_ERROR`, `INTERNAL_ERROR`, etc.

---

### 8. Coinbase SDK Finalization
**Priority: P0 (MAINNET BLOCKER) / P1 for testnet**
**Effort: 2-3 weeks**
**Status: PBKDF2 Shim (Testnet Only)**

Current implementation uses PBKDF2 shim, not real Coinbase CDP SDK.

**Current state (Testnet OK):**
- PBKDF2-based wallet derivation from email
- Works for demo/testing
- Transaction signing implemented

**Required for Mainnet:**
- [ ] Obtain CDP credentials from Coinbase
- [ ] Replace PBKDF2 with real CDP SDK
- [ ] Implement proper wallet creation
- [ ] Add wallet recovery flow
- [ ] Test gasless transactions (if available)
- [ ] Handle network switching

**Files:**
- `static/js/coinbase-wallet.js`
- `services/embedded_wallet.py`

> **Note:** See M1 in Mainnet Blockers section above for full details.

---

## Medium Priority (Nice to Have for Launch)

### 9. Structured Logging
**Priority: P2**
**Effort: 1-2 days**

Logging is inconsistent and hard to debug.

**Current state:**
- Basic `print()` statements in some places
- `logging` module used inconsistently
- No structured format for log aggregation

**Required:**
- [ ] Implement structured logging (JSON format)
- [ ] Add request ID tracking
- [ ] Configure log levels per environment
- [ ] Add performance timing logs

---

### 10. Rate Limiting
**Priority: P2**
**Effort: 1 day**

No rate limiting on API endpoints.

**Current state:**
- Endpoints open to unlimited requests
- Vulnerable to DDoS/abuse

**Required:**
- [ ] Add Flask-Limiter or similar
- [ ] Configure per-endpoint limits
- [ ] Add rate limit headers to responses
- [ ] Document limits in API docs

---

### 11. Monitoring & Alerting
**Priority: P2**
**Effort: 2-3 days**

No production monitoring in place.

**Current state:**
- No metrics collection
- No alerting on errors
- No uptime monitoring

**Required:**
- [ ] Set up error tracking (Sentry)
- [ ] Add metrics (Prometheus/DataDog)
- [ ] Configure alerts for critical errors
- [ ] Uptime monitoring (Better Uptime, etc.)

---

### 12. Test Coverage Gaps
**Priority: P2**
**Effort: 3-5 days**

Some services lack unit test coverage.

**Current state:**
- 56 Python unit tests
- Some services not tested:
  - `services/celery_tasks.py`
  - `services/redis_cache.py`
  - Route handlers

**Required:**
- [ ] Add tests for Celery tasks
- [ ] Add tests for Redis caching
- [ ] Add route handler tests
- [ ] Achieve 80% coverage target

---

## Low Priority (Post-Launch)

### 13. Documentation Gaps
**Priority: P3**
**Effort: 1-2 days**

Some documentation areas thin.

**Items:**
- [ ] API authentication examples
- [ ] Webhook documentation (if applicable)
- [ ] Troubleshooting guide expansion
- [ ] Architecture diagrams (visual)

---

### 14. Performance Optimization
**Priority: P3**
**Effort: Ongoing**

No performance testing or optimization done.

**Items:**
- [ ] Load testing with realistic traffic
- [ ] Database query optimization (if any)
- [ ] Frontend bundle size optimization
- [ ] CDN for static assets

---

### 15. Accessibility
**Priority: P3**
**Effort: 2-3 days**

No accessibility audit performed.

**Items:**
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation
- [ ] Screen reader testing
- [ ] Color contrast compliance

---

## Summary Table

### Mainnet Blockers
| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| **Real Coinbase CDP** | P0 | 2-3 weeks | **NOT STARTED** (PBKDF2 shim = testnet only) |
| **Multisig Setup** | P0 | 1-2 days | **NOT STARTED** (solo operator = testnet only) |
| **External Audit** | P0 | 2-4 weeks | **NOT STARTED** (need to engage auditor) |

### Testnet Complete
| Gap | Priority | Effort | Status |
|-----|----------|--------|--------|
| UI/Contract Integration | P0 | 2-3 days | **COMPLETE** (V2 deployed) |
| V2 Resolution Integration | P0 | 3-4 days | **COMPLETE** |
| Wallet Session Persistence | P0 | 2-3 days | **COMPLETE** |
| Error Handling | P1 | 2 days | **COMPLETE** |
| Governance Bootstrap | P2 | Architecture | **DEFERRED** (V2 doesn't require) |

### Remaining Work
| Gap | Priority | Effort | Blocker? | Status |
|-----|----------|--------|----------|--------|
| Mobile Testing | P0 | 2-3 days | Mainnet | CSS done, device testing needed |
| Integration Tests | P1 | 2-3 days | No | Tests Passing, **CI/CD COMPLETE** |
| Structured Logging | P2 | 1-2 days | No | Not started |
| Rate Limiting | P2 | 1 day | No | **COMPLETE** (Flask-Limiter) |
| Monitoring | P2 | 2-3 days | Mainnet | Partial |
| Test Coverage | P2 | 3-5 days | No | 180 tests passing |
| Documentation | P3 | 1-2 days | No | **COMPLETE** |
| Performance | P3 | Ongoing | No | Not started |
| Accessibility | P3 | 2-3 days | No | Not started |

---

## Recommended Order of Work

### Testnet Demo (Now)
1. ~~**UI/Contract Integration**~~ - **COMPLETE** - Frontend connected to PredictionMarketV2
2. ~~**Wallet Session Persistence**~~ - **COMPLETE** - Sessions persist across reloads
3. ~~**V2 Resolution Integration**~~ - **COMPLETE** - Admin dashboard + Celery tasks
4. ~~**Error Handling**~~ - **COMPLETE** - Standardized error responses across all routes
5. **Mobile Testing** - Verify wallet works on mobile devices (CSS done)

### Mainnet Preparation (Parallel with Audit)
6. **Engage Auditor** - Research, get quotes, engage (longest lead time)
7. **Real Coinbase CDP** - Replace PBKDF2 shim with real CDP SDK
8. **Multisig Setup** - Gnosis Safe for owner key
9. **Monitoring Setup** - Sentry, alerting for production

### Mainnet Launch
10. **Audit Remediation** - Fix any critical/high findings
11. **Deploy to Mainnet** - After all blockers resolved

---

## Timeline Estimate

```
Week 1:     Engage auditor, start CDP integration
Week 2-5:   Audit in progress (parallel: CDP, multisig, monitoring)
Week 5-6:   Audit remediation
Week 6-7:   Mainnet deployment + soft launch

Estimated mainnet: ~7 weeks from today
```

---

## Notes

**Testnet Status:**
- **PredictionMarketV2 deployed** at `0x5174Da96BCA87c78591038DEe9DB1811288c9286` with full resolution
- V2 Resolution service complete with admin dashboard and Celery auto-resolution
- 180 tests passing (109 Hardhat + 56 Python unit + 15 integration)
- Standardized API error handling complete (`utils/api_errors.py`)
- Wallet session persistence complete
- PBKDF2 wallet shim works for testnet (not mainnet)
- Solo operator resolution acceptable for testnet

**Mainnet Blockers:**
- Real Coinbase CDP integration required (PBKDF2 shim not acceptable)
- Multisig required for owner key (solo operator not acceptable)
- External security audit required (Slither not sufficient)

**Other Notes:**
- Governance bootstrap deferred - V2 uses owner-based resolution (centralized MVP)
- Security audit is the longest lead-time item (~2-4 weeks)
- Mobile CSS complete - manual device testing required
- Genesis NFT minting is finalized (60/100 minted)
- PredictionMarket V1 deprecated (no resolution mechanism)
- Launch strategy: Centralized MVP first, decentralization upgrade later
