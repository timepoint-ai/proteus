# Clockchain - Fully Decentralized Linguistic Prediction Platform

**Phase 7 Complete (August 2025)**: A fully decentralized, blockchain-only prediction market platform where users bet on the exact words public figures will say. Built exclusively on BASE blockchain with zero database dependencies, featuring advanced oracle systems, distributed governance, and production-grade performance optimizations.

## 🎯 What is Clockchain?

Clockchain creates prediction markets for linguistic outputs - users predict specific phrases that public figures will say within defined time windows. Winners are determined by measuring the Levenshtein distance between predictions and actual speech, with automated resolution through decentralized oracles. The entire system operates directly on blockchain with no centralized components.

## 💎 Genesis NFT System (Phase 1 Complete - January 2025)

### Improved Economics (7X Payout Increase!)
- **100 Genesis NFTs**: Fixed supply, on-chain minting window
- **Revenue Share**: 1.4% of ALL platform volume (20% of the 7% platform fees)
- **Per NFT**: 0.014% of platform volume
- **Deployment**: ImprovedDistributedPayoutManager at `0xE9eE183b76A8BDfDa8EA926b2f44137Aa65379B5`
- **SVG Art**: Generated entirely on-chain in `contracts/src/GenesisNFT.sol` using the `generateSVG()` function

### Revenue Projections
With 100 Genesis NFTs at $1M daily volume:
- Daily earnings: $14,000
- Monthly income: $420,000
- Annual income: $5,110,000

## 🚀 Quick Start

### Prerequisites
- MetaMask or Coinbase Wallet
- BASE Sepolia ETH for testing
- Node.js 18+ and Python 3.10+

### Installation

```bash
# Clone repository
git clone <repository>

# Install dependencies (auto-installed on Replit)
npm install
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your DEPLOYER_PRIVATE_KEY and other secrets
```

### Deploy Genesis NFTs

```bash
# Deploy to BASE Sepolia
npx hardhat run scripts/deploy-genesis-phase1.js --network baseSepolia

# Deploy improved payout system
npx hardhat run scripts/deploy-improved-payouts.js --network baseSepolia

# Mint Genesis NFTs
npx hardhat run scripts/mint-genesis.js --network baseSepolia

# Verify payouts
npx hardhat run scripts/verify-final-status.js --network baseSepolia
```

## 📊 Platform Architecture

### Smart Contract Stack (BASE Exclusive)
- **GenesisNFT**: 100 founder NFTs with on-chain SVG art generation
- **ImprovedDistributedPayoutManager**: 1.4% volume distribution to Genesis holders
- **EnhancedPredictionMarket**: Core market functionality with on-chain data
- **DecentralizedOracle**: Automated text analysis and resolution
- **TestMarketWithPayouts**: Testing infrastructure for payout verification

### Fee Distribution (Fully Decentralized)
Platform Fee: 7% of market volume
- **Genesis NFT Holders**: 20% → 1.4% of volume
- **Oracles**: 28.6% → 2% of volume
- **Node Operators**: 14.3% → 1% of volume
- **Market Creators**: 14.3% → 1% of volume
- **Builder Pool**: 28.6% → 2% of volume
- **Bittensor AI Pool**: 14.3% → 1% of volume

### Technology Stack (Fully Decentralized)
- **Blockchain**: BASE (Coinbase L2) exclusively - ALL data on-chain
- **Smart Contracts**: Solidity 0.8.19+ with full event indexing
- **Backend**: Flask + Web3.py (chain-only API routes)
- **Frontend**: Web3.js + MetaMask/Coinbase Wallet integration
- **Authentication**: Wallet-based JWT authentication only
- **Oracle**: Decentralized X.com integration with on-chain verification
- **Performance**: Redis caching + RPC retry logic with exponential backoff
- **Database**: REMOVED - All data now on blockchain

## 🔧 Development Commands

### Smart Contract Development
```bash
# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy to testnet
npx hardhat run scripts/deploy-improved-payouts.js --network baseSepolia

# Verify on Basescan
npx hardhat verify --network baseSepolia <CONTRACT_ADDRESS>
```

### Backend Services
```bash
# Start Flask application
python main.py
# or
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Start Celery worker
celery -A app.celery worker --loglevel=info

# Start monitoring service
python -m services.monitoring
```

## 🔄 Migration Status (Phase 7 Complete - August 2025)

### All 7 Phases Completed ✅
1. **Phase 1**: Database writes disabled, blockchain-first architecture
2. **Phase 2**: Wallet-only authentication implemented
3. **Phase 3**: Chain-only API routes created (/api/chain/*)
4. **Phase 4**: Configuration cleaned, database configs removed
5. **Phase 5**: Smart contract integration complete
6. **Phase 6**: Frontend fully integrated with Web3
7. **Phase 7**: Final cleanup - models.py removed, 27+ files cleaned

### Key Achievements
- **Zero Database Dependencies**: All data now on blockchain
- **Performance Optimized**: Redis caching + RPC retry logic
- **Production Ready**: Full error handling and monitoring
- **Fully Decentralized**: No admin functions, distributed governance

## 📁 Project Structure

```
├── contracts/              # Smart contracts
│   ├── src/
│   │   ├── GenesisNFT.sol          # On-chain SVG NFT art
│   │   ├── ImprovedDistributedPayoutManager.sol
│   │   └── TestMarketWithPayouts.sol
│   └── artifacts/          # Compiled contracts
├── scripts/                # Deployment & testing
│   ├── deploy-genesis-phase1.js
│   ├── deploy-improved-payouts.js
│   ├── mint-genesis.js
│   └── test-payouts-and-show-balance.js
├── deployments/            # Deployment records
│   ├── genesis-phase1-testnet.json
│   └── improved-genesis-testnet.json
├── services/               # Backend services
│   ├── blockchain_base.py
│   ├── oracle.py
│   └── monitoring.py
├── routes/                 # API endpoints
├── static/                 # Frontend assets
│   └── js/
│       ├── wallet.js
│       └── market-blockchain.js
├── templates/              # HTML templates
└── docs/                   # Documentation
```

## 🌟 Key Features

### For Genesis NFT Holders
- Earn 1.4% of all platform volume (7X improvement from initial design)
- Transparent on-chain payouts via ImprovedDistributedPayoutManager
- Unique on-chain generated SVG art (no external dependencies)
- Future governance rights over protocol changes

### For Market Participants
- Create linguistic prediction markets for any X.com user
- Bet on exact phrases with specific time windows
- Automated resolution via Levenshtein distance
- Instant payouts on winning predictions

### For Node Operators
- Earn 1% of platform volume
- Participate in consensus mechanisms
- Validate oracle submissions
- Secure the network

## 📈 Verified Transactions

Recent mainnet-ready transactions on BASE Sepolia:
- [Market Resolution with Payout](https://sepolia.basescan.org/tx/0x7ed4c83ec8a90159fee06e916ce74db5267e1e4f4be496a60505664e75c51330)
- [Genesis NFT Payout Distribution](https://sepolia.basescan.org/tx/0xdd9fba256c354062cc44a30104ee296af804e4bd4c634f752ef56100727311b9)

## 🔐 Security Features

- All smart contracts tested on BASE Sepolia
- Immutable Genesis NFT supply (100 maximum)
- No admin functions in payout contracts (fully decentralized)
- Time-locked minting window (24 hours for Genesis NFTs)
- Automated payout distribution (no manual intervention)

## 📚 Documentation

Core documentation in `/docs/`:
- [Engineering Architecture](docs/ENGINEERING.md) - Technical implementation details
- [Governance Model](docs/GOVERNANCE.md) - Decentralized governance structure
- [Platform Logic Analysis](docs/LOGIC.md) - Economic model and fee distribution
- [MetaMask Setup Guide](docs/METAMASK_SETUP.md) - Wallet configuration
- [Minting Guide](docs/MINTING_GUIDE.md) - How to mint Genesis NFTs
- [View Your NFTs](docs/VIEW_YOUR_NFTS.md) - Check your Genesis NFT collection

## 🚀 Roadmap

### ✅ Phase 1: Genesis NFT System (Complete - January 2025)
- Deployed Genesis NFT contract with 100 fixed supply
- Implemented 7X improved payout system (1.4% of volume)
- On-chain SVG art generation
- Verified on BASE Sepolia with real transactions

### 🔄 Phase 2: Mainnet Launch (In Progress)
- Deploy to BASE mainnet
- Open Genesis NFT minting window
- Launch initial prediction markets
- Activate oracle network

### 📅 Phase 3: Platform Expansion (Q2 2025)
- DAO governance implementation
- Advanced market types (conditional, range)
- Mobile applications
- Cross-chain bridges

### 🔮 Phase 4: AI Integration (Q3 2025)
- Bittensor subnet integration
- AI-powered prediction models
- TAO token rewards
- Neural network validation

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a PR with tests
4. Update documentation

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Important Links

- **BASE Sepolia Faucet**: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
- **Basescan Explorer**: https://sepolia.basescan.org
- **Contract Deployments**: See `/deployments/` directory
- **Support**: Open an issue on GitHub

---

**Built with ❤️ for the future of decentralized prediction markets**

*Current Testnet Status: 60 Genesis NFTs minted, ImprovedDistributedPayoutManager deployed and tested*