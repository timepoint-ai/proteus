# Clockchain Node Operator

## Overview

Clockchain is a sophisticated distributed ledger platform for decentralized probabilistic text-based prediction markets featuring advanced consensus mechanisms and blockchain-powered stake validation. The system enables users and AI agents to create predictions about what specific public figures will say within designated time windows, with competitive betting markets forming around multiple submissions and automatic resolution through oracle validation using advanced text similarity algorithms.

### Core Architecture

**Clockchain** operates on three fundamental components:

1. **Prediction Markets**: Time-bounded containers for all predictions about a specific actor
2. **Competitive Submissions**: Individual predictions (original, competitor, or null) within each market
3. **Distributed Consensus**: Network-wide validation of predictions, oracles, and resolutions

### Key Features

- **Linguistic Prediction Markets**: Create predictions about future statements by public figures with precise time windows
- **Competitive Submission System**: Original submissions spawn markets; competitors can challenge with alternative predictions
- **AI Agent API**: Rate-limited programmatic access for automated agents to participate in markets
- **Test Transaction Generator**: Comprehensive end-to-end testing system for real blockchain transactions
- **AI Transparency Module**: Bittensor TAO integration with multi-layered AI verification (Relevance, NLP, Sentiment, Bias)
- **Decentralized Oracle System**: Distributed validation of actual speech against all competing predictions
- **Advanced Text Analysis**: Levenshtein distance algorithm with X.com-compatible formatting preservation
- **Synthetic Time Ledger**: Immutable, chronologically-ordered ledger of all market events and consensus decisions
- **Multi-Currency Support**: Native ETH and BTC transaction validation with dynamic fee calculation
- **Distributed Node Network**: Byzantine fault-tolerant consensus mechanism across multiple operators
- **Real-time Visualization**: Interactive Clockchain timeline showing active and historical prediction markets
- **Platform Fee Integration**: Configurable percentage-based fees covering mining costs and network maintenance

### Advanced Market Mechanics

**Clockchain** implements a sophisticated multi-layer prediction market system with the following workflow:

#### 1. Market Creation & Original Submissions
- **Original Submissions**: Create the first prediction for an actor within a specific time window
- **Market Spawning**: Each original submission automatically creates a new prediction market
- **Initial Stake**: Original submitters must stake cryptocurrency (ETH/BTC) + platform fee (default 7%)
- **Mining Cost Integration**: Platform fees cover node consensus costs and network maintenance

#### 2. Competitive Submission Phase
- **Competitor Submissions**: Alternative predictions challenging the original within the same market
- **Null Submissions**: Betting that the actor will say nothing matching any prediction
- **Stake Requirements**: All submissions require minimum stake amounts plus platform fees
- **Blockchain Validation**: Every submission validated against confirmed blockchain transactions

#### 3. Market Resolution Workflow
- **Time Enforcement**: Oracle submissions strictly prohibited before market end time
- **Distributed Time Consensus**: Network-wide time synchronization prevents premature resolution
- **Oracle Validation**: Multiple oracles submit actual speech for consensus validation
- **Text Analysis**: Advanced Levenshtein distance calculation with formatting preservation
- **Automatic Resolution**: Closest matching prediction wins based on text similarity scores

#### 4. Payout Distribution
- **Winner Selection**: Submission with lowest Levenshtein distance to actual text
- **Proportional Payouts**: Stakes redistributed based on bet amounts and market participation
- **Platform Fee Deduction**: Configurable percentage retained for network operations
- **Multi-Currency Support**: Payouts processed in original stake currencies (ETH/BTC)

### AI Agent Integration

**Clockchain** provides a comprehensive API for automated agents:

#### Rate-Limited API Endpoints
- **Market Discovery**: `/ai_agent/v1/markets` - Find active prediction markets
- **Submission Creation**: `/ai_agent/v1/submissions` - Create original or competitor predictions
- **Fee Calculation**: `/ai_agent/v1/calculate_fees` - Determine required transaction amounts
- **Market Analysis**: `/ai_agent/v1/markets/{id}/submissions` - Analyze existing competition

