# Clockchain

**v0 Alpha -- Proof of Concept**

A prediction market protocol on BASE where users stake ETH on the exact text a public figure will post. Winners are determined by on-chain Levenshtein distance. This is a working prototype that demonstrates why text prediction markets are a fundamentally different -- and more durable -- market structure than binary yes/no contracts.

## The Thesis

Binary prediction markets encode exactly one bit of information per contract. The outcome space is {0, 1}, and as AI systems approach superhuman forecasting along an exponential capability curve, the edge any participant can capture in a binary market collapses toward zero because the correct answer becomes trivially computable. Text prediction over an alphabet with strings up to length *n* has a combinatorially explosive outcome space, and Levenshtein distance induces a proper metric on that space, meaning payoffs aren't a binary cliff but a continuous gradient surface where every character of precision is rewarded. Information density per market scales as O(*n* log|alphabet|) versus O(1) for yes/no contracts, and the Levenshtein metric ensures the payoff function is Lipschitz-continuous with respect to prediction quality, so marginal improvements in language modeling *always* translate to marginal improvements in expected payout. As AI capabilities hit the steep part of the curve, binary markets become commoditized -- everyone's model says 87% yes and the spread vanishes -- but the text prediction space remains strategically rich because the distance between the 99th and 99.9th percentile language model still corresponds to dozens of edit operations, each worth money. This is a market structure where the approaching AI capability explosion doesn't destroy the game -- it deepens it.

Coinbase/Kalshi launched binary prediction markets to all 50 US states in January 2026. They run off-chain through Kalshi's CFTC-regulated backend. Polymarket does ~$12B/month in binary yes/no volume on Polygon. Neither supports text prediction. Neither scores on a continuous distance metric. That's the gap this prototype explores.

## What This Is (and Isn't)

**This is a v0 alpha.** It was largely vibe-coded to validate the core idea: that on-chain Levenshtein distance creates a viable, AI-resistant prediction market primitive. The smart contracts work. The market lifecycle works. The math works. Everything else -- the Flask backend, the wallet auth, the admin dashboard -- is scaffolding around that proof of concept.

**Do not deploy this to mainnet.** There is no security audit, no multisig, no production wallet integration. The embedded wallet service uses a PBKDF2 shim. The resolution mechanism is centralized (single EOA). These are known, accepted tradeoffs for a prototype.

### What works (BASE Sepolia testnet)

- Full market lifecycle: create -> submit predictions -> resolve -> claim payouts
- On-chain Levenshtein distance for winner determination (PredictionMarketV2)
- 250+ passing tests (109 contract, 125 unit, 15 integration)
- Genesis NFT (60/100 minted, finalized) with on-chain SVG art
- JWT wallet auth (MetaMask) + email OTP (Coinbase Embedded Wallet shim)
- Admin resolution dashboard, Redis caching, rate limiting, structured logging
- CI/CD pipeline, Slither static analysis complete

### What's intentionally not done

- External security audit
- Real Coinbase CDP wallet integration (no credentials)
- Multisig for contract owner key
- Production RPC (Alchemy/QuickNode)
- Production monitoring (Sentry)
- Decentralized oracle resolution

## How It Works

```
User predicts: "I think @elonmusk will tweet exactly: 'Mars by 2030'"
          |
          v
    ETH staked on-chain (PredictionMarketV2)
          |
          v
    Market ends, oracle fetches actual tweet text
          |
          v
    On-chain Levenshtein distance: edit_distance(prediction, actual)
          |
          v
    Closest prediction wins the pool (minus 7% platform fee)
```

The scoring is continuous, not binary. A prediction of "Mars by 2030" vs actual "Mars by 2031" is a distance of 1. A prediction of "Moon by 2025" vs actual "Mars by 2031" is much larger. The closest match wins.

## Deployed Contracts (BASE Sepolia)

| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | Active |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | 60/100 minted |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |

Use **PredictionMarketV2** for everything. V1 lacks a resolution mechanism.

## Quick Start

```bash
# Install dependencies
npm install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"

# Run tests
make test-all             # Everything
make test-unit            # Python unit tests
make test-contracts       # Solidity tests (Hardhat)

# Start the app (testnet only)
redis-server &
python main.py
```

You'll need BASE Sepolia ETH from the [faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet).

## Project Structure

```
contracts/src/     # Solidity smart contracts (the core primitive)
contracts/test/    # Hardhat tests
services/          # Python backend services (prototype scaffolding)
routes/            # Flask API endpoints
static/js/         # Frontend JavaScript
templates/         # HTML templates
tests/             # Python tests (unit, integration, load)
docs/              # Documentation
```

## Architecture

```
Frontend (Web3.js, wallet connect)
    |  JWT Auth
Flask Backend (routes/, services/)
    |  Web3.py
BASE Sepolia (PredictionMarketV2, GenesisNFT, + 12 others)
```

All market data lives on-chain. Zero database. Redis is used only for caching RPC responses, auth nonces/OTPs, and rate limiting.

## Fee Structure

7% platform fee on market volume, split:

| Recipient | Share |
|-----------|-------|
| Genesis NFT Holders | 20% (1.4% of volume) |
| Oracles | 28.6% (2%) |
| Market Creators | 14.3% (1%) |
| Node Operators | 14.3% (1%) |
| Builder Pool | 28.6% (2%) |

## Technology

- **Blockchain**: BASE (Coinbase L2, OP Stack)
- **Contracts**: Solidity 0.8.20, OpenZeppelin, Hardhat
- **Backend**: Flask, Web3.py, Celery, Redis
- **Auth**: JWT (MetaMask) + Firebase email OTP (Coinbase Embedded Wallet shim)

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and contract stack
- [Setup Guide](docs/SETUP.md) - Development environment
- [Roadmap](docs/ROADMAP.md) - What's done, what's next
- [Gap Analysis](docs/GAPS.md) - Honest accounting of remaining work
- [Security Analysis](docs/SECURITY-ANALYSIS.md) - Slither static analysis results
- [Audit Preparation](docs/AUDIT-PREPARATION.md) - Contract inventory for future audit

## What Would Make This Real

In rough priority order:

1. **Validate demand** -- Do people actually want to bet on exact tweet text? Ship the testnet demo and find out.
2. **Security audit** -- The ~1,025 lines of in-scope Solidity need a real audit before touching mainnet.
3. **Decentralize resolution** -- Replace single-EOA resolution with oracle consensus (commit-reveal).
4. **Real wallet integration** -- Replace PBKDF2 shim with Coinbase CDP Server Signer.
5. **Multisig** -- Gnosis Safe 2-of-3 for contract owner key.
6. **Production infra** -- Alchemy/QuickNode RPC, Sentry monitoring, proper deployment pipeline.

## License

MIT
