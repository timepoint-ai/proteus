# Setup Guide

**v0 Alpha** -- Development environment setup for the Proteus Markets prototype.

## Prerequisites

- Node.js 18+
- Python 3.10+
- Redis server
- MetaMask or Coinbase Wallet

## 1. Clone and Install

```bash
git clone https://github.com/proteus-markets/proteus-markets
cd proteus-markets

# Install Node dependencies
npm install

# Set up Python virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -e ".[test]"
```

## 2. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env
```

### Required Variables

```bash
# Network
NETWORK=base-sepolia
CHAIN_ID=84532
RPC_URL=https://sepolia.base.org

# Deployer wallet (for contract deployment)
DEPLOYER_PRIVATE_KEY=your_private_key_here

# Redis
REDIS_URL=redis://localhost:6379

# Firebase (for email authentication)
FIREBASE_API_KEY=your_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project
FIREBASE_APP_ID=your_app_id

# Coinbase (for embedded wallet)
COINBASE_PROJECT_ID=your_project_id
```

## 3. Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication > Email/Password
4. Enable Email link (passwordless sign-in)
5. Add your domain to Authorized domains
6. Copy credentials to `.env`

See [FIREBASE-SETUP-GUIDE.md](../FIREBASE-SETUP-GUIDE.md) for detailed steps.

## 4. Coinbase Developer Platform

1. Sign up at [CDP Console](https://portal.cdp.coinbase.com/)
2. Create a project
3. Generate API keys with permissions:
   - `wallet:create`
   - `wallet:read`
   - `wallet:transactions:send`
4. Copy Project ID and API keys to `.env`

See [COINBASE-INTEGRATION-GUIDE.md](../COINBASE-INTEGRATION-GUIDE.md) for detailed steps.

## 5. Get Test ETH

Visit the BASE Sepolia faucet:
https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet

Request 0.1 ETH to your deployer wallet.

## 6. Compile and Deploy Contracts

```bash
# Compile
npx hardhat compile

# Deploy to testnet
npx hardhat run scripts/deploy-genesis-phase1.js --network baseSepolia

# Verify on Basescan
npx hardhat verify --network baseSepolia <CONTRACT_ADDRESS>
```

### Contract Architecture Note

Three prediction market contracts are available:

| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | **Recommended** |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |
| EnhancedPredictionMarket | `0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c` | Requires governance |

**Use PredictionMarketV2 for all new development.** It includes:
- Complete market lifecycle (create -> submit -> resolve -> claim)
- On-chain Levenshtein distance for winner determination
- 7% platform fee with pull-based collection

V1 is deprecated (no resolution mechanism). EnhancedPredictionMarket requires governance bootstrap.

## 7. Run the Application

### Start Redis
```bash
redis-server
```

### Start Flask Backend
```bash
python main.py
```

### Start Celery Worker (for background tasks)
```bash
celery -A app.celery worker --loglevel=info
```

### Access the Application
Open http://localhost:5000 in your browser.

## 8. Run Tests

### Quick Start

```bash
# Run all tests (recommended)
make test-all

# Or run separately
make test-unit       # Python unit tests
make test-contracts  # Smart contract tests
```

### Python Tests

Tests are organized in `tests/` directory:

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests (no server required)
│   ├── test_embedded_wallet.py
│   ├── test_firebase_auth.py
│   └── test_text_analysis.py
├── integration/         # Integration tests (require server)
│   ├── test_api_chain.py
│   └── test_wallet_auth.py
└── e2e/                 # End-to-end tests
```

**Available Commands:**

```bash
# All Python tests
make test

# Unit tests only (fast, no server needed)
make test-unit

# Integration tests (requires running server)
make test-integration

# With coverage report
make test-cov

# Quick check (stops on first failure)
make test-fast
```

**Direct pytest usage:**

```bash
# Run specific test file
pytest tests/unit/test_embedded_wallet.py -v

# Run tests matching pattern
pytest -k "wallet" -v

# Run with markers
pytest -m unit -v
pytest -m integration -v
```

### Smart Contract Tests

```bash
# All contract tests
make test-contracts

# Specific contract tests
make test-market    # PredictionMarket tests
make test-genesis   # GenesisNFT tests
make test-payout    # DistributedPayoutManager tests

# With gas reporting
npx hardhat test --gas-reporter
```

### Test Coverage

```bash
# Python coverage
make test-cov
# Report at: htmlcov/index.html

# Solidity coverage
npx hardhat coverage
# Report at: coverage/index.html
```

### Current Test Status

| Suite | Tests | Status |
|-------|-------|--------|
| Python Unit | 135 | Passing |
| Smart Contracts | 109 | Passing |
| Integration | 15 | Passing (2 expected skips) |
| **Total** | **259** | **All passing** |

### Running Integration Tests

Integration tests require a running Flask server:

```bash
# Terminal 1: Start the server
source .venv/bin/activate
python main.py

# Terminal 2: Run integration tests
source .venv/bin/activate
export TEST_BASE_URL=http://127.0.0.1:5000
pytest tests/integration/ -v
```

## Troubleshooting

### "Insufficient funds"
Get more test ETH from the faucet.

### "Transaction failed"
- Check gas limits in hardhat.config.js
- Verify RPC endpoint is responding
- Ensure wallet has enough ETH

### "Firebase auth not working"
- Verify authorized domains include your URL
- Check API key restrictions in Google Cloud Console

### "Redis connection refused"
Ensure Redis server is running:
```bash
redis-cli ping
```

## Seed Example Markets

The `scripts/seed_examples.py` script creates 6 worked-example markets on BASE Sepolia that demonstrate the full spectrum of prediction quality.

```bash
# Preview what will be created (no transactions sent)
python scripts/seed_examples.py --dry-run

# Create markets + submissions (requires funded wallets)
python scripts/seed_examples.py

# Resolve markets after they end (requires OWNER_PRIVATE_KEY)
python scripts/seed_examples.py --resolve
```

**Required env vars:** `OWNER_PRIVATE_KEY`, `TEST_WALLET_KEY_1` through `TEST_WALLET_KEY_4`, and optionally `BASE_SEPOLIA_RPC_URL`.

See the README "Worked Examples" section for details on each example market.

## Production Deployment

For mainnet deployment:

1. Change `NETWORK=base-mainnet` and `CHAIN_ID=8453`
2. Use production RPC endpoints (Alchemy, QuickNode)
3. Use hardware wallet for deployer
4. Complete security audit first
5. Set up monitoring and alerts
