# Clockchain Production Launch Guide

## Overview

This guide outlines the steps to transition Clockchain from BASE Sepolia testnet to BASE mainnet production deployment.

## 1. Stripping Test Data

Before launching to production, all test data must be removed from the database:

### Step 1: Backup Current Database
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Step 2: Remove Test Data
```python
# Run the production data cleanup script
python scripts/clean_production_data.py
```

This script will:
- Remove all test actors (where `is_test_account = true`)
- Delete all associated markets, submissions, bets, and transactions
- Clear test node operators (keeping only production nodes)
- Reset oracle submissions and votes
- Clean up test wallet data

### Step 3: Verify Clean State
```sql
-- Verify no test actors remain
SELECT COUNT(*) FROM actors WHERE is_test_account = true;

-- Verify no test markets
SELECT COUNT(*) FROM prediction_markets WHERE actor_id IN 
  (SELECT id FROM actors WHERE is_test_account = true);
```

## 2. Using Real Data

### X.com Production API Setup

1. **Apply for X.com API v2 Access**
   - Visit: https://developer.twitter.com/en/portal/dashboard
   - Apply for Elevated access (required for screenshot capture)
   - Expected approval time: 1-2 weeks

2. **Configure Production Credentials**
   ```bash
   # Set environment variables
   XCOM_CONSUMER_KEY=your_consumer_key
   XCOM_CONSUMER_SECRET=your_consumer_secret
   XCOM_ACCESS_TOKEN=your_access_token
   XCOM_ACCESS_TOKEN_SECRET=your_access_token_secret
   XCOM_BEARER_TOKEN=your_bearer_token
   ```

3. **Update Rate Limits**
   ```python
   # config.py
   XCOM_RATE_LIMIT = 300  # Elevated tier: 300 requests/15min
   XCOM_SCREENSHOT_INTERVAL = 300  # 5 minutes between screenshots
   ```

### Real Actor Creation

1. **Create Production Actors**
   ```python
   # scripts/create_production_actors.py
   actors = [
       {
           "x_username": "elonmusk",
           "display_name": "Elon Musk",
           "bio": "From official X.com API",
           "verified": True,
           "is_test_account": False
       }
   ]
   ```

2. **Sync with X.com API**
   ```python
   # Automatically sync actor data from X.com
   python scripts/sync_actors_from_xcom.py
   ```

## 3. Launching on BASE Mainnet

### Network Configuration

BASE is Coinbase's Layer 2 blockchain built on the OP Stack, offering:
- **Chain ID**: 8453 (mainnet)
- **Currency**: ETH
- **Block Explorer**: https://basescan.org
- **RPC Endpoints**: See node providers below

### Step 1: Update Configuration

```python
# config.py
BASE_NETWORK = 'mainnet'  # Switch from 'sepolia'
BASE_CHAIN_ID = 8453  # Mainnet chain ID
BASE_RPC_URL = 'https://mainnet.base.org'  # Or use a node provider

# Contract addresses will be updated after deployment
PREDICTION_MARKET_ADDRESS = None  # To be deployed
CLOCKCHAIN_ORACLE_ADDRESS = None  # To be deployed
NODE_REGISTRY_ADDRESS = None  # To be deployed
PAYOUT_MANAGER_ADDRESS = None  # To be deployed
```

### Step 2: Select Node Provider

Choose a reliable RPC provider for production:

1. **Coinbase Developer Platform (CDP)**
   - Free tier available
   - Same infrastructure as Coinbase exchange
   - URL: https://api.developer.coinbase.com/rpc/v1/base/{project_id}

2. **Alchemy**
   - URL: https://base-mainnet.g.alchemy.com/v2/{api_key}
   - Robust free tier with SDKs

3. **QuickNode**
   - URL: https://base-mainnet.quiknode.pro/{endpoint_id}
   - Institutional-grade reliability

4. **Infura**
   - URL: https://base-mainnet.infura.io/v3/{project_id}
   - Enterprise support available

### Step 3: Deploy Smart Contracts

1. **Update Hardhat Configuration**
   ```javascript
   // hardhat.config.js
   networks: {
     base: {
       url: process.env.BASE_RPC_URL,
       accounts: [process.env.DEPLOYER_PRIVATE_KEY],
       chainId: 8453
     }
   }
   ```

2. **Deploy Contracts**
   ```bash
   # Deploy to BASE mainnet
   npx hardhat run scripts/deploy.js --network base
   
   # Verify contracts on Basescan
   npx hardhat verify --network base CONTRACT_ADDRESS
   ```

