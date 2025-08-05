# On-Chain Migration & Cleanup Plan

## Overview
This document outlines the phased approach to remove legacy code and align the entire system with the fully on-chain architecture deployed on BASE Sepolia. All 14 phases are now live, requiring significant cleanup of database-dependent code and UI/UX alignment.

## Current State
- ✅ All 14 smart contracts deployed to BASE Sepolia
- ❌ Frontend still references database models heavily
- ❌ Backend has mixed database/blockchain calls
- ❌ UI/UX doesn't reflect on-chain capabilities
- ❌ Test data generation still uses database

## Phase 1: Backend Cleanup (Priority: CRITICAL)

### 1.1 Remove Database Dependencies from Core Services

| Service | Current State | Required Changes | Files to Modify |
|---------|--------------|------------------|-----------------|
| **PredictionMarket** | Hybrid DB/Chain | Remove all DB writes, read-only from chain | `services/blockchain_base.py` |
| **Submissions** | DB primary | Remove DB model, use EnhancedPredictionMarket | `models.py`, `routes/api.py` |
| **Bets** | DB primary | Remove DB model, use EnhancedPredictionMarket | `models.py`, `routes/api.py` |
| **Actors** | DB with chain sync | Remove DB model, use ActorRegistry only | `models.py`, `routes/actors.py` |
| **Oracle** | DB submissions | Use DecentralizedOracle contract | `services/oracle_xcom.py` |

### 1.2 Database Model Removal Checklist

- [ ] **Phase 1A: Make Models Read-Only**
  - [ ] Remove all `db.session.add()` calls
  - [ ] Remove all `db.session.commit()` for these models
  - [ ] Add deprecation warnings to model classes
  
- [ ] **Phase 1B: Replace with Blockchain Calls**
  - [ ] `PredictionMarket` → `EnhancedPredictionMarket.getMarket()`
  - [ ] `Submission` → `EnhancedPredictionMarket.getSubmission()`
  - [ ] `Bet` → `EnhancedPredictionMarket.getBet()`
  - [ ] `Actor` → `ActorRegistry.getActor()`
  - [ ] `OracleSubmission` → `DecentralizedOracle.getSubmission()`

- [ ] **Phase 1C: Remove Models Entirely**
  - [ ] Delete from `models.py`
  - [ ] Remove all imports
  - [ ] Update all references

### 1.3 Service Migration Table

| Old Service | New Contract | Migration Status | Action Required |
|-------------|--------------|------------------|-----------------|
| `services/ledger.py` | On-chain events | ❌ Not migrated | Remove file |
| `services/consensus.py` | DecentralizedOracle | ❌ Not migrated | Remove file |
| `services/bet_resolution.py` | DecentralizedOracle | ❌ Not migrated | Remove file |
| `services/text_analysis.py` | DecentralizedOracle | ✅ On-chain | Remove file |
| `services/payout_base.py` | PayoutManager | ⚠️ Partial | Update to chain-only |
| `services/monitoring.py` | Keep | ✅ Still needed | Fix oracle_votes error |

## Phase 2: Frontend Alignment (Priority: HIGH)

### 2.1 Route Updates

| Route | Current Functionality | Required Changes | Template Updates |
|-------|----------------------|------------------|------------------|
| `/` | Shows DB markets | Query chain via web3 | `index.html` |
| `/market/<id>` | DB market details | Get from EnhancedPredictionMarket | `market_detail.html` |
| `/actors` | DB actor list | Get from ActorRegistry | `actors.html` |
| `/submit` | DB submission | Call contract directly | `submit_prediction.html` |
| `/admin` | Mixed DB/chain | Chain-only dashboard | `admin_dashboard.html` |

### 2.2 UI/UX Improvements

- [ ] **Transaction Feedback**
  - [ ] Add MetaMask transaction status modals
  - [ ] Show gas estimation before transactions
  - [ ] Display transaction hashes with Basescan links
  - [ ] Add loading states during blockchain calls

- [ ] **Wallet Integration**
  - [ ] Prominent "Connect Wallet" button
  - [ ] Show connected address and balance
  - [ ] Network switching helper (BASE Sepolia/Mainnet)
  - [ ] Handle disconnections gracefully

- [ ] **Real-time Updates**
  - [ ] Subscribe to contract events via WebSocket
  - [ ] Update UI without page refresh
  - [ ] Show pending transactions
  - [ ] Display confirmation counts

### 2.3 Template Specific Changes

