# API Documentation

REST API reference for Proteus. All data is fetched from blockchain.

## Base URL

```
/api/chain/
```

## Authentication

Wallet-based JWT authentication:

1. Connect wallet (MetaMask/Coinbase)
2. Sign authentication message
3. Receive JWT token
4. Include in header: `Authorization: Bearer <token>`

---

## Authentication Endpoints

### Get Nonce

```http
GET /auth/nonce/{address}
```

**Response:**
```json
{
  "nonce": "abc123...",
  "message": "Sign this message to authenticate with Proteus: abc123..."
}
```

### Verify Signature

```http
POST /auth/verify
```

**Body:**
```json
{
  "address": "0x123...",
  "signature": "0x456...",
  "message": "Sign this message..."
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGc...",
  "address": "0x123..."
}
```

### Refresh Token

```http
POST /auth/refresh
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGc..."
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

**Response:** `200 OK`

---

## Embedded Wallet Endpoints

### Request OTP

```http
POST /api/embedded/request-otp
```

**Body:**
```json
{
  "identifier": "user@example.com",
  "auth_method": "email"
}
```

**Response:**
```json
{
  "success": true
}
```

### Verify OTP

```http
POST /api/embedded/verify-otp
```

**Body:**
```json
{
  "identifier": "user@example.com",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "wallet_address": "0x789..."
}
```

> **Test Mode:** When `FLASK_ENV=testing`, OTP code `123456` is accepted for any email.

---

## Health Endpoint

```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "proteus-node"
}
```

---

## Chain Endpoints

> **Integration Tests:** All chain endpoints are covered by integration tests in `tests/integration/test_api_chain.py`

### Get Actors

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

### Get Markets

```http
GET /api/chain/markets
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| status | string | "active", "resolved", or "all" |
| actor_id | int | Filter by actor |
| limit | int | Max results (default: 100) |

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

### Get Market Details

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
        "amount": "50000000000000000"
      }
    ]
  },
  "source": "blockchain"
}
```

### Get Platform Stats

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
    "genesis_holders": 60,
    "chain": "base-sepolia"
  },
  "source": "blockchain"
}
```

### Get Genesis NFT Data

```http
GET /api/chain/genesis
```

**Response:**
```json
{
  "genesis": {
    "total_supply": 100,
    "minted": 60,
    "holders": [
      {
        "address": "0x789...",
        "token_ids": [1, 5, 12],
        "count": 3
      }
    ],
    "payout_percentage": 1.4
  },
  "source": "blockchain"
}
```

### Get Oracle Data

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
        "verified": true
      }
    ],
    "consensus_text": "Mars is definitely the future",
    "consensus_reached": true
  },
  "source": "blockchain"
}
```

---

## Admin Resolution Endpoints (V2)

Endpoints for managing PredictionMarketV2 market resolution. Requires admin authentication.

> **Dashboard:** Web UI available at `/proteus/admin/resolution`

### Get Resolution Stats

```http
GET /api/admin/resolution-stats
```

**Response:**
```json
{
  "total_markets": 10,
  "resolved_markets": 5,
  "pending_resolution": 3,
  "active_markets": 2,
  "total_pool": "15.5",
  "pending_platform_fees": "0.75",
  "owner_address": "0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA",
  "owner_key_configured": true,
  "xcom_api_configured": false
}
```

### Get Pending Markets

```http
GET /api/admin/pending-markets
```

**Response:**
```json
{
  "pending_markets": [
    {
      "id": 1,
      "actor_handle": "elonmusk",
      "end_time": 1733270400,
      "end_time_formatted": "2024-12-03 18:00",
      "total_pool": "2.5",
      "submission_count": 3,
      "can_resolve": true
    }
  ]
}
```

### Get Market Resolution Details

```http
GET /api/admin/market/<market_id>/details
```

**Response:**
```json
{
  "market": {
    "id": 1,
    "actor_handle": "elonmusk",
    "end_time": 1733270400,
    "total_pool": "2.5",
    "resolved": false,
    "submissions": [
      {
        "id": 1,
        "submitter": "0x123...",
        "predicted_text": "Mars is the future!",
        "amount": "1.0"
      }
    ],
    "can_resolve": true
  }
}
```

### Resolve Market

```http
POST /api/admin/resolve-market/<market_id>
```

**Body:**
```json
{
  "actual_text": "The actual tweet text that was posted",
  "tweet_url": "https://x.com/user/status/123456789"
}
```

**Response (Success):**
```json
{
  "success": true,
  "tx_hash": "0xabc123...",
  "gas_used": 1500000,
  "market_id": 1
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Market has not ended yet",
  "market_id": 1
}
```

### Auto-Resolve Market (Fetch Tweet)

```http
POST /api/admin/auto-resolve-market/<market_id>
```

**Body:**
```json
{
  "tweet_url": "https://x.com/user/status/123456789"
}
```

> **Note:** Requires `X_BEARER_TOKEN` environment variable for X.com API access.
> X now offers [pay-per-use API pricing](https://developer.x.com/) -- credit-based billing, no subscriptions or monthly caps. Generate a bearer token at the [X Developer Portal](https://developer.x.com/).

**Response:**
```json
{
  "success": true,
  "tx_hash": "0xabc123...",
  "tweet_text": "The fetched tweet text",
  "market_id": 1
}
```

### Withdraw Platform Fees

```http
POST /api/admin/withdraw-fees
```

**Response (Success):**
```json
{
  "success": true,
  "tx_hash": "0xdef456...",
  "amount": "0.75"
}
```

**Response (No Fees):**
```json
{
  "success": false,
  "error": "No fees to withdraw"
}
```

---

## Error Responses

All API endpoints return standardized error responses:

**Error Response Format:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {}
  }
}
```

**Success Response Format:**
```json
{
  "success": true,
  "data": {},
  "message": "Optional success message"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input data or missing required fields |
| `INVALID_REQUEST` | 400 | Malformed request |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication |
| `INVALID_TOKEN` | 401 | JWT token is invalid |
| `TOKEN_EXPIRED` | 401 | JWT token or OTP has expired |
| `INVALID_SIGNATURE` | 401 | Wallet signature verification failed |
| `FORBIDDEN` | 403 | Permission denied |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `BLOCKCHAIN_ERROR` | 500 | RPC or chain interaction failed |
| `CONTRACT_ERROR` | 500 | Smart contract call failed |
| `WALLET_ERROR` | 500 | Wallet operation failed |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Market-Specific Error Codes

| Code | Description |
|------|-------------|
| `MARKET_NOT_FOUND` | Market does not exist |
| `MARKET_ENDED` | Market has already ended |
| `MARKET_NOT_ENDED` | Market has not ended yet |
| `MARKET_RESOLVED` | Market is already resolved |
| `INSUFFICIENT_FUNDS` | Not enough ETH for operation |

### Example Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "actual_text is required (or provide tweet_url)",
    "details": {
      "field": "actual_text"
    }
  }
}
```

---

## Rate Limits

| User Type | Limit |
|-----------|-------|
| Default | 100 req/min |
| Genesis Holder | 500 req/min |

---

## Caching

Responses are cached in Redis:

| Data | TTL |
|------|-----|
| Actors | 5 min |
| Markets | 30 sec |
| Stats | 10 sec |
| Genesis | 1 min |

---

## Contract Addresses

### BASE Sepolia (Testnet)

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

> **Note:** Use **PredictionMarketV2** for all new development. It has complete market lifecycle with on-chain resolution.

### BASE Mainnet

Not yet deployed.