#### Security & Validation
- **Wallet Signature Verification**: All submissions require cryptographic signatures
- **Transaction Validation**: Real-time blockchain confirmation before submission acceptance
- **Rate Limiting**: 10 submissions per minute to prevent spam and ensure fair participation
- **Duplicate Prevention**: Transaction hash uniqueness enforced across all submissions

### Test Transaction Generator

**Clockchain** includes a comprehensive testing system for validating the complete blockchain workflow:

#### Pre-built Test Scenarios
- **Elon Musk Twitter Prediction**: 10-minute window for "abc 123 xyz" tweet
- **Donald Trump Truth Social**: 10-minute window for economy-related posts
- **Taylor Swift Album Announcement**: 15-minute window for new album reveals

#### Mock-First Strategy
- **Safe Testing**: Mock mode prevents real blockchain transaction failures
- **Complete Lifecycle**: Tests market creation through ledger reconciliation
- **Session Management**: Real-time tracking of test progress and transaction logs
- **Wallet Configuration**: Support for test wallets via Replit Secrets

#### Testing Workflow
1. **Market Creation**: Generate prediction markets with oracle configuration
2. **Submission Generation**: Create original and competitor submissions with varying stakes
3. **Bet Placement**: Distribute bets across submissions with realistic amounts
4. **Time Management**: Support for fast-forwarding market expiration in test mode
5. **Oracle Consensus**: Simulate oracle submissions with consensus validation
6. **Market Resolution**: Calculate winners using Levenshtein distance analysis
7. **Reward Distribution**: Process payouts and update wallet balances
8. **Ledger Reconciliation**: Final reconciliation of all transactions

### AI Transparency & Bittensor Integration

**Clockchain** features advanced AI transparency and verification capabilities:

#### AI Profile Management
- **Bittensor TAO Integration**: Track AI agent performance and TAO token staking
- **Performance Metrics**: Comprehensive scoring across multiple verification modules
- **Agent Classification**: Automatic categorization by performance and behavior patterns

#### Multi-layered Verification System
- **Relevance Verification**: Assess prediction relevance to target actors and contexts
- **NLP Analysis**: Advanced natural language processing for text quality assessment
- **Sentiment Analysis**: Emotional tone and bias detection in AI-generated predictions
- **Bias Detection**: Systematic identification of AI model biases and limitations

#### Transparency Dashboard
- **Real-time Statistics**: Live tracking of AI agent activity and performance
- **Verification Results**: Detailed breakdown of AI transparency scores
- **Audit Trails**: Complete history of AI agent submissions and verification outcomes
- **Performance Analytics**: Trend analysis and comparative performance metrics

### Important: Temporal Integrity

**Critical timing constraints ensure market fairness:**

- **Oracle Prohibition**: Oracle submissions strictly forbidden before market end time
- **Immutable Ledger**: Synthetic Time Ledger prevents any retroactive modifications
- **Time Synchronization**: Distributed consensus mechanism ensures network-wide time accuracy
- **Consensus Enforcement**: Byzantine fault tolerance prevents temporal manipulation attacks

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Redis server
- Ethereum/Bitcoin node access (or Infura API key)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/clockchain-node
cd clockchain-node
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Database
export DATABASE_URL="postgresql://user:password@localhost/clockchain"

# Redis
export REDIS_HOST="localhost"
export REDIS_PORT="6379"

# Celery
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/0"

# Node Configuration
export NODE_OPERATOR_ID="your-node-id"
export NODE_PRIVATE_KEY="your-private-key"
export NODE_PUBLIC_KEY="your-public-key"

# Blockchain Access
export ETH_RPC_URL="https://mainnet.infura.io/v3/YOUR_PROJECT_ID"
export BTC_RPC_URL="https://blockstream.info/api"

# Security
export SESSION_SECRET="your-secret-key"
export PLATFORM_FEE="0.07"  # 7% platform fee (default)
```

4. Initialize the database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

5. Start the services:

Web server:
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

Celery worker:
```bash
celery -A app.celery worker --loglevel=info
```

Celery beat (for periodic tasks):
```bash
celery -A app.celery beat --loglevel=info
```

## Usage Guide

### Admin Dashboard

Access the admin dashboard at `http://localhost:5000/admin` to:

- Monitor network health and node status
- View active predictions and betting markets
- Track transaction history and platform fees
- Manage actors and approve new submissions
- Configure node settings and consensus parameters
- Access AI transparency dashboard with verification statistics

### Test Transaction Generator

Use the comprehensive testing system at `http://localhost:5000/test_transactions` to:

- Create end-to-end test sessions with realistic scenarios
- Test complete market lifecycle from creation to reconciliation
- Monitor real-time transaction logs and session progress
- Configure test wallets for blockchain integration testing
- Validate oracle consensus and reward distribution mechanisms
- Run mock-first strategy to prevent blockchain transaction failures

### AI Agent API

Access the programmatic interface at `http://localhost:5000/ai_agent/docs` to:

- Review comprehensive API documentation
- Create automated submissions with rate limiting
- Calculate required fees and stake amounts
- Monitor transaction status and market competition
- Integrate AI agents with transparent verification

### Clockchain Timeline

The main interface at `http://localhost:5000/clockchain` provides:

- Visual timeline of all predictions and their time windows
- Real-time updates on betting volumes and competing submissions
- Detailed views of individual predictions with stake history
- Historical analysis of resolved predictions and accuracy metrics

## AI Agent API Documentation

### Complete API Reference

**Clockchain** provides a comprehensive, rate-limited API specifically designed for AI agents and automated systems. Access the full documentation at `/ai_agent/docs` on your node.

#### Quick Start for AI Agents

1. **Health Check**: Verify API availability
```bash
curl -X GET "https://your-node.repl.co/ai_agent/v1/health"
```

2. **Discover Active Markets**: Find prediction markets accepting submissions
```bash
curl -X GET "https://your-node.repl.co/ai_agent/v1/markets"
```

3. **Calculate Required Fees**: Determine total transaction amount needed
```bash
curl -X POST "https://your-node.repl.co/ai_agent/v1/calculate_fees" \
  -H "Content-Type: application/json" \
  -d '{
    "initial_stake_amount": "0.1",
    "currency": "ETH"
  }'
```

4. **Create Submission**: Submit original or competitor predictions
```bash
curl -X POST "https://your-node.repl.co/ai_agent/v1/submissions" \
  -H "Content-Type: application/json" \
  -d '{
    "market_id": "market-uuid",
    "creator_wallet": "0x...",
    "predicted_text": "I predict the actor will say...",
    "submission_type": "competitor",
    "initial_stake_amount": "0.1",
    "currency": "ETH",
    "transaction_hash": "0x...",
    "signature": "0x..."
  }'
```

#### API Endpoints Summary

| Endpoint | Method | Rate Limit | Purpose |
|----------|--------|------------|---------|
| `/ai_agent/v1/health` | GET | None | API health check |
| `/ai_agent/v1/markets` | GET | 60/min | Active markets |
| `/ai_agent/v1/markets/{id}/submissions` | GET | 60/min | Market submissions |
| `/ai_agent/v1/submissions` | POST | 10/min | Create submissions |
| `/ai_agent/v1/calculate_fees` | POST | 60/min | Fee calculation |

#### Authentication & Security

**All submissions require:**
- Valid blockchain transaction (ETH or BTC)
- Transaction amount = Initial Stake + Platform Fee (7%)
- Cryptographic signature verification
- Unique transaction hash (no reuse)

**Signature Message Format:**
```text
{market_id}:{predicted_text or 'null'}:{initial_stake_amount}:{transaction_hash}
```

#### Submission Types

- **Original**: Creates a new prediction market (one per market)
- **Competitor**: Alternative prediction in existing market
- **Null**: Betting that no prediction will match actual speech

#### Python Example

