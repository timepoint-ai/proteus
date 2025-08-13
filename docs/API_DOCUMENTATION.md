# Clockchain API Documentation

**Last Updated**: August 13, 2025 (Phase 7 Complete)

## Overview

The Clockchain API provides fully decentralized, blockchain-only access to all platform data. All endpoints query the blockchain directly with no database dependencies.

## Base URL

```
https://clockchain.app/api/chain/
```

## Authentication

All API endpoints use wallet-based JWT authentication:

1. Connect wallet (MetaMask/Coinbase Wallet)
2. Sign authentication message
3. Receive JWT token
4. Include token in Authorization header: `Bearer <token>`

## Chain-Only API Endpoints

### 1. Get All Actors

```http
GET /api/chain/actors
```

**Response:**
```json
{
  "actors": [
    {
      "id": 1,
      "name": "Elon Musk",
      "handle": "@elonmusk",
      "verified": true,
      "market_count": 15
    }
  ],
  "source": "blockchain",
  "total": 1
}
```

### 2. Get All Markets

```http
GET /api/chain/markets
```

**Query Parameters:**
- `status` (optional): "active", "resolved", "all"
- `actor_id` (optional): Filter by actor ID
- `limit` (optional): Number of results (default: 100)

**Response:**
```json
{
  "markets": [
    {
      "id": 1,
      "actor_id": 1,
      "description": "Will say 'Mars' in next tweet",
      "end_time": 1735689600,
      "total_pool": "1000000000000000000",
      "status": "active",
      "submission_count": 5,
      "bet_count": 23
    }
  ],
  "source": "blockchain",
  "total": 1
}
```

### 3. Get Market Details

```http
GET /api/chain/markets/<market_id>
```

**Response:**
```json
{
  "market": {
    "id": 1,
    "actor": {
      "name": "Elon Musk",
      "handle": "@elonmusk"
    },
    "submissions": [
      {
        "id": 1,
        "predicted_text": "Mars is the future",
        "submitter": "0x123...",
        "stake": "100000000000000000",
        "odds": 3.5
      }
    ],
    "bets": [
      {
        "submission_id": 1,
        "bettor": "0x456...",
        "amount": "50000000000000000",
        "timestamp": 1735600000
      }
    ]
  },
  "source": "blockchain"
}
```

### 4. Get Platform Statistics

```http
GET /api/chain/stats
```

**Response:**
```json
{
  "stats": {
    "total_markets": 150,
    "active_markets": 45,
    "total_volume": "15000000000000000000000",
    "total_users": 1234,
    "genesis_holders": 85,
    "platform_fees_collected": "1050000000000000000000",
    "gas_price": "0.001000062",
    "chain": "base-sepolia"
  },
  "source": "blockchain"
}
```

### 5. Get Genesis NFT Holders

```http
GET /api/chain/genesis
```

**Response:**
```json
{
  "genesis": {
    "total_supply": 100,
    "holders": [
      {
        "address": "0x789...",
        "token_ids": [1, 5, 12],
        "count": 3,
        "earnings": "21000000000000000000"
      }
    ],
    "total_distributed": "1050000000000000000000",
    "payout_percentage": 1.4
  },
  "source": "blockchain"
}
```

### 6. Get Oracle Data

```http
GET /api/chain/oracle/<market_id>
```

**Response:**
```json
{
  "oracle": {
    "market_id": 1,
    "submissions": [
      {
        "oracle": "0xABC...",
        "actual_text": "Mars is definitely the future",
        "screenshot_ipfs": "QmXYZ...",
        "timestamp": 1735650000,
        "verified": true
      }
    ],
    "consensus_text": "Mars is definitely the future",
    "consensus_reached": true,
    "resolution_time": 1735651000
  },
  "source": "blockchain"
}
```

## Performance Features

### Caching
All endpoints utilize Redis caching with TTL:
- Actor data: 5 minutes
- Market lists: 30 seconds
- Statistics: 10 seconds
- Genesis data: 1 minute

### RPC Retry Logic
- Exponential backoff with jitter
- Automatic failover between RPC endpoints
- Maximum 3 retry attempts

## Rate Limiting
- Default: 100 requests per minute per wallet
- Genesis holders: 500 requests per minute
- No rate limit for contract interactions

## Error Responses

```json
{
  "error": "Description of error",
  "code": "ERROR_CODE",
  "details": "Additional information"
}
```

Common error codes:
- `UNAUTHORIZED`: Invalid or missing JWT token
- `BLOCKCHAIN_ERROR`: RPC connection issue
- `CONTRACT_ERROR`: Smart contract interaction failed
- `RATE_LIMITED`: Too many requests

## WebSocket Events

Connect to receive real-time updates:

```javascript
const ws = new WebSocket('wss://clockchain.app/ws');

// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  events: ['market_created', 'submission_added', 'market_resolved']
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

## Smart Contract Addresses

### BASE Sepolia (Testnet)
- GenesisNFT: `0x...`
- ImprovedDistributedPayoutManager: `0xE9eE183b76A8BDfDa8EA926b2f44137Aa65379B5`
- EnhancedPredictionMarket: `0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C`
- DecentralizedOracle: `0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1`

### BASE Mainnet
- Coming soon...

## Migration Notes

**Phase 7 Complete**: All database dependencies have been removed. The API now queries blockchain directly for all data. Legacy database endpoints have been deprecated and removed.