| Template | Remove | Add | Priority |
|----------|--------|-----|----------|
| `base.html` | DB connection status | Wallet connection widget | HIGH |
| `index.html` | Database queries | Web3 market queries | HIGH |
| `market_detail.html` | Form submissions | MetaMask transactions | HIGH |
| `actors.html` | Admin approval buttons | On-chain voting interface | MEDIUM |
| `admin_dashboard.html` | DB statistics | Contract statistics | MEDIUM |

## Phase 3: Test Infrastructure (Priority: MEDIUM)

### 3.1 Test Data Migration

- [ ] **Remove Database Test Data**
  - [ ] Delete `routes/test_data.py`
  - [ ] Delete `routes/test_data_new.py`
  - [ ] Delete `routes/test_data_v2.py`
  - [ ] Remove test data generation endpoints

- [ ] **Create On-Chain Test Tools**
  - [ ] Script to deploy test markets on-chain
  - [ ] Script to create test submissions
  - [ ] Script to place test bets
  - [ ] Use test wallets from `.test_wallets.json`

### 3.2 E2E Test Updates

| Test File | Current State | Required Changes |
|-----------|--------------|------------------|
| `test_e2e_runner.py` | Mixed DB/chain | Chain-only tests |
| `debug_e2e_test.py` | Database focused | Remove or update |
| `test_phase11_12.py` | Contract tests | Keep as-is |
| `test_phase13_14.py` | Contract tests | Keep as-is |

## Phase 4: Documentation & Cleanup (Priority: LOW)

### 4.1 File Deletion List

**Definitely Delete:**
- [ ] `models_old.py` - Legacy models
- [ ] `services/bet_resolution_old.py` - Replaced by on-chain
- [ ] `services/oracle_old.py` - Replaced by DecentralizedOracle
- [ ] `services/ledger.py` - Now on-chain events
- [ ] `services/consensus.py` - In DecentralizedOracle
- [ ] `services/mock_node_registry.py` - Use real NodeRegistry
- [ ] All `test_data*.py` routes

**Consider Deleting:**
- [ ] `CRYPTO_PLAN.md` - All phases complete
- [ ] `LAUNCH.md` - If launch plan executed
- [ ] `services/node_registry_service.py` - If fully on-chain

### 4.2 Documentation Updates

| Document | Updates Required | Priority |
|----------|-----------------|----------|
| `README.md` | Remove DB setup, add chain-only instructions | HIGH |
| `ENGINEERING.md` | Document on-chain architecture | HIGH |
| `replit.md` | Update architecture section | MEDIUM |
| `TEST_DATA_GUIDE.md` | Rewrite for on-chain testing | LOW |

## Phase 5: Production Readiness (Priority: MEDIUM)

### 5.1 Environment Configuration

- [ ] **Remove Database URLs**
  - [ ] Remove DATABASE_URL from production
  - [ ] Remove Redis dependency if not needed
  - [ ] Keep only blockchain RPC endpoints

- [ ] **Add Production Variables**
  - [ ] `BASE_MAINNET_RPC`
  - [ ] `PRODUCTION_PRIVATE_KEY`
  - [ ] `BASESCAN_API_KEY`
  - [ ] `X_API_KEY` (production)

### 5.2 Deployment Changes

- [ ] Update `main.py` to remove DB initialization
- [ ] Update `app.py` to remove SQLAlchemy
- [ ] Simplify deployment to static + RPC calls
- [ ] Remove Celery/Redis if not needed

## Implementation Order

1. **Week 1**: Backend cleanup (Phase 1)
   - Start with read-only models
   - Migrate one service at a time
   - Test each migration thoroughly

2. **Week 2**: Frontend alignment (Phase 2)
   - Update templates for Web3
   - Add wallet integration
   - Improve transaction UX

3. **Week 3**: Test & Documentation (Phase 3-4)
   - Clean up test infrastructure
   - Update all documentation
   - Delete legacy files

4. **Week 4**: Production prep (Phase 5)
   - Final testing
   - Environment cleanup
   - Mainnet deployment

## Success Metrics

- [ ] Zero database writes for core functionality
- [ ] All data sourced from blockchain
- [ ] Wallet-first user experience
- [ ] Clean codebase with no legacy files
- [ ] Updated documentation reflecting reality
- [ ] Successful BASE mainnet deployment

## Risk Mitigation

1. **Keep database read-only during transition**
   - Don't delete models until replacements work
   - Maintain backwards compatibility temporarily

2. **Test on Sepolia first**
   - Each change tested on testnet
   - User acceptance testing before mainnet

3. **Gradual rollout**
   - Feature flags for new functionality
   - A/B testing if needed

## Next Steps

1. Create feature branch: `on-chain-migration`
2. Start with Phase 1.1 - Backend cleanup
3. Daily progress updates in this document
4. Code review after each phase