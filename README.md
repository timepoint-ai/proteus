# Clockchain

A fully decentralized prediction market on BASE blockchain where users bet on exact phrases public figures will say.

## What It Does

Users create markets predicting specific text a public figure will say on X.com (Twitter). Winners are determined by Levenshtein distance (text similarity) with automated oracle resolution. The entire system operates on-chain with zero database dependencies.

## Current Status

| Component | Status |
|-----------|--------|
| Smart Contracts | Deployed on BASE Sepolia |
| Genesis NFTs | 60/100 minted (finalized) |
| Architecture | Fully on-chain (no database) |
| UI/Contract Integration | Complete (PredictionMarketV2) |
| V2 Resolution | Complete (admin dashboard + Celery tasks) |
| Wallet Integration | ~90% complete |
| Session Persistence | Complete |
| Mobile Responsiveness | CSS complete (device testing needed) |
| Error Handling | Complete (standardized API responses) |
| Tests | 180 passing (56 unit + 109 contract + 15 integration) |
| CI/CD | GitHub Actions (automated testing) |
| Security Analysis | Slither complete (1 bug fixed) |
| External Audit | Pending |
| Mainnet | Not deployed |

## Deployed Contracts (BASE Sepolia)

| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | **Recommended** |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | Active |
| EnhancedPredictionMarket | `0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c` | Requires governance |
| ActorRegistry | `0xC71CC19C5573C5E1E144829800cD0005D0eDB723` | Active |
| NodeRegistry | `0xA69C842F335dfE1F69288a70054A34018282218d` | Active |
| PayoutManager | `0x88d399C949Ff2f1aaa8eA5a859Ae4d97c74f6871` | Active |
| DecentralizedOracle | `0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1` | Active |

> **Note**: Use **PredictionMarketV2** for all new development. It includes complete market lifecycle with on-chain Levenshtein distance winner determination. V1 is deprecated (lacks resolution mechanism).

## Genesis NFT Economics

- **Total Supply**: 100 NFTs (fixed, immutable)
- **Holder Revenue**: 1.4% of all platform volume (20% of 7% platform fee)
- **Per NFT**: 0.014% of platform volume

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- BASE Sepolia ETH ([faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet))

### Run Locally
```bash
# Install dependencies
npm install

# Set up Python virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"

# Run all tests
make test-all

# Or run separately
make test-unit        # Python unit tests (56 tests)
make test-contracts   # Solidity tests (109 tests)
make test-integration # Integration tests (15 tests, requires server)

# Start backend
python main.py
```

### Deploy Contracts
```bash
# Deploy to BASE Sepolia
npx hardhat run scripts/deploy-genesis-phase1.js --network baseSepolia

# Verify on Basescan
npx hardhat verify --network baseSepolia <CONTRACT_ADDRESS>
```

## Project Structure

```
contracts/src/     # Solidity smart contracts
contracts/test/    # Hardhat tests
scripts/           # Deployment scripts
services/          # Python backend services
routes/            # Flask API endpoints
static/js/         # Frontend JavaScript
templates/         # HTML templates
tests/             # Python tests (unit, integration, e2e)
docs/              # Documentation
```

## Technology Stack

- **Blockchain**: BASE (Coinbase L2)
- **Contracts**: Solidity 0.8.20, OpenZeppelin, Hardhat
- **Backend**: Flask, Web3.py, Celery, Redis
- **Auth**: Firebase (email OTP) + Coinbase Embedded Wallet

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Technical design
- [Setup Guide](docs/SETUP.md) - Development environment
- [Contracts](docs/CONTRACTS.md) - Smart contract reference
- [API](docs/API_DOCUMENTATION.md) - API endpoints
- [Betting Guide](docs/CHAIN_SUBMISSION_GUIDE.md) - How to place bets and predictions
- [Security Analysis](docs/SECURITY-ANALYSIS.md) - Slither audit results
- [Roadmap](docs/ROADMAP.md) - Development phases
- [Gap Analysis](docs/GAPS.md) - Remaining work for launch

## Fee Distribution

Platform fee: 7% of market volume

| Recipient | Share |
|-----------|-------|
| Genesis NFT Holders | 20% (1.4% of volume) |
| Oracles | 28.6% (2% of volume) |
| Market Creators | 14.3% (1% of volume) |
| Node Operators | 14.3% (1% of volume) |
| Builder Pool | 28.6% (2% of volume) |

## Links

- [BASE Sepolia Explorer](https://sepolia.basescan.org)
- [BASE Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)

## License

MIT
