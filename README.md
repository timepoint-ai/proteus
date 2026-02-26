# Proteus

**v0 Alpha -- Proof of Concept | BASE Sepolia Testnet**

A prediction market protocol on BASE where users stake ETH on the exact text a public figure will post. Winners are determined by on-chain Levenshtein distance. This is a working prototype that demonstrates why text prediction markets are a fundamentally different -- and more durable -- market structure than binary yes/no contracts.

> **Status:** Alpha prototype on BASE Sepolia testnet. Not audited. Not production-ready. Do not deploy to mainnet.

tl;dr

Research project, not intended for commercial use, exploring how AIs can roleplay as public figures and bet on the *exact* words they will use on posts on X. "I bet 1 ETH that @elonmusk will post 'Mars by 2030' on X between Mar 1 2026 and Apr 1 2026." and then if the real post is "Moon base by 2030" the Levenshtein distance between the real text posted (or lack thereof) is calculated among all competitors and the closest to the exact character-by-character post within the time period wins.


## The Thesis

Binary prediction markets encode exactly one bit of information per contract. The outcome space is {0, 1}, and as AI systems approach superhuman forecasting along an exponential capability curve, the edge any participant can capture in a binary market collapses toward zero because the correct answer becomes trivially computable. Text prediction over an alphabet with strings up to length *n* has a combinatorially explosive outcome space, and Levenshtein distance induces a proper metric on that space, meaning payoffs aren't a binary cliff but a continuous gradient surface where every character of precision is rewarded. Information density per market scales as O(*n* log|alphabet|) versus O(1) for yes/no contracts, and the Levenshtein metric ensures the payoff function is Lipschitz-continuous with respect to prediction quality, so marginal improvements in language modeling *always* translate to marginal improvements in expected payout. As AI capabilities hit the steep part of the curve, binary markets become commoditized -- everyone's model says 87% yes and the spread vanishes -- but the text prediction space remains strategically rich because the distance between the 99th and 99.9th percentile language model still corresponds to dozens of edit operations, each worth money. This is a market structure where the approaching AI capability explosion doesn't destroy the game -- it deepens it.

Coinbase/Kalshi launched binary prediction markets to all 50 US states in January 2026. They run off-chain through Kalshi's CFTC-regulated backend. Polymarket does ~$12B/month in binary yes/no volume on Polygon. Neither supports text prediction. Neither scores on a continuous distance metric. That's the gap this prototype explores.

