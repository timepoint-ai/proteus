# On-Chain Migration & Cleanup Plan

## Overview
This document outlines the phased approach to remove legacy code and align the entire system with the fully on-chain architecture deployed on BASE Sepolia. All 14 phases are now live, requiring significant cleanup of database-dependent code and UI/UX alignment.

## Current State
- ✅ All 14 smart contracts deployed to BASE Sepolia
- ✅ Phase 1: Backend cleanup completed (database writes disabled)
- ✅ Phase 2: Frontend Web3 integration completed
- ✅ Phase 3: Test infrastructure migrated to blockchain (August 5, 2025)
- ❌ Phase 4: Documentation and final cleanup pending

## Completed Phases

### Phase 1: Backend Cleanup ✅ COMPLETED
- Disabled all database write operations
- Maintained read-only access for legacy data
- Added blockchain read methods to services
- System now operates in hybrid mode with blockchain as source of truth

### Phase 2: Frontend Alignment ✅ COMPLETED
- Added MetaMask wallet integration in navbar
- Created Web3.js market query system (market-blockchain.js)
- Built transaction handlers for submissions and bets
- Added real-time blockchain statistics to admin dashboard
- Implemented event subscriptions for live updates
- Added contract ABI endpoint for Web3 integration

## Phase 3: Test Infrastructure (Priority: HIGH)

### Completed Items from Phase 1 & 2:

**Backend Changes (Phase 1):**
- ✅ Disabled all database write operations 
- ✅ Made models read-only with blockchain fallback
- ✅ Added deprecation warnings to affected services
- ✅ Blockchain read methods implemented in services

**Frontend Changes (Phase 2):**
- ✅ Added MetaMask wallet connection widget to navbar
- ✅ Implemented Web3.js for blockchain queries
- ✅ Created transaction handlers for submissions/bets
- ✅ Added real-time event subscriptions
- ✅ Updated admin dashboard with contract statistics
- ✅ Implemented loading states and transaction feedback

### Implementation Details:

**New JavaScript Files Created:**
- `wallet.js` - MetaMask connection management
- `market-blockchain.js` - Direct blockchain market queries
- `timeline-blockchain.js` - Real-time timeline updates
- `market-detail-blockchain.js` - Transaction handling
- `admin-blockchain-stats.js` - Contract statistics display

**API Enhancements:**
- Added `/api/contract-abi/<contract_name>` endpoint for Web3 integration
- Contract ABIs served from artifacts directory

## Remaining Phases

### Phase 3: Test Infrastructure ✅ COMPLETED (August 5, 2025)

#### 3.1 Test Data Migration

- [x] **Remove Database Test Data**
  - [x] Delete `routes/test_data.py`
  - [x] Delete `routes/test_data_new.py`
  - [x] Delete `routes/test_data_v2.py`
  - [x] Delete `routes/test_data_ai.py`
  - [x] Remove test data generation endpoints

- [x] **Create On-Chain Test Tools**
  - [x] Script to deploy test markets on-chain (`scripts/blockchain_test_data.py`)
  - [x] Script to create test submissions
  - [x] Script to place test bets
  - [x] Script to clean test data (`scripts/clean_blockchain_test_data.py`)
  - [x] Use test wallets from `.test_wallets.json`

#### 3.2 E2E Test Updates

- [x] **Updated Test Manager**
  - [x] Modified `clean_test_data()` to use blockchain cleanup script
  - [x] Added `generate_data()` endpoint for blockchain test data generation
  - [x] Imports `subprocess` to run blockchain scripts

| Test File | Current State | Required Changes | Status |
|-----------|--------------|------------------|--------|
| `test_e2e_runner.py` | Mixed DB/chain | Chain-only tests | Pending |
| `debug_e2e_test.py` | Database focused | Remove or update | Pending |
| `test_phase11_12.py` | Contract tests | Keep as-is | ✅ Confirmed |
| `test_phase13_14.py` | Contract tests | Keep as-is | ✅ Confirmed |

### Phase 4: Documentation & Cleanup (Pending)

#### 4.1 File Deletion List (After Phase 3)

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