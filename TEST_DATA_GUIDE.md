# Clockchain Test Data Generation Guide

## Overview

Clockchain provides a comprehensive test data generation ecosystem for BASE Sepolia testnet development. The system includes automated scripts, visual interfaces, and E2E testing tools.

## Test Data Generation Components

### 1. Automated Script Generator (`scripts/generate_realistic_data.py`)

The primary test data generator creates realistic market scenarios with proper time flows and transaction patterns.

#### Features
- Creates 8+ celebrity actors with wallet addresses
- Generates active, pending, and resolved markets
- Simulates betting patterns with realistic volumes
- Creates oracle submissions with consensus
- Generates transaction history on BASE

#### Usage
```bash
python scripts/generate_realistic_data.py
```

This will create:
- 8 celebrity actors (Elon Musk, Taylor Swift, etc.)
- 15-20 prediction markets in various states
- 50+ submissions with diverse predictions
- 100+ bets with realistic stake patterns
- Complete transaction history
- Oracle consensus data

### 2. Test Manager Interface (`/test_manager`)

Visual interface for creating and managing test scenarios on BASE Sepolia.

#### Access
Navigate to: `http://localhost:5000/test_manager`

#### Features
- **Market Creation Wizard**: Step-by-step market setup
- **Wallet Management**: View and fund test wallets
- **Contract Interaction**: Direct smart contract calls
- **Result Verification**: Check oracle submissions and payouts
- **Transaction Monitor**: Real-time BASE transaction tracking

### 3. E2E Test Suite (`test_e2e_runner.py`)

Automated end-to-end testing of the complete market lifecycle.

#### Features
- Automated wallet creation and funding
- Market creation on BASE Sepolia
- Submission and betting simulation
- Oracle consensus testing
- Payout verification

#### Usage
```bash
python test_e2e_runner.py
```

## Test Wallet Configuration

### Available Test Wallets

The system uses pre-configured test wallets stored in `.test_wallets.json`:

```json
{
  "deployer": {
    "address": "0x...",
    "private_key": "0x..."
  },
  "oracle_1": {
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f2bD7d",
    "private_key": "0x..."
  },
  "oracle_2": {
    "address": "0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199",
    "private_key": "0x..."
  },
  "bettor_1": {
    "address": "0x...",
    "private_key": "0x..."
  }
}
```

### Funding Test Wallets

1. **Via Coinbase Faucet**: https://www.coinbase.com/faucets/base-ethereum-goerli-faucet
2. **Via Test Manager**: Use the "Fund Wallet" feature
3. **Via Script**: `python scripts/fund_test_wallets.py`

## Creating Realistic Test Scenarios

### Scenario 1: Active Market with Competition

```python
# Create market for Elon Musk
market = create_market(
    actor_name="Elon Musk",
    start_time=datetime.utcnow(),
    end_time=datetime.utcnow() + timedelta(hours=2)
)

# Create competing predictions
submission1 = create_submission(
    market_id=market.id,
    predicted_text="AI will revolutionize everything",
    stake_amount=0.01  # BASE
)

submission2 = create_submission(
    market_id=market.id,
    predicted_text="We need more nuclear power",
    stake_amount=0.015  # BASE
)

# Add bets
create_bet(submission1.id, amount=0.005)
create_bet(submission2.id, amount=0.008)
```

### Scenario 2: Oracle Resolution Test

```python
# Create expired market ready for oracle
market = create_market(
    actor_name="Taylor Swift",
    start_time=datetime.utcnow() - timedelta(hours=3),
    end_time=datetime.utcnow() - timedelta(hours=1)
)

# Submit oracle data
oracle_submission = submit_oracle_data(
    market_id=market.id,
    actual_text="Music brings us together",
    tweet_id="1234567890",
    screenshot_base64="..."
)
```

### Scenario 3: Payout Distribution Test

