# Clockchain Node Operator

## Overview

Clockchain is a sophisticated distributed ledger platform for decentralized linguistic prediction markets. The system enables users to create predictions about what specific public figures will say within designated time windows, with betting markets forming around competing predictions and automatic resolution through oracle validation using text similarity algorithms.

### Key Features

- **Linguistic Prediction Markets**: Create predictions about future statements by public figures
- **Decentralized Oracle System**: Distributed validation of actual speech against predictions
- **Levenshtein Distance Algorithm**: Automated text similarity scoring for prediction resolution
- **Synthetic Time Ledger**: Immutable timeline of all predictions, bets, and resolutions
- **Multi-Currency Support**: Stakes and payouts in ETH and BTC
- **Distributed Node Network**: Fault-tolerant consensus mechanism across multiple operators
- **Real-time Visualization**: Interactive timeline showing active and historical predictions

### How It Works

1. **Submission Creation**: Users create predictions by betting that a specific actor will say certain words within a time window
2. **Secondary Market**: Other users can place bets on competing predictions for the same actor and timeframe
3. **Oracle Validation**: When the time window expires, oracles submit the actual text spoken by the actor
4. **Automatic Resolution**: The system compares all predictions using Levenshtein distance and resolves in favor of the closest match
5. **Payout Distribution**: Stakes are distributed to winning participants minus platform fees

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

### Clockchain Timeline

The main interface at `http://localhost:5000/clockchain` provides:

- Visual timeline of all predictions and their time windows
- Real-time updates on betting volumes and competing submissions
- Detailed views of individual predictions with stake history
- Historical analysis of resolved predictions and accuracy metrics

### API Endpoints

The platform provides REST APIs for programmatic access:

- `/api/actors` - Manage public figures available for predictions
- `/api/bets` - Create and query prediction markets
- `/api/stakes` - Place bets on existing predictions
- `/api/oracle` - Submit oracle validations
- `/api/network` - Query network status and node information

## Configuration

### Network Parameters

- `CONSENSUS_THRESHOLD`: Minimum percentage of nodes required for consensus (default: 51%)
- `PLATFORM_FEE_RATE`: Fee percentage taken from winning payouts (default: 1%)
- `LEVENSHTEIN_THRESHOLD`: Similarity threshold for text matching (default: 80%)
- `ORACLE_VOTE_TIMEOUT`: Time window for oracle submissions (default: 1 hour)

### Time Management

The system operates on Pacific Time (America/Los_Angeles) for all predictions and resolutions. Time synchronization across nodes is critical for consensus.

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