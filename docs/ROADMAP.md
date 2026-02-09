# Roadmap

**v0 Alpha** -- Updated February 2026

This is a prototype. The roadmap reflects that honestly.

---

## Phase 0: Prove the Primitive (COMPLETE)

Validate that on-chain Levenshtein distance works as a prediction market scoring function.

- [x] PredictionMarketV2 deployed on BASE Sepolia
- [x] Full market lifecycle: create -> submit -> resolve -> claim
- [x] On-chain Levenshtein distance for winner determination
- [x] 259+ tests passing (109 contract, 135 unit, 15 integration)
- [x] Genesis NFT (60/100 minted, finalized)
- [x] Flask backend with wallet auth (MetaMask JWT + email OTP)
- [x] Admin resolution dashboard
- [x] Redis-backed auth storage with rate limiting
- [x] CI/CD pipeline, Slither static analysis
- [x] Structured logging, request tracing

**Result:** The primitive works. Smart contracts handle the full lifecycle. Levenshtein scoring resolves markets deterministically on-chain.

**Known tradeoffs (acceptable for prototype):**
- PBKDF2 embedded wallet shim (not real CDP)
- Single EOA for resolution (centralized)
- No multisig, no audit, no production infra

---

## Phase 0.5: Worked Examples (COMPLETE)

Populate 6 worked examples demonstrating the full spectrum of prediction quality.

- [x] README: 6 collapsible worked examples with verified Levenshtein distances
- [x] Seed script (`scripts/seed_examples.py`): create example markets on BASE Sepolia
- [x] Landing page: thesis example (AI vs AI, Satya Nadella) in "How It Works" section
- [x] Fix 4 pre-existing unit test failures (135 unit tests now pass)

---

## Phase 1: Validate Demand (NOT STARTED)

Before spending money on audits or infrastructure, answer the question: do people want this?

- [ ] Ship testnet demo publicly
- [ ] Get real users submitting predictions
- [ ] Collect feedback on the text prediction UX
- [ ] Determine if the market mechanic is engaging
- [ ] Identify the right market categories (tweets, speeches, press releases?)

**Decision gate:** If nobody cares, stop here. If there's signal, continue.

---

## Phase 2: Security & Infrastructure (BLOCKED on Phase 1 signal)

Only worth doing if Phase 1 shows demand.

### External Audit
- [ ] Engage auditor for ~1,025 lines of in-scope Solidity
- [ ] PredictionMarketV2.sol (513 lines, CRITICAL)
- [ ] GenesisNFT.sol (288 lines, HIGH)
- [ ] ImprovedDistributedPayoutManager.sol (224 lines, HIGH)
- [ ] Remediate findings

### Infrastructure
- [ ] Obtain Coinbase CDP credentials
- [ ] Replace PBKDF2 shim with CDP Server Signer
- [ ] Production RPC (Alchemy or QuickNode)
- [ ] Monitoring (Sentry)
- [ ] Multisig (Gnosis Safe 2-of-3) for contract owner

---

## Phase 3: Mainnet (BLOCKED on Phase 2)

### Go/No-Go Checklist
- [ ] External audit complete, critical/high addressed
- [ ] Real CDP wallet integration working
- [ ] Owner key in multisig
- [ ] Monitoring operational
- [ ] Incident response plan documented

### Deployment
- [ ] Dry-run on fresh Sepolia
- [ ] Deploy PredictionMarketV2 to BASE mainnet
- [ ] Deploy PayoutManager
- [ ] Verify contracts on Basescan

---

## Phase 4: Decentralize (FUTURE)

After mainnet is stable and has users.

- [ ] Oracle commit-reveal (prevent front-running)
- [ ] Slashing mechanism for dishonest oracles
- [ ] Node operator onboarding (staked participation)
- [ ] Migration to EnhancedPredictionMarket (full governance)
- [ ] Consider Kalshi API integration as data source
- [ ] X API pay-per-use integration for multi-oracle tweet verification

> **X API Update (Feb 2026):** X now offers [pay-per-use API access](https://developer.x.com/) for individual developers -- credit-based billing, no subscriptions or monthly caps. This unblocks the multi-oracle verification model: each oracle node can independently call the X API v2 to fetch a post by ID, verify the author handle, and confirm the timestamp, paying only for the API calls it actually makes. Previously the $200/mo Basic tier (15K reads) or $5,000/mo Pro tier (1M reads) made independent per-oracle verification cost-prohibitive. This is a prerequisite for decentralized resolution.

---

## Deployed Contracts (BASE Sepolia)

| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | Active |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | 60/100 minted |

BASE Mainnet: Not deployed. Blocked on audit + prerequisites.