3. **Update Contract Addresses**
   ```python
   # Update config.py with deployed addresses
   PREDICTION_MARKET_ADDRESS = '0x...'
   CLOCKCHAIN_ORACLE_ADDRESS = '0x...'
   NODE_REGISTRY_ADDRESS = '0x...'
   PAYOUT_MANAGER_ADDRESS = '0x...'
   ```

### Step 4: Security Audit

1. **Pre-launch Checklist**
   - [ ] Smart contract audit completed
   - [ ] Rate limiting configured
   - [ ] DDoS protection enabled
   - [ ] SSL certificates valid
   - [ ] Backup procedures tested

2. **Contract Security**
   - [ ] Reentrancy guards implemented
   - [ ] Integer overflow protection
   - [ ] Access control verified
   - [ ] Emergency pause mechanism

### Step 5: Fund Production Wallets

1. **Platform Wallet**
   ```bash
   # Fund the platform wallet for gas costs
   # Recommended: 0.1 ETH minimum on BASE
   ```

2. **Oracle Wallets**
   ```bash
   # Fund each oracle wallet
   # Recommended: 0.05 ETH per oracle
   ```

### Step 6: Production Environment Setup

1. **Environment Variables**
   ```bash
   # .env.production
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   BASE_NETWORK=mainnet
   BASE_RPC_URL=https://...
   NODE_ENV=production
   ```

2. **Infrastructure**
   - Use production-grade PostgreSQL
   - Configure Redis with persistence
   - Enable monitoring and alerts
   - Set up automated backups

### Step 7: Launch Sequence

1. **Database Migration**
   ```bash
   flask db upgrade
   ```

2. **Start Services**
   ```bash
   # Start Celery workers
   celery -A app.celery worker --loglevel=info
   
   # Start Celery beat
   celery -A app.celery beat --loglevel=info
   
   # Start web server
   gunicorn main:app --workers 4 --bind 0.0.0.0:5000
   ```

3. **Verify Deployment**
   - Check contract deployment on Basescan
   - Verify RPC connectivity
   - Test wallet connections
   - Confirm oracle functionality

## Production Monitoring

### Key Metrics to Track

1. **Blockchain Metrics**
   - Gas prices (alert if > 0.002 gwei)
   - Transaction success rate
   - Block confirmation times
   - Contract event logs

2. **Application Metrics**
   - X.com API rate limits
   - Oracle consensus rates
   - Database query performance
   - WebSocket connection stability

3. **Business Metrics**
   - Active markets count
   - Total volume (BASE)
   - User wallet connections
   - Platform fee collection

### Alerting Configuration

```python
# monitoring/alerts.py
ALERT_THRESHOLDS = {
    'gas_price_gwei': 0.002,  # 50x normal
    'oracle_consensus_percent': 66,
    'xcom_rate_limit_remaining': 10,
    'error_rate_percent': 5
}
```

## Post-Launch Tasks

1. **Marketing Website**
   - Deploy landing page
   - Add documentation portal
   - Create API documentation
   - Set up community forum

2. **User Onboarding**
   - Interactive tutorial
   - Demo market creation
   - First-time user incentives
   - Help documentation

3. **Continuous Monitoring**
   - Daily health checks
   - Weekly performance reviews
   - Monthly security audits
   - Quarterly contract upgrades

## Rollback Procedures

If issues arise during launch:

1. **Immediate Actions**
   - Pause smart contracts
   - Stop accepting new markets
   - Preserve all transaction data

2. **Rollback Steps**
   ```bash
   # Restore database backup
   psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
   
   # Switch back to testnet
   BASE_NETWORK=sepolia
   ```

3. **Communication**
   - Notify users via all channels
   - Provide timeline for resolution
   - Offer compensation if needed

## Cost Estimates

### BASE Mainnet Costs

1. **Contract Deployment**
   - Estimated: 0.01-0.02 ETH total
   - One-time cost

2. **Operational Costs**
   - Gas per market creation: ~0.0001 ETH
   - Gas per oracle submission: ~0.00005 ETH
   - Platform maintenance: ~0.01 ETH/day

3. **Infrastructure Costs**
   - Node provider: $0-299/month
   - Database hosting: $50-200/month
   - Monitoring services: $100-500/month

## Support Resources

- **BASE Documentation**: https://docs.base.org
- **Coinbase Developer Platform**: https://www.coinbase.com/developer-platform
- **BASE Discord**: https://discord.gg/buildonbase
- **Basescan**: https://basescan.org
- **Status Page**: https://status.base.org