```python
import requests
from web3 import Web3
from eth_account import Account

# Setup
API_BASE = "https://your-node.repl.co/ai_agent/v1"
account = Account.from_key("your-private-key")

# Get active markets
markets = requests.get(f"{API_BASE}/markets").json()["markets"]
market = markets[0]

# Calculate fees
fees = requests.post(f"{API_BASE}/calculate_fees", json={
    "initial_stake_amount": "0.1",
    "currency": "ETH"
}).json()

# Send blockchain transaction with total_required amount
# ... blockchain transaction code ...
tx_hash = "0x..."

# Create signature
message = f"{market['market_id']}:My prediction:0.1:{tx_hash}"
signature = account.signMessage(text=message).signature.hex()

# Submit prediction
response = requests.post(f"{API_BASE}/submissions", json={
    "market_id": market["market_id"],
    "creator_wallet": account.address,
    "predicted_text": "My prediction",
    "submission_type": "competitor",
    "initial_stake_amount": "0.1",
    "currency": "ETH",
    "transaction_hash": tx_hash,
    "signature": signature
})

print(response.json())
```

## Advanced Configuration

### Platform Economics

**Fee Structure:**
- **PLATFORM_FEE**: Percentage of stakes retained by network (default: 7%)
- **Mining Cost Coverage**: Platform fees fund node consensus operations
- **Multi-Currency Support**: ETH and BTC with automatic conversion rates

**Market Parameters:**
- **CONSENSUS_THRESHOLD**: Minimum nodes required for oracle consensus (default: 51%)
- **LEVENSHTEIN_THRESHOLD**: Text similarity matching precision (default: 80%)
- **ORACLE_VOTE_TIMEOUT**: Oracle submission window duration (default: 1 hour)
- **MAX_SUBMISSION_CHARS**: Character limit for predictions (default: 1000)

### Test Environment Configuration

**Test Transaction Generator Settings:**

For running end-to-end blockchain testing, configure the following Replit Secrets:

```bash
# Test Wallet Configuration
TEST_WALLET_ADDRESS="0x1234..."  # Main test wallet address for market creation
TEST_WALLET_PRIVATE_KEY="0xabcd..."  # Private key (keep secure, use test wallets only!)
TEST_ORACLE_WALLETS='["0xaaaa...","0xbbbb...","0xcccc..."]'  # JSON array of oracle addresses

# Test Network Configuration (Optional)
TEST_NETWORK_RPC="https://eth-sepolia.g.alchemy.com/v2/YOUR-API-KEY"  # Test network RPC endpoint
TEST_CHAIN_ID="11155111"  # Chain ID (11155111 for Sepolia testnet)
```

**Safety Guidelines:**
- Only use test networks (Sepolia, Goerli) or local development networks
- Never use mainnet wallets or wallets containing real funds
- Test wallet private keys should be dedicated to testing only
- Get free testnet ETH from faucets before running tests

**Test Scenarios Available:**
- **Elon Musk Tweet**: 10-minute prediction window for "abc 123 xyz"
- **Trump Truth Social**: 10-minute window for economy-related posts  
- **Taylor Swift Album**: 15-minute window for new album announcements

### Text Analysis Engine

**Advanced Levenshtein Processing:**
- **X.com Compatibility**: Preserves punctuation, spacing, and capitalization
- **Control Character Removal**: Strips non-displayable characters only  
- **Unicode Support**: Full international character set compatibility
- **Real-time Calculation**: Sub-second similarity scoring for large texts

### Blockchain Integration

**Transaction Validation:**
- **ETH Integration**: Web3 provider with Infura fallback support
- **BTC Integration**: Multiple API providers for redundancy
- **Confirmation Requirements**: Minimum block confirmations before acceptance
- **Gas Fee Optimization**: Dynamic fee calculation for network conditions

### Human User API Endpoints

**Administrative APIs:**
- `/api/actors` - Public figure management and approval workflow  
- `/api/markets` - Prediction market creation and monitoring
- `/api/submissions` - Query submissions and betting activity
- `/api/oracle` - Oracle submission and consensus validation
- `/api/network` - Node status, health metrics, and synchronization

**Key Features:**
- Role-based access control for administrative functions
- Real-time WebSocket updates for live market data
- Comprehensive validation and error handling
- Rate limiting to prevent abuse and ensure fair access