```python
# Create resolved market with winners
market = create_resolved_market(
    winning_text="Climate change is real",
    total_pool=0.5,  # BASE
    winner_count=3
)

# Verify payouts
verify_payouts(market.id)
```

## Test Data API Endpoints

### Generate Test Markets
```bash
POST /test_data/generate_markets
{
  "count": 5,
  "actor_names": ["Elon Musk", "Taylor Swift"],
  "time_range": "active"  # active, pending, expired
}
```

### Generate Test Bets
```bash
POST /test_data/generate_bets
{
  "market_id": "123",
  "bet_count": 10,
  "amount_range": [0.001, 0.1]  # BASE amounts
}
```

### Simulate Oracle Consensus
```bash
POST /test_data/simulate_oracle
{
  "market_id": "123",
  "consensus_percentage": 80,
  "actual_text": "The future is bright"
}
```

## Best Practices

### 1. Time-based Testing
- Use different time windows to test all market states
- Test timezone handling with international actors
- Verify oracle submission timing restrictions

### 2. Volume Testing
- Create markets with varying stake amounts
- Test with 0-100 bets per submission
- Verify gas optimization with large payouts

### 3. Edge Case Testing
- Empty predictions (null submissions)
- Exact text matches
- Consensus failures (< 66% agreement)
- Network disconnections

### 4. Integration Testing
- Test wallet switching in MetaMask
- Verify BASE network auto-switching
- Test transaction confirmation flows

## Monitoring Test Data

### Database Queries
```sql
-- Active markets
SELECT * FROM prediction_markets WHERE status = 'active';

-- Top submissions by volume
SELECT s.*, SUM(b.amount) as total_volume 
FROM submissions s 
JOIN bets b ON b.submission_id = s.id 
GROUP BY s.id 
ORDER BY total_volume DESC;

-- Oracle consensus stats
SELECT market_id, 
       COUNT(*) as oracle_count,
       AVG(CASE WHEN selected_submission_id IS NOT NULL THEN 1 ELSE 0 END) as consensus_rate
FROM oracle_submissions
GROUP BY market_id;
```

### Test Manager Dashboard
- Real-time market status
- Betting volume charts
- Oracle submission tracker
- Transaction confirmation status

## Troubleshooting

### Common Issues

1. **Insufficient BASE for tests**
   - Use faucet: https://www.coinbase.com/faucets
   - Reduce stake amounts in test data
   - Reuse funded test wallets

2. **Oracle timing errors**
   - Ensure market.end_time < current time
   - Check timezone settings
   - Verify contract time synchronization

3. **Transaction failures**
   - Check wallet BASE balance
   - Verify correct network (BASE Sepolia)
   - Review gas price settings

4. **Data consistency**
   - Run `python scripts/validate_test_data.py`
   - Check foreign key constraints
   - Verify transaction hashes are unique

## Advanced Testing

### Load Testing
```bash
# Generate 1000 markets with activity
python scripts/load_test.py --markets 1000 --bets-per-market 50
```

### Contract Stress Testing
```bash
# Test gas limits and optimization
python scripts/test_contract_limits.py
```

### Network Simulation
```bash
# Simulate network delays and failures
python scripts/network_simulation.py --delay 500ms --failure-rate 0.1
```

## Test Data Cleanup

### Reset Database
```bash
# Clear all test data
python scripts/clear_test_data.py --confirm

# Keep actors, clear markets
python scripts/clear_test_data.py --keep-actors
```

### Archive Test Results
```bash
# Export test data for analysis
python scripts/export_test_results.py --format json --output test_results_$(date +%Y%m%d).json
```

## Continuous Integration

### GitHub Actions
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run E2E Tests
        run: |
          python scripts/generate_realistic_data.py
          python test_e2e_runner.py
```

## Resources

- **BASE Sepolia Faucet**: https://www.coinbase.com/faucets
- **Contract Addresses**: See README.md
- **API Documentation**: `/ai_agent`
- **Test Manager**: `/test_manager`