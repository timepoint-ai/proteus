# Gap Analysis

**v0 Alpha** -- Updated February 2026

Honest accounting of what's done, what's not, and what matters.

---

## What's Done

The core primitive works:

- [x] On-chain Levenshtein distance scoring (PredictionMarketV2)
- [x] Full market lifecycle on BASE Sepolia
- [x] 250+ passing tests
- [x] Slither static analysis (1 real bug found and fixed)
- [x] Flask backend with JWT auth and Redis-backed OTP
- [x] CI/CD pipeline
- [x] Genesis NFT with on-chain SVG art

---

## What's Not Done (and Why)

### Must-have before mainnet

| Gap | Why it matters | Status |
|-----|---------------|--------|
| External security audit | Smart contracts hold real ETH | NOT STARTED |
| Multisig for owner key | Single EOA = single point of failure | NOT STARTED |
| Real CDP wallet integration | PBKDF2 shim is not production-safe | BLOCKED (no credentials) |
| Decentralized resolution | Owner-based resolution is centralized | DESIGNED, not built. X API pay-per-use access now available ([developer.x.com](https://developer.x.com/)) -- unblocks multi-oracle verification |
| Production RPC | Public RPCs have rate limits and no SLA | NOT CONFIGURED |

### Should-have for credibility

| Gap | Why it matters | Status |
|-----|---------------|--------|
| Production monitoring (Sentry) | Need to know when things break | NOT STARTED |
| Mobile device testing | Wallet UX varies wildly across devices | NOT STARTED |
| Incident response plan | What happens when something goes wrong | NOT WRITTEN |
| Load testing in production-like env | Redis caching untested under real load | SCRIPTS WRITTEN, not validated |

### Nice-to-have

| Gap | Status |
|-----|--------|
| Coinbase Onramp SDK (fiat purchases) | Future |
| OpenSea listing for Genesis NFTs | Future |
| Governance token | Future, maybe never |

---

## Known Technical Debt

### Smart Contracts
- `AdvancedMarkets.sol` locked-ether bug was **fixed** but contract is experimental
- `BuilderRewardPool` has divide-before-multiply precision loss (affects dust amounts)
- `DecentralizedOracle._tryAutoResolve()` has uninitialized local variable
- Gas optimizations identified by Slither (cache array lengths, use immutable) not applied

### Backend
- `services/embedded_wallet.py` -- PBKDF2 key derivation is a testnet shim. Runtime warning added for mainnet. Must be replaced with CDP Server Signer before any real deployment.
- `services/v2_resolution.py` -- Resolution is owner-based (single EOA). This is the biggest centralization risk.
- Several deprecated service files still in the repo (`.deprecated` suffix)

### Frontend
- Vanilla JS, no framework, no build step. Works but not scalable.
- Wallet connection UX needs real device testing.

---

## Competitive Landscape (February 2026)

| Platform | Model | On-chain? | Scoring |
|----------|-------|-----------|---------|
| Coinbase/Kalshi | Binary yes/no | No (Kalshi backend) | Binary |
| Polymarket | Binary yes/no | Yes (Polygon) | Binary |
| **Proteus Markets** | Text prediction | Yes (BASE) | Levenshtein distance |

The gap we're exploring: continuous scoring on a metric space vs binary outcomes. As AI capabilities improve, binary markets lose edge (trivially computable). Text prediction markets gain depth (exponential outcome space, continuous payoff gradient).

**X API Access (Feb 2026 update):** X's new [pay-per-use API model](https://developer.x.com/) removes the subscription barrier for oracle resolution. Individual developers can now access the X API v2 (post lookup, user verification, timestamps) with credit-based billing -- no $200/mo minimum. This makes multi-oracle tweet verification economically viable and is a key infrastructure prerequisite that was previously a blocker.

---

## Summary

| Category | Status |
|----------|--------|
| Core primitive (Levenshtein scoring) | **Working** |
| Smart contracts | **Deployed on testnet, need audit** |
| Backend | **Functional prototype** |
| Frontend | **Functional prototype** |
| Security | **Static analysis only, no external audit** |
| Production readiness | **Not ready** |
| Demand validation | **Not started** |