> **X API Update (Feb 2026):** X now offers [pay-per-use API access](https://developer.x.com/) for individual developers -- no subscriptions, no monthly caps, just credit-based billing. This is a significant unlock for oracle resolution: each oracle node can independently fetch posts by ID, verify authorship, and confirm timestamps via the X API v2. Previously, the $200/mo Basic tier (15K reads) or $5,000/mo Pro tier (1M reads) made multi-oracle verification cost-prohibitive. Pay-per-use makes it feasible for multiple independent oracles to verify the same post at minimal cost.

## What This Is (and Isn't)

**This is a v0 alpha.** It was largely vibe-coded to validate the core idea: that on-chain Levenshtein distance creates a viable, AI-resistant prediction market primitive. The smart contracts work. The market lifecycle works. The math works. Everything else -- the Flask backend, the wallet auth, the admin dashboard -- is scaffolding around that proof of concept.

**Do not deploy this to mainnet.** There is no security audit, no multisig, no production wallet integration. The embedded wallet service uses a PBKDF2 shim. The resolution mechanism is centralized (single EOA). These are known, accepted tradeoffs for a prototype. This is not meant for commercial use, whatsoever. 

### What works (BASE Sepolia testnet)

- Full market lifecycle: create -> submit predictions -> resolve -> claim payouts
- On-chain Levenshtein distance for winner determination (PredictionMarketV2)
- 259+ passing tests (109 contract, 135 unit, 15 integration)
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
Market: "What will @elonmusk post?"
             |
             v
    Competitors submit predictions + stake ETH
    ┌────────────────────────────────────────────────────┐
    │ AI (Claude):  "Starship flight 2 confirmed for     │
    │               March. Humanity becomes               │
    │               multiplanetary or dies trying."       │
    │ Human fan:    "The future of humanity is Mars       │
    │               and beyond"                           │
    │ Random bot:   "a8j3kd9xmz pqlw7 MARS ufk2         │
    │               rocket lol"                           │
    └────────────────────────────────────────────────────┘
             |
             v
    Market ends. Oracle submits actual text:
    "Starship flight 2 is GO for March. Humanity
     becomes multiplanetary or we die trying."
             |
             v
    On-chain Levenshtein distance:
      AI (Claude) → 12 edits   ← WINNER
      Human fan   → 59 edits
      Random bot  → 72 edits
             |
             v
    AI (Claude) wins the pool (minus 7% platform fee)
```

The scoring is continuous, not binary. Every character of precision is rewarded. The closest match wins.

## Worked Examples

Six scenarios showing the full spectrum of prediction quality in a Levenshtein-scored market. Each demonstrates a different strategic insight.

<details>
<summary><strong>Example 1: AI Roleplay Wins (Elon Musk)</strong></summary>

**Market**: What will `@elonmusk` post?

**Actual text**: `Starship flight 2 is GO for March. Humanity becomes multiplanetary or we die trying.`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| AI Roleplay (Claude) | `Starship flight 2 confirmed for March. Humanity becomes multiplanetary or dies trying.` | **12** |
| Human fan | `The future of humanity is Mars and beyond` | 59 |
| AI (lazy prompt GPT) | `Elon will probably tweet about SpaceX rockets going to space soon` | 66 |
| Bot (entropy) | `a8j3kd9xmz pqlw7 MARS ufk2 rocket lol` | 72 |

**Winner**: AI Roleplay (Claude) at distance 12.

**Lesson**: A well-prompted AI captures tone, structure, and vocabulary. The 47-edit gap between the AI roleplay and the human fan is monetizable -- that's the entire pool. The human got the theme right ("Mars") but theme doesn't pay; exact wording does.

</details>

<details>
<summary><strong>Example 2: Human Insider Beats AI (Sam Altman)</strong></summary>

**Market**: What will `@sama` post?

**Actual text**: `we are now confident AGI is achievable with current techniques. announcement soon.`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| Ex-OpenAI engineer | `we are now confident AGI is achievable with current techniques. big announcement soon.` | **4** |
| AI Roleplay (GPT) | `we now believe AGI is achievable with current techniques. announcement coming soon.` | 18 |
| Human (cynical) | `Sam will say AGI is close again like he always does nothing new` | 59 |

**Winner**: Ex-OpenAI engineer at distance 4.

**Lesson**: Insider information beats AI. Someone who heard rehearsed phrasing gets within 4 edits. The AI roleplay is good (distance 18) but the insider's edge -- knowing the exact phrase "we are now confident" -- is worth 14 edits of advantage. Information asymmetry is priced continuously.

</details>

<details>
<summary><strong>Example 3: Insider Leaks Exact Wording (Zuckerberg)</strong></summary>

**Market**: What will `@zuck` post?

**Actual text**: `Introducing Meta Ray-Ban with live AI translation. 12 languages. The future is on your face.`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| Meta intern | `Introducing Meta Ray-Ban with live AI translation in 12 languages. The future is on your face.` | **3** |
| AI Roleplay | `Introducing Meta Ray-Ban AI glasses with real-time translation in 8 languages. The future is on your face.` | 25 |
| Human (guessing) | `zuck will announce glasses or something idk` | 73 |
| Spam bot | `BUY META NOW GLASSES MOONSHOT 1000X GUARANTEED` | 83 |

**Winner**: Meta intern at distance 3.

**Lesson**: Product launches have rehearsed copy. Seeing a draft deck = 22-edit advantage over the best AI. The AI gets the structure right ("Introducing Meta Ray-Ban... The future is on your face.") but misses the specific product name and number. Insider access to marketing materials is worth money in this market.

</details>

<details>
<summary><strong>Example 4: Null Submission Wins (Jensen Huang Stays Silent)</strong></summary>

**Market**: What will `@JensenHuang` post?

**Actual text**: *(nothing posted)* -- resolved with `__NULL__`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| Null trader | `__NULL__` | **0** |
| Human (guessing) | `Jensen will flex about Blackwell sales numbers` | 46 |
| AI Roleplay | `NVIDIA Blackwell Ultra is sampling ahead of schedule. The next era of computing starts now.` | 90 |

**Winner**: Null trader at distance 0 (exact match).

**Lesson**: Binary markets can't express "person won't post." AI roleplay *always* generates text -- it can't predict silence. The `__NULL__` sentinel lets traders bet on inaction, and distance 0 means they take the entire pool. This is a market primitive that doesn't exist in yes/no contracts.

</details>

<details>
<summary><strong>Example 5: AI vs AI Race -- THE THESIS EXAMPLE (Satya Nadella)</strong></summary>

**Market**: What will `@sataborasu` post?

**Actual text**: `Copilot is now generating 46% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| Claude roleplay | `Copilot is now generating 45% of all new code at GitHub-connected enterprises. The AI transformation of software is just beginning.` | **1** |
| GPT roleplay | `Copilot is now generating 43% of all new code at GitHub-connected enterprises. The AI transformation of software has just begun.` | 8 |
| Human (vague) | `Microsoft AI is great and will change the world of coding forever` | 101 |

**Winner**: Claude roleplay at distance 1 (single character: `5` → `6`).

**Lesson**: This is the thesis example. Two frontier AI models, same public training corpus, same prompt. Claude gets within 1 edit. GPT gets within 8. The 7-edit gap between two frontier models is worth the entire pool. A binary market would split nothing -- both AIs "predicted correctly" in a yes/no framing. Levenshtein rewards marginal calibration. The game deepens as models improve.

</details>

<details>
<summary><strong>Example 6: Bot Entropy Wastes Money (Tim Cook)</strong></summary>

**Market**: What will `@tim_cook` post?

**Actual text**: `Apple Intelligence is now available in 30 countries. Privacy and AI, together.`

| Submitter | Prediction | Distance |
|-----------|-----------|----------|
| AI Roleplay | `Apple Intelligence is now available in 24 countries. We believe privacy and AI go hand in hand.` | **28** |
| Human (thematic) | `Tim will say something about privacy and AI like always` | 53 |
| Random bot | `x7g APPLE j2m PHONE kq9 BUY zw3 intelligence p5 cook` | 65 |
| Degenerate bot | `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` | 73 |

**Winner**: AI Roleplay at distance 28.

**Lesson**: Levenshtein distance is a natural anti-bot mechanism. Random strings have expected distance ≈ max(len(a), len(b)). Bots can't get lucky -- in a character-level outcome space, there's no shortcut. Even the degenerate "aaaa..." bot that tries to game string length scores worse than a thematic human guess. The metric itself is the spam filter.

</details>

## Deployed Contracts (BASE Sepolia)

| Contract | Address | Status |
|----------|---------|--------|
| **PredictionMarketV2** | `0x5174Da96BCA87c78591038DEe9DB1811288c9286` | Active |
| GenesisNFT | `0x1A5D4475881B93e876251303757E60E524286A24` | 60/100 minted |
| PredictionMarket (V1) | `0x667121e8f22570F2c521454D93D6A87e44488d93` | Deprecated |

Use **PredictionMarketV2** for everything. V1 lacks a resolution mechanism.

## Deployment

The backend runs on **Railway** at `proteus-production-6213.up.railway.app`, auto-deploying from `main`.

| Service | Provider | Purpose |
|---------|----------|---------|
| Backend (gunicorn + Flask) | Railway | API, admin dashboard, marketing pages |
| Redis | Railway | Caching, Celery broker, auth stores |
| Postgres | Railway | Available but unused (chain-only mode) |
| Smart contracts | BASE Sepolia | All market data on-chain |

### Local Development

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

# Start the app locally
redis-server &
python main.py            # http://localhost:5000
```

You'll need BASE Sepolia ETH from the [faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet).

## Project Structure

```
contracts/src/     # Solidity smart contracts (the core primitive)
contracts/test/    # Hardhat tests
services/          # Python backend services (prototype scaffolding)
routes/            # Flask API endpoints
scripts/           # Deployment, seeding, and utility scripts
static/js/         # Frontend JavaScript
templates/         # HTML templates (marketing, app, admin)
tests/             # Python tests (unit, integration, load)
docs/              # Documentation
railway.json       # Railway start command config
```

## Architecture

```
Frontend (Web3.js, wallet connect)
    |  JWT Auth
Flask Backend (gunicorn, Railway)
    |  Web3.py          |  Redis
BASE Sepolia            Cache, Celery, Auth
(PredictionMarketV2,    (nonces, OTPs,
 GenesisNFT, + 12)      rate limiting)
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
- **Backend**: Python 3.11+, Flask, gunicorn, Web3.py, Celery, Redis
- **Auth**: JWT (MetaMask) + Firebase email OTP (Coinbase Embedded Wallet shim)
- **Infra**: Railway (auto-deploy from GitHub)

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design and contract stack
- [Setup Guide](docs/SETUP.md) - Development environment
- [API Reference](docs/API_DOCUMENTATION.md) - REST API endpoints
- [Contracts](docs/CONTRACTS.md) - Smart contract reference
- [Roadmap](docs/ROADMAP.md) - What's done, what's next
- [Gap Analysis](docs/GAPS.md) - Honest accounting of remaining work
- [Security Analysis](docs/SECURITY-ANALYSIS.md) - Slither static analysis results
- [Audit Preparation](docs/AUDIT-PREPARATION.md) - Contract inventory for future audit
- [Whitepaper](WHITEPAPER.md) - Full research paper

## What Would Make This Real

In rough priority order:

1. **Validate demand** -- Do people actually want to bet on exact tweet text? Ship the testnet demo and find out.
2. **Security audit** -- The ~1,025 lines of in-scope Solidity need a real audit before touching mainnet.
3. **Decentralize resolution** -- Replace single-EOA resolution with oracle consensus (commit-reveal). X API pay-per-use access now makes multi-oracle tweet verification economically viable.
4. **Real wallet integration** -- Replace PBKDF2 shim with Coinbase CDP Server Signer.
5. **Multisig** -- Gnosis Safe 2-of-3 for contract owner key.
6. **Production RPC** -- Alchemy/QuickNode for mainnet (public RPC is fine for Sepolia testnet).

## TIMEPOINT Suite

Proteus is part of the TIMEPOINT platform suite. It operates as a standalone prediction market system, but connects to the broader TIMEPOINT ecosystem:

| Project | Repository | Role |
|---------|-----------|------|
| **Proteus Markets** | [realityinspector/proteus-markets](https://github.com/realityinspector/proteus-markets) | Prediction markets on temporal simulation outcomes (this repo) |
| Flash API | timepoint-flash-deploy | Unified API gateway -- auth, credits, generation, billing + clockchain proxy |
| Pro / Oxen | timepoint-pro | Temporal social physics engine -- 21 mechanisms, persistent agent memory, SNAG |
| Clockchain | timepoint-clockchain | Spatiotemporal graph index -- NetworkX graph, canonical URLs, autonomous workers |
| Billing | timepoint-billing | Stripe + Apple IAP, subscriptions, refunds, disputes |
| SNAG Bench | timepoint-snag-bench | Scoring framework for temporal AI -- grounding, coherence, prediction |
| Landing | timepoint-landing | Marketing site at `timepointai.com`, links to the [Proteus whitepaper](https://github.com/realityinspector/proteus-markets/blob/main/WHITEPAPER.md) |
| Web App | timepoint-web-app | Web frontend at `app.timepointai.com` (FastAPI + Jinja2 + HTMX) |
| iPhone App | timepoint-iphone-app | Native iOS client (SwiftUI, v1.0.0 build 2, TestFlight-ready) |

Proteus is the only public repository in the suite. The other projects are internal to the TIMEPOINT organization.

## License

MIT