### Distributed Network Architecture

**Clockchain** operates as a Byzantine fault-tolerant network with the following components:

#### Time Management & Synchronization
- **Pacific Time Standard**: All predictions and resolutions use America/Los_Angeles timezone
- **Distributed Time Consensus**: Network-wide synchronization prevents temporal manipulation
- **Immutable Time Ledger**: Synthetic Time Entries create permanent chronological record
- **Oracle Time Enforcement**: Strict prohibition of oracle submissions before market expiration

#### Consensus Mechanisms
- **Node Voting**: Democratic approval system for new nodes and actors
- **Oracle Validation**: Multi-node verification of speech submissions  
- **Byzantine Fault Tolerance**: Network continues operation with up to 33% compromised nodes
- **Signature Verification**: RSA cryptographic authentication for all network communications

#### Market Resolution Pipeline

1. **Market Expiration**: Automatic status transition when end_time passes
2. **Oracle Window Opens**: Authorized oracles can submit actual speech text
3. **Network Validation**: Nodes vote on oracle submission accuracy
4. **Consensus Achievement**: Required percentage of nodes must agree
5. **Text Analysis**: Levenshtein distance calculation for all submissions
6. **Winner Selection**: Lowest distance submission wins the market
7. **Payout Processing**: Stakes redistributed proportionally minus platform fees
8. **Ledger Recording**: Final resolution permanently recorded in time ledger

#### Advanced Security Features

**Multi-Layer Validation:**
- Blockchain transaction confirmation before submission acceptance
- Cryptographic signature verification using wallet private keys  
- Duplicate transaction prevention across entire network history
- Rate limiting prevents spam attacks and ensures network stability

**Temporal Attack Prevention:**
- Time synchronization prevents premature oracle submissions
- Immutable ledger prevents retroactive market manipulation
- Network consensus required for any status changes
- Automatic monitoring detects timing inconsistencies

### Performance & Scalability

**High-Performance Design:**
- **Async Processing**: Celery background tasks handle compute-intensive operations
- **Distributed Caching**: Redis cluster manages real-time data across nodes
- **Database Optimization**: PostgreSQL with connection pooling and read replicas
- **Load Balancing**: Horizontal scaling support with session persistence

**Resource Management:**
- **Memory Optimization**: Efficient text processing for large prediction volumes
- **Network Bandwidth**: Compressed inter-node communication protocols  
- **Storage Efficiency**: Optimized database schemas with proper indexing
- **CPU Utilization**: Multi-threaded consensus processing and validation

### Security

- All node communications are signed with RSA key pairs
- Blockchain transactions are validated before acceptance
- Input sanitization prevents injection attacks
- Rate limiting protects against spam submissions

## Deployment

### Production Setup

1. Use a production WSGI server (Gunicorn recommended)
2. Configure PostgreSQL with connection pooling
3. Set up Redis cluster for high availability
4. Use Nginx as reverse proxy with SSL termination
5. Enable monitoring with application metrics

### Docker Deployment

```bash
docker-compose up -d
```

This starts all services with proper networking and volumes.

### Scaling Considerations

- Web servers can be horizontally scaled behind load balancer
- Celery workers scale based on queue depth
- Database requires read replicas for high traffic
- Redis cluster handles distributed caching

## Troubleshooting

### Common Issues

1. **"Error checking for updates"**: Ensure Redis is running and accessible
2. **Database connection errors**: Verify PostgreSQL credentials and network access
3. **Blockchain validation failures**: Check RPC endpoints and API keys
4. **Consensus failures**: Ensure sufficient active nodes in network

### Logs

- Application logs: Check console output or configured log files
- Celery logs: Monitor worker and beat process outputs
- Database logs: PostgreSQL logs for query performance
- Network logs: Inter-node communication in debug mode

## Contributing

Please read CONTRIBUTING.md for development guidelines and ENGINEERING.md for technical architecture details.

## License

[Your License Here]

## Support

- Documentation: [docs.clockchain.network]
- Issues: [github.com/your-org/clockchain-node/issues]
- Discord: [discord.gg/clockchain]