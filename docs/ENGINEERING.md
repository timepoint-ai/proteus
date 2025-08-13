# Clockchain Engineering Architecture

## Executive Summary

Clockchain is a fully decentralized linguistic prediction market platform built exclusively on BASE blockchain. The platform enables users to create markets predicting exact phrases public figures will say, with automated resolution through Levenshtein distance calculations and decentralized oracles.

## Genesis NFT System Architecture (Phase 1 Complete)

### Smart Contract Design
The Genesis NFT system represents the core economic innovation of Clockchain, providing founder rewards through a revolutionary payout structure.

#### GenesisNFT Contract (`contracts/src/GenesisNFT.sol`)
- **Fixed Supply**: 100 NFTs maximum, enforced on-chain
- **Minting Window**: 24-hour time-locked period after deployment
- **SVG Generation**: Complete on-chain art generation in `generateSVG()` function
  - Unique hexagonal patterns based on token ID
  - Dynamic color generation from seed values
  - No external dependencies or IPFS storage
- **Auto-finalization**: Minting automatically closes after max supply or deadline

#### ImprovedDistributedPayoutManager Contract
- **Address**: `0xE9eE183b76A8BDfDa8EA926b2f44137Aa65379B5` (BASE Sepolia)
- **Payout Structure**: 
  - Genesis holders receive 20% of platform fees (1.4% of volume)
  - 7X improvement from initial 0.2% design
  - Automatic distribution to all NFT holders
- **No Admin Functions**: Fully decentralized, immutable payout logic

### Economic Model

#### Platform Fee Distribution (7% of Market Volume)
```
Total Platform Fee: 7% of volume
├── Genesis NFT Holders: 20% → 1.4% of volume
├── Oracle Network: 28.6% → 2% of volume  
├── Node Operators: 14.3% → 1% of volume
├── Market Creators: 14.3% → 1% of volume
├── Builder Pool: 28.6% → 2% of volume
└── Bittensor AI Pool: 14.3% → 1% of volume
```

#### Revenue Projections (100 Genesis NFTs)
- $100K daily volume → $1,400/day
- $1M daily volume → $14,000/day
- $10M daily volume → $140,000/day

## Core Platform Architecture

### Blockchain Layer (BASE Exclusive)

#### Smart Contract Stack
1. **EnhancedPredictionMarket**: Core market functionality with full on-chain data
2. **DecentralizedOracle**: Text analysis and Levenshtein distance calculation
3. **NodeRegistry**: Decentralized node operator management
4. **ActorRegistry**: On-chain X.com actor validation
5. **AdvancedMarkets**: Multi-choice, conditional, and range markets
6. **SecurityAudit**: Production security features

#### Transaction Flow
```
User Submission → Smart Contract Validation → Event Emission
                                            ↓
                                     Oracle Processing
                                            ↓
                                     Consensus Voting
                                            ↓
                                     Market Resolution
                                            ↓
                                     Payout Distribution
```

### Backend Architecture

#### Technology Stack
- **Framework**: Flask 3.0+ with async support
- **Blockchain**: Web3.py 6.0+ for BASE interaction
- **Task Queue**: Celery 5.3+ with Redis broker
- **Database**: PostgreSQL (legacy, read-only)
- **Cache**: Redis for real-time data
- **WebSockets**: Socket.IO for live updates

#### Service Architecture
```
services/
├── blockchain_base.py      # Core blockchain interactions
├── oracle.py              # X.com data fetching & validation
├── consensus.py           # Node consensus mechanisms
├── text_analysis.py       # Levenshtein distance calculations
├── monitoring.py          # Production monitoring & alerts
└── contract_monitoring.py # Smart contract event tracking
```

#### Key Services

**Oracle Service**
- X.com API integration for tweet fetching
- Playwright-based screenshot capture for proof
- Automated text extraction and validation
- Submission to on-chain oracle contract

**Consensus Service**
- 66% agreement threshold for validation
- Weight-based voting for established nodes
- Slashing conditions for malicious actors
- Automatic reward distribution

**Monitoring Service**
- Gas price tracking and alerts
- Oracle consensus monitoring
- Node health checks
- Contract event logging

### Frontend Architecture

#### Web3 Integration
```
static/js/
├── wallet.js              # MetaMask/Coinbase Wallet connection
├── market-blockchain.js   # Market creation & betting
├── genesis-nft.js        # NFT minting & viewing
└── payout-tracker.js     # Real-time payout monitoring
```

#### User Flow
1. Connect wallet (MetaMask/Coinbase)
2. Auto-switch to BASE network
3. Create market or place bet
4. Sign transaction
5. Receive confirmation
6. Track payouts in real-time

### Database Schema (Legacy, Read-Only)

The platform maintains a PostgreSQL database for historical data and fast queries, but all write operations occur on-chain.

#### Key Tables
- `prediction_markets`: Historical market data
- `submissions`: Past prediction submissions
- `bets`: Betting history
- `transactions`: Transaction records
- `oracle_submissions`: Oracle validation history

## Security Architecture

### Smart Contract Security
- Reentrancy guards on all payment functions
- Integer overflow protection (Solidity 0.8.19+)
- Time-lock mechanisms for critical operations
- No upgradeable proxies (immutable contracts)

### Backend Security
- Private key management via environment variables
- Rate limiting on all API endpoints
- CORS configuration for approved domains
- Input validation and sanitization

### Oracle Security
- Multiple oracle sources for validation
- Screenshot proof requirements
- Consensus-based resolution
- Slashing for false submissions

## Deployment Architecture

### Development Environment
```bash
# Local blockchain
npx hardhat node

# Deploy contracts
npx hardhat run scripts/deploy.js --network localhost

# Start backend
python main.py
```

### Testnet (BASE Sepolia)
```bash
# Deploy contracts
npx hardhat run scripts/deploy-genesis-phase1.js --network baseSepolia

# Verify contracts
npx hardhat verify --network baseSepolia <address>

# Monitor
python -m services.monitoring
```

### Production (BASE Mainnet)
```bash
# Deploy with hardware wallet
npx hardhat run scripts/deploy-mainnet.js --network baseMainnet

# Start services
gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
celery -A app.celery worker --loglevel=warning
```

## Performance Optimizations

### Blockchain Optimizations
- Batch transaction processing
- Event log indexing for fast queries
- Gas-efficient contract design
- Minimal on-chain storage

### Backend Optimizations
- Redis caching for frequent queries
- Async processing for non-critical tasks
- Connection pooling for database
- CDN for static assets

### Frontend Optimizations
- Lazy loading for contract interactions
- WebSocket subscriptions for real-time data
- Local storage for wallet preferences
- Optimistic UI updates

## Monitoring & Observability

### Metrics Tracked
- Gas prices and transaction costs
- Oracle response times
- Consensus participation rates
- Market creation velocity
- Payout distribution latency

### Alert Thresholds
- Gas price > 100 gwei
- Oracle failures > 10%
- Node participation < 66%
- Contract balance < 1 ETH

## Testing Strategy

### Smart Contract Testing
```bash
# Unit tests
npx hardhat test

# Coverage
npx hardhat coverage

# Gas reporting
REPORT_GAS=true npx hardhat test
```

### Integration Testing
```bash
# Deploy test contracts
npx hardhat run scripts/test-e2e.js --network baseSepolia

# Run integration suite
pytest tests/integration/
```

### Load Testing
```bash
# Simulate high volume
python scripts/load_test.py --users 1000 --duration 3600
```

## Future Architecture Plans

### Phase 2: Mainnet Launch
- Multi-sig deployment process
- Gradual rollout strategy
- Emergency pause mechanisms
- Insurance fund implementation

### Phase 3: Scaling Solutions
- Layer 2 optimizations
- State channel implementations
- IPFS for large data storage
- Cross-chain bridges

### Phase 4: Advanced Features
- AI model integration via Bittensor
- Prediction aggregation algorithms
- Reputation-based weighting
- Governance token launch

## Development Guidelines

### Code Standards
- Solidity style guide compliance
- Python PEP 8 formatting
- Comprehensive documentation
- 80% test coverage minimum

### Git Workflow
```bash
main
├── develop
│   ├── feature/genesis-nft
│   ├── feature/improved-payouts
│   └── feature/oracle-upgrade
└── release/v2.0.0
```

### Deployment Checklist
- [ ] All tests passing
- [ ] Security audit complete
- [ ] Gas optimization verified
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Backup procedures tested

## Contact & Support

For engineering questions or architectural discussions, please open an issue on GitHub or contact the development team.

---

*Last Updated: January 2025*
*Version: 2.0.0 - Genesis NFT Improvement Release*