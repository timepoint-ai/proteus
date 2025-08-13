# Clockchain Code Cleanup Guide - BASE-Only Architecture

## Executive Summary

This document provides a comprehensive audit of all code components that need modification to transition from the hybrid database/blockchain model to a pure BASE blockchain architecture. All local storage must be eliminated in favor of on-chain data.

## 1. Backend Services Audit

### 1.1 Core Services (/services)

| Service | Current State | Required Changes | Priority |
|---------|--------------|------------------|----------|
| **blockchain_base.py** | Hybrid DB/chain reads | Remove all DB reads, pure chain queries | HIGH |
| **oracle.py** | DB writes for submissions | Chain-only oracle submissions | HIGH |
| **consensus.py** | DB-based voting | On-chain consensus via smart contract | HIGH |
| **text_analysis.py** | Local Levenshtein calc | Move to on-chain oracle contract | MEDIUM |
| **ledger.py** | PostgreSQL ledger | Remove entirely (use chain events) | HIGH |
| **time_sync.py** | Local time management | Use block timestamps | MEDIUM |
| **monitoring.py** | Mixed DB/chain metrics | Chain-only monitoring | LOW |
| **contract_monitoring.py** | Event tracking to DB | Remove DB writes, use logs | HIGH |

#### Code Changes Required:

```python
# OLD: blockchain_base.py
def get_market_data(market_id):
    # Check database first
    market = db.session.query(PredictionMarket).filter_by(id=market_id).first()
    if market:
        return market
    # Fallback to blockchain
    return get_market_from_chain(market_id)

# NEW: blockchain_base.py
def get_market_data(market_id):
    # Only fetch from blockchain
    contract = w3.eth.contract(address=MARKET_ADDRESS, abi=MARKET_ABI)
    return contract.functions.getMarket(market_id).call()
```

### 1.2 Database Models (/models.py)

| Model | Usage | Action Required |
|-------|-------|-----------------|
| **NodeOperator** | User accounts | Remove - use wallet addresses |
| **Actor** | X.com accounts | Move to ActorRegistry contract |
| **PredictionMarket** | Market data | Remove - use chain events |
| **Submission** | Predictions | Remove - use chain events |
| **Bet** | User bets | Remove - use chain events |
| **Transaction** | TX records | Remove - use chain TX history |
| **OracleSubmission** | Oracle data | Remove - use oracle contract |
| **SyntheticTimeEntry** | Time ledger | Remove - use block timestamps |

**Action: Delete models.py entirely after migrating all queries to blockchain**

## 2. Frontend Components Audit

### 2.1 Templates (/templates)

| Template | Current Issues | Required Changes |
|----------|---------------|------------------|
| **index.html** | DB-based market list | Fetch markets from chain |
| **market_detail.html** | Mixed DB/chain data | Pure chain data display |
| **create_market.html** | Form posts to backend | Direct contract interaction |
| **admin_dashboard.html** | DB statistics | Chain analytics only |
| **node_dashboard.html** | DB node status | On-chain node registry |
| **timeline.html** | DB timeline entries | Chain event logs |
| **test_manager.html** | DB test data | Remove or chain-only tests |

### 2.2 JavaScript Files (/static/js)

| File | Current State | Required Changes | Status |
|------|--------------|------------------|--------|
| **wallet.js** | Good - wallet connection | Add Coinbase Wallet SDK | UPDATE |
| **market-blockchain.js** | Partial chain integration | Full chain-only | UPDATE |
| **timeline-blockchain.js** | Mixed DB/chain | Remove DB calls | UPDATE |
| **market-detail-blockchain.js** | Mixed implementation | Pure chain | UPDATE |
| **admin-blockchain-stats.js** | DB statistics | Chain analytics | UPDATE |
| **test-manager.js** | DB operations | Remove or rewrite | DELETE |

#### JavaScript Migration Example:

```javascript
// OLD: market-blockchain.js
async function loadMarkets() {
    // Fetch from backend API
    const response = await fetch('/api/markets');
    const markets = await response.json();
    displayMarkets(markets);
}

// NEW: market-blockchain.js
async function loadMarkets() {
    // Direct blockchain query
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const contract = new ethers.Contract(MARKET_ADDRESS, MARKET_ABI, provider);
    
    // Get all market events
    const filter = contract.filters.MarketCreated();
    const events = await contract.queryFilter(filter, 0, 'latest');
    
    const markets = await Promise.all(
        events.map(async (event) => {
            const market = await contract.getMarket(event.args.marketId);
            return formatMarketData(market);
        })
    );
    
    displayMarkets(markets);
}
```

## 3. API Routes Audit (/routes)

### 3.1 API Endpoints

| Route File | Endpoints | Action Required |
|------------|-----------|-----------------|
| **main.py** | DB-based routes | Remove or convert to chain readers |
| **market_routes.py** | CRUD operations | Direct contract calls only |
| **admin_routes.py** | DB statistics | Chain analytics endpoints |
| **node_routes.py** | Node management | On-chain registry only |
| **api_routes.py** | Mixed DB/chain | Pure chain data APIs |

### 3.2 Routes to Remove

```python
# DELETE these routes entirely:
@app.route('/market/create', methods=['POST'])  # Use contract directly
@app.route('/market/<id>/edit', methods=['POST'])  # Immutable on-chain
@app.route('/admin/users')  # No user accounts, only wallets
@app.route('/admin/database')  # No database operations
@app.route('/test/generate')  # No test data generation
```

### 3.3 Routes to Modify

```python
# MODIFY to chain-only:
@app.route('/market/<id>')  # Fetch from blockchain
@app.route('/api/markets')  # Query chain events
@app.route('/api/stats')  # Calculate from chain data
@app.route('/profile/<address>')  # Wallet-based profiles
```

## 4. Configuration Files Audit

### 4.1 Environment Variables

| Variable | Current Use | Action |
|----------|------------|--------|
| DATABASE_URL | PostgreSQL connection | REMOVE |
| FLASK_SECRET_KEY | Session management | REMOVE (no sessions) |
| REDIS_URL | Caching | KEEP (for performance) |
| BASE_RPC_URL | Chain connection | KEEP |
| PRIVATE_KEY | Deployment only | REMOVE from app |
| CONTRACT_ADDRESSES | Chain contracts | KEEP |

### 4.2 Configuration Files

```python
# OLD: config.py
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    
# NEW: config.py
class Config:
    BASE_RPC_URL = os.getenv('BASE_RPC_URL', 'https://mainnet.base.org')
    CHAIN_ID = int(os.getenv('CHAIN_ID', '8453'))
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    # No database, no sessions
```

## 5. Smart Contract Integration Checklist

### 5.1 Required Contract Functions

| Contract | Missing Functions | Priority |
|----------|------------------|----------|
| **EnhancedPredictionMarket** | `getAllMarkets()`, `getMarketsByActor()` | HIGH |
| **GenesisNFT** | `tokenURI()` for metadata | MEDIUM |
| **DecentralizedOracle** | `getOracleHistory()` | MEDIUM |
| **ActorRegistry** | `searchActors()`, `getActorStats()` | HIGH |
| **NodeRegistry** | `getActiveNodes()`, `getNodePerformance()` | MEDIUM |

### 5.2 Event Indexing Requirements

```solidity
// Add these events for better querying:
event MarketCreated(uint256 indexed marketId, address indexed creator, address indexed actor);
event SubmissionMade(uint256 indexed marketId, address indexed submitter, uint256 timestamp);
event BetPlaced(uint256 indexed marketId, uint256 indexed submissionId, address indexed bettor);
event MarketResolved(uint256 indexed marketId, uint256 winningSubmission, uint256 totalPayout);
```

## 6. Testing Infrastructure Cleanup

### 6.1 Test Files to Remove

| File | Purpose | Action |
|------|---------|--------|
| test_data.py | DB test data | DELETE |
| test_data_new.py | DB test data | DELETE |
| test_data_v2.py | DB test data | DELETE |
| test_data_ai.py | DB test data | DELETE |
| mock_node_registry.py | Mock nodes | DELETE |
| test_rig_setup.py | DB testing | DELETE |

### 6.2 New Test Infrastructure

```javascript
// scripts/test-chain-only.js
const testChainOnly = async () => {
    // 1. Deploy test contracts
    await deployTestContracts();
    
    // 2. Create test markets on-chain
    await createTestMarkets();
    
    // 3. Test wallet interactions
    await testWalletConnections();
    
    // 4. Verify chain queries
    await verifyChainQueries();
    
    // 5. Test gas optimization
    await testGasUsage();
};
```

## 7. Component Priority Matrix

### 7.1 Critical Path (Week 1)

| Component | Work Required | Complexity |
|-----------|---------------|------------|
| Remove DB writes | Delete all DB write operations | LOW |
| Wallet-only auth | Remove session management | MEDIUM |
| Chain queries | Replace DB reads with chain | HIGH |
| Contract updates | Add missing query functions | HIGH |

### 7.2 Secondary Tasks (Week 2)

| Component | Work Required | Complexity |
|-----------|---------------|------------|
| Frontend refactor | Update all JS to chain-only | MEDIUM |
| API cleanup | Remove unnecessary endpoints | LOW |
| Event indexing | Implement efficient queries | HIGH |
| Testing update | Chain-based test suite | MEDIUM |

### 7.3 Polish Phase (Week 3)

| Component | Work Required | Complexity |
|-----------|---------------|------------|
| Performance | Optimize RPC calls | HIGH |
| Caching | Redis for chain data | MEDIUM |
| Analytics | On-chain metrics | MEDIUM |
| Documentation | Update all docs | LOW |

## 8. Migration Script

### 8.1 Database to Chain Migration

```python
# scripts/migrate_to_chain.py
async def migrate_to_chain():
    """One-time migration of existing data to chain"""
    
    # 1. Export existing markets
    markets = db.session.query(PredictionMarket).all()
    for market in markets:
        # Skip - markets already on chain
        pass
    
    # 2. Export actor registry
    actors = db.session.query(Actor).all()
    for actor in actors:
        await actor_registry.registerActor(
            actor.xcom_username,
            actor.xcom_user_id
        )
    
    # 3. Export node registry
    nodes = db.session.query(NodeOperator).all()
    for node in nodes:
        await node_registry.registerNode(
            node.wallet_address,
            node.name
        )
    
    print("Migration complete - database can be removed")
```

## 9. Removal Checklist

### 9.1 Files to Delete

```bash
# Backend files to remove
rm models.py
rm models_old.py
rm migrations/
rm test_data*.py
rm mock_*.py

# Frontend files to remove
rm static/js/test-manager.js
rm templates/test_manager.html
rm templates/admin_database.html

# Configuration to remove
rm alembic.ini
rm database.db
```

### 9.2 Dependencies to Remove

```python
# From requirements.txt, remove:
SQLAlchemy
Flask-SQLAlchemy
Flask-Migrate
alembic
psycopg2-binary

# From package.json, remove:
# (None - all Web3 dependencies needed)
```

## 10. Validation Checklist

### 10.1 Pre-Launch Validation

- [ ] No database connections in code
- [ ] All data fetched from blockchain
- [ ] Wallet-only authentication
- [ ] No server-side sessions
- [ ] Direct contract interactions
- [ ] Event-based data queries
- [ ] Gas-optimized operations
- [ ] Proper error handling
- [ ] Loading states for chain queries
- [ ] Fallback RPC providers

### 10.2 Post-Launch Monitoring

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| RPC response time | < 500ms | > 1000ms |
| Gas per transaction | < 200k | > 500k |
| Failed transactions | < 1% | > 5% |
| Wallet connect rate | > 80% | < 60% |
| Page load time | < 2s | > 5s |

## Appendix A: Code Snippets

### Wallet-Based User System

```javascript
// No more user accounts, only wallets
class WalletUser {
    constructor(address) {
        this.address = address;
        this.ensName = null;
        this.avatar = null;
    }
    
    async load() {
        // Load ENS name
        const provider = new ethers.providers.Web3Provider(window.ethereum);
        this.ensName = await provider.lookupAddress(this.address);
        
        // Load on-chain data
        this.genesisNFTs = await this.getGenesisNFTs();
        this.markets = await this.getMarkets();
        this.earnings = await this.getEarnings();
    }
}
```

### Chain-Only Data Fetching

```javascript
// Replace all API calls with direct chain queries
async function fetchAllData() {
    const provider = new ethers.providers.Web3Provider(window.ethereum);
    const contracts = {
        market: new ethers.Contract(MARKET_ADDRESS, MARKET_ABI, provider),
        genesis: new ethers.Contract(GENESIS_ADDRESS, GENESIS_ABI, provider),
        oracle: new ethers.Contract(ORACLE_ADDRESS, ORACLE_ABI, provider)
    };
    
    // Parallel fetch all data
    const [markets, nfts, oracles] = await Promise.all([
        fetchMarkets(contracts.market),
        fetchNFTs(contracts.genesis),
        fetchOracles(contracts.oracle)
    ]);
    
    return { markets, nfts, oracles };
}
```

## Appendix B: Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Backend cleanup | Remove DB, implement chain queries |
| 2 | Frontend migration | Wallet-only UI, direct contract calls |
| 3 | Testing & optimization | Performance tuning, gas optimization |
| 4 | Launch preparation | Final cleanup, documentation |

---

*Last Updated: January 2025*
*Version: 1.0.0 - Cleanup Guide for BASE-Only Architecture*