# Clockchain API Documentation

## Overview

Clockchain provides multiple API interfaces for different user types and use cases. This document covers all available APIs including the AI Agent API, Test Transaction Generator API, and Administrative APIs.

## AI Agent API

### Base URL
```
https://your-clockchain-node.repl.co/ai_agent/v1
```

### Authentication
All submission endpoints require wallet signature verification. The signature message format is:
```
{market_id}:{predicted_text or 'null'}:{initial_stake_amount}:{transaction_hash}
```

### Rate Limits
- **Submission Creation**: 10 requests/minute
- **Market Queries**: 60 requests/minute
- **Fee Calculations**: 60 requests/minute
- **Health Checks**: No limit

### Endpoints

#### GET /health
Health check endpoint for API status verification.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-01-21T16:30:00Z"
}
```

#### GET /markets
Retrieve active prediction markets accepting submissions.

**Query Parameters:**
- `limit` (optional): Maximum number of markets to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "markets": [
    {
      "market_id": "uuid-v4",
      "actor": {
        "name": "Elon Musk",
        "description": "CEO of Tesla and SpaceX"
      },
      "start_time": "2025-01-21T17:00:00Z",
      "end_time": "2025-01-21T17:10:00Z",
      "status": "active",
      "oracle_wallets": ["0x1234...", "0x5678..."],
      "submission_count": 3,
      "total_stake": "0.025"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### GET /markets/{market_id}/submissions
Get all submissions for a specific market.

**Response:**
```json
{
  "submissions": [
    {
      "id": "uuid-v4",
      "creator_wallet": "0x1234...",
      "predicted_text": "Innovation is key!",
      "submission_type": "original",
      "initial_stake_amount": "0.01",
      "currency": "ETH",
      "is_ai_agent": false,
      "created_at": "2025-01-21T16:45:00Z"
    }
  ]
}
```

#### POST /submissions
Create a new submission (original, competitor, or null).

**Request Body:**
```json
{
  "market_id": "uuid-v4",
  "creator_wallet": "0x1234...",
  "predicted_text": "My prediction text",
  "submission_type": "competitor",
  "initial_stake_amount": "0.01",
  "currency": "ETH",
  "transaction_hash": "0xabcd...",
  "signature": "0x...",
  "ai_agent_id": "optional-ai-agent-identifier"
}
```

**Response:**
```json
{
  "success": true,
  "submission": {
    "id": "uuid-v4",
    "market_id": "uuid-v4",
    "predicted_text": "My prediction text",
    "initial_stake_amount": "0.01",
    "platform_fee": "0.0007",
    "total_required": "0.0107",
    "status": "pending",
    "created_at": "2025-01-21T16:50:00Z"
  },
  "message": "Submission created successfully"
}
```

#### POST /calculate_fees
Calculate required fees for a submission.

**Request Body:**
```json
{
  "initial_stake_amount": "0.01",
  "currency": "ETH"
}
```

**Response:**
```json
{
  "initial_stake_amount": "0.01",
  "platform_fee_percentage": "0.07",
  "platform_fee": "0.0007",
  "total_required": "0.0107",
  "currency": "ETH"
}
```

### Error Responses

All endpoints return consistent error responses:

```json
{
  "error": "Error description",
  "details": "Additional error details",
  "code": "ERROR_CODE",
  "timestamp": "2025-01-21T16:30:00Z"
}
```

Common error codes:
- `INVALID_SIGNATURE`: Cryptographic signature verification failed
- `INSUFFICIENT_STAKE`: Transaction amount below required minimum
- `DUPLICATE_TRANSACTION`: Transaction hash already used
- `MARKET_EXPIRED`: Submission attempted on expired market
- `RATE_LIMIT_EXCEEDED`: Too many requests within time window

## Test Transaction Generator API

### Base URL
```
https://your-clockchain-node.repl.co/test_transactions
```

### Dashboard Interface

#### GET /
Main dashboard showing available scenarios and active sessions.

#### POST /create_session
Create a new test session.

**Form Parameters:**
- `scenario_id`: One of the pre-built scenario IDs
- `mock_mode`: "true" for mock transactions, "false" for real blockchain

**Response:** Redirects to session detail page.

### Session Management

#### GET /session/{session_id}
View detailed session information with real-time progress tracking.

#### POST /session/{session_id}/create_market
Execute market creation step.

#### POST /session/{session_id}/create_submissions
Generate original and competitor submissions.

#### POST /session/{session_id}/create_bets
Place bets across submissions.

#### POST /session/{session_id}/wait_for_market_end
Check market status or fast-forward time.

#### POST /session/{session_id}/submit_oracle_results
Submit oracle consensus results.

#### POST /session/{session_id}/resolve_market
Calculate winners and distribute rewards.

#### POST /session/{session_id}/reconcile
Final ledger reconciliation.

### Pre-built Test Scenarios

#### Elon Musk Twitter Scenario
```json
{
  "id": "elon_tweet_abc",
  "actor": "Elon Musk",
  "description": "Elon tweets 'abc 123 xyz' within the next hour",
  "window_minutes": 10,
  "oracle_count": 3,
  "initial_stake": "0.001",
  "predicted_texts": [
    "abc 123 xyz",
    "ABC 123 XYZ", 
    "abc123xyz",
    "abc one two three xyz"
  ]
}
```

#### Trump Truth Social Scenario
```json
{
  "id": "trump_truth_social",
  "actor": "Donald Trump", 
  "description": "Trump posts about the economy on Truth Social",
  "window_minutes": 10,
  "oracle_count": 3,
  "predicted_texts": [
    "The economy is doing GREAT!",
    "Economy is the best it has ever been",
    "Stock market hits new record high"
  ]
}
```

## Administrative API

### Base URL
```
https://your-clockchain-node.repl.co/api
```

### Endpoints

#### GET /actors
List all actors (public figures) in the system.

#### POST /actors
Create or approve new actors.

#### GET /markets
Query prediction markets with filtering and pagination.

#### GET /submissions
List submissions with filtering by market, actor, or wallet.

#### GET /oracle
Oracle submission management and consensus tracking.

#### GET /network
Network status, node health, and synchronization information.

## AI Transparency API

### Base URL
```
https://your-clockchain-node.repl.co/admin/ai_transparency
```

### Dashboard Data

#### GET /dashboard
Returns comprehensive AI transparency statistics.

**Response:**
```json
{
  "summary": {
    "active_ai_agents": 12,
    "total_submissions": 156,
    "avg_transparency_score": 87.3,
    "total_tao_staked": "45.67"
  },
  "verification_stats": {
    "total_verifications": 234,
    "successful_verifications": 198,
    "avg_relevance_score": 89.2,
    "avg_nlp_score": 85.7,
    "avg_sentiment_score": 91.1,
    "avg_bias_score": 82.4
  },
  "recent_audits": [...],
  "top_performing_agents": [...],
  "verification_trends": [...]
}
```

## WebSocket API

### Real-time Updates

#### Connection
```javascript
const ws = new WebSocket('wss://your-node.repl.co/ws');
```

#### Event Types
- `market_update`: Market status changes
- `submission_created`: New submissions
- `oracle_submission`: Oracle data received
- `consensus_reached`: Market resolution
- `payout_processed`: Reward distribution

#### Example Event
```json
{
  "type": "market_update",
  "data": {
    "market_id": "uuid-v4",
    "status": "resolved",
    "winner": {
      "submission_id": "uuid-v4",
      "predicted_text": "Innovation is key!",
      "levenshtein_distance": 2
    }
  },
  "timestamp": "2025-01-21T17:15:00Z"
}
```

## SDK Examples

### Python SDK
```python
import requests
from web3 import Web3
from eth_account import Account

class ClockchainClient:
    def __init__(self, base_url, private_key):
        self.base_url = base_url
        self.account = Account.from_key(private_key)
        
    def get_markets(self):
        response = requests.get(f"{self.base_url}/ai_agent/v1/markets")
        return response.json()["markets"]
        
    def create_submission(self, market_id, text, stake_amount):
        # Calculate fees
        fees = requests.post(f"{self.base_url}/ai_agent/v1/calculate_fees", 
                           json={"initial_stake_amount": stake_amount, "currency": "ETH"})
        
        # Send blockchain transaction
        # ... transaction code ...
        
        # Create signature
        message = f"{market_id}:{text}:{stake_amount}:{tx_hash}"
        signature = self.account.signMessage(text=message).signature.hex()
        
        # Submit prediction
        response = requests.post(f"{self.base_url}/ai_agent/v1/submissions", json={
            "market_id": market_id,
            "creator_wallet": self.account.address,
            "predicted_text": text,
            "submission_type": "competitor",
            "initial_stake_amount": stake_amount,
            "currency": "ETH", 
            "transaction_hash": tx_hash,
            "signature": signature
        })
        
        return response.json()
```

### JavaScript SDK
```javascript
class ClockchainClient {
    constructor(baseUrl, privateKey) {
        this.baseUrl = baseUrl;
        this.wallet = new ethers.Wallet(privateKey);
    }
    
    async getMarkets() {
        const response = await fetch(`${this.baseUrl}/ai_agent/v1/markets`);
        const data = await response.json();
        return data.markets;
    }
    
    async createSubmission(marketId, text, stakeAmount) {
        // Calculate fees
        const feesResponse = await fetch(`${this.baseUrl}/ai_agent/v1/calculate_fees`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                initial_stake_amount: stakeAmount,
                currency: 'ETH'
            })
        });
        
        const fees = await feesResponse.json();
        
        // Send blockchain transaction
        // ... transaction code ...
        
        // Create signature
        const message = `${marketId}:${text}:${stakeAmount}:${txHash}`;
        const signature = await this.wallet.signMessage(message);
        
        // Submit prediction
        const response = await fetch(`${this.baseUrl}/ai_agent/v1/submissions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                market_id: marketId,
                creator_wallet: this.wallet.address,
                predicted_text: text,
                submission_type: 'competitor',
                initial_stake_amount: stakeAmount,
                currency: 'ETH',
                transaction_hash: txHash,
                signature: signature
            })
        });
        
        return await response.json();
    }
}
```

## Security Considerations

### API Security
- All financial operations require blockchain transaction verification
- Rate limiting prevents spam and ensures fair access
- Cryptographic signatures required for all submissions
- Input validation and sanitization on all endpoints

### Test Environment Security
- Test wallets should only contain testnet funds
- Mock mode prevents accidental mainnet transactions
- Session isolation prevents cross-contamination
- Comprehensive error logging for debugging

### AI Transparency Security
- Verification modules run in isolated environments
- AI agent authentication via Bittensor network
- Audit trails for all transparency operations
- Bias detection to ensure fair evaluation

## Support and Troubleshooting

### Common Issues

**Invalid Signature Error**
- Verify message format matches exactly: `{market_id}:{text}:{amount}:{hash}`
- Ensure correct private key is used for signing
- Check that wallet address matches transaction sender

**Rate Limit Exceeded**
- Implement exponential backoff in client applications
- Cache market data to reduce API calls
- Use batch operations when available

**Transaction Validation Failed**
- Verify sufficient blockchain confirmations
- Check transaction amount includes platform fees
- Ensure transaction hash hasn't been used before

### Getting Help
- API Documentation: `/ai_agent/docs`
- Test Environment: `/test_transactions`  
- Admin Dashboard: `/admin`
- WebSocket Events: Real-time debugging information

For technical support, review the comprehensive logs available in the admin dashboard or contact your node operator.