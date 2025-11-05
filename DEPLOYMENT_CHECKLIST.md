# Mainnet Deployment Checklist
**Version 1.0** | **Created: November 3, 2025** | **For BASE Mainnet Launch**

## Pre-Deployment (Complete Before Deploy Day)

### Infrastructure Setup
- [ ] Production RPC endpoints configured (Alchemy + QuickNode backup)
- [ ] Redis instance deployed and tested
- [ ] CDN configured for static assets
- [ ] Error tracking (Sentry) API keys obtained
- [ ] Monitoring (Datadog/New Relic) configured
- [ ] Backup RPC endpoints tested

### Wallet Preparation
- [ ] Hardware wallet funded with BASE ETH (minimum 0.5 ETH for deployment)
- [ ] Multisig wallet created (3-of-5) for emergency operations
- [ ] All wallet addresses documented securely
- [ ] Private keys backed up offline (3 separate locations)
- [ ] Test transaction on BASE Sepolia successful

### Security Audit
- [ ] External security audit completed (CertiK/OpenZeppelin)
- [ ] All critical findings remediated
- [ ] Audit certificate received
- [ ] Bug bounty program listed (Immunefi)
- [ ] Code review by 2+ senior developers

### Smart Contract Verification
- [ ] All contracts compile without warnings
- [ ] Gas optimization verified (<500k per transaction)
- [ ] Contract sizes under 24KB limit
- [ ] No admin/owner functions in final code
- [ ] Immutability verified (no upgradeable proxies)

## Deployment Day

### Step 1: Deploy Genesis NFT (30 mins)
```bash
# Terminal 1: Deploy Genesis NFT
npx hardhat run scripts/deploy-genesis-mainnet.js --network baseMainnet

# Verify immediately
npx hardhat verify --network baseMainnet <GENESIS_NFT_ADDRESS>
```

**Checklist:**
- [ ] Deployment transaction confirmed
- [ ] Contract verified on Basescan
- [ ] Max supply = 100 (verify on-chain)
- [ ] Minting window = 24 hours
- [ ] Test mint function (1 NFT to test wallet)
- [ ] SVG metadata rendering correctly on OpenSea

### Step 2: Deploy Payout Manager (20 mins)
```bash
# Deploy ImprovedDistributedPayoutManager
npx hardhat run scripts/deploy-payout-mainnet.js --network baseMainnet

# Verify
npx hardhat verify --network baseMainnet <PAYOUT_MANAGER_ADDRESS> <GENESIS_NFT_ADDRESS>
```

**Checklist:**
- [ ] Linked to Genesis NFT contract
- [ ] Fee distribution percentages correct (1.4% to Genesis holders)
- [ ] No owner withdrawal functions
- [ ] Test payout calculation

### Step 3: Deploy Core Contracts (40 mins)
```bash
# Deploy all platform contracts
npx hardhat run scripts/deploy-platform-mainnet.js --network baseMainnet
```

**Contracts to deploy:**
- [ ] EnhancedPredictionMarket
- [ ] DecentralizedOracle
- [ ] ActorRegistry
- [ ] NodeRegistry

**Post-deployment checks:**
- [ ] All contracts verified on Basescan
- [ ] Contract addresses saved to deployments/base-mainnet.json
- [ ] Gas prices reasonable (test with 1 gwei)
- [ ] All inter-contract links verified

### Step 4: Initialize Platform (15 mins)
```bash
# Run initialization
npx hardhat run scripts/initialize-mainnet.js --network baseMainnet
```

**Initialization tasks:**
- [ ] Register initial actors (top 10 Twitter accounts)
- [ ] Set up 3 initial oracle nodes
- [ ] Configure fee distribution
- [ ] Verify contract permissions

### Step 5: Frontend Deployment (20 mins)
```bash
# Update environment variables
export NEXT_PUBLIC_NETWORK=base
export NEXT_PUBLIC_CHAIN_ID=8453
export NEXT_PUBLIC_GENESIS_NFT_ADDRESS=<address>
export NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=<address>

# Deploy frontend
vercel --prod
# or: netlify deploy --prod
```

**Frontend checklist:**
- [ ] All contract addresses updated
- [ ] Network switched to BASE mainnet
- [ ] Wallet connection tested
- [ ] Test market creation (0.001 ETH)
- [ ] Mobile responsive

### Step 6: Smoke Tests (30 mins)
Run comprehensive smoke tests on production:

```bash
npx hardhat run scripts/smoke-test-mainnet.js --network baseMainnet
```

**Test scenarios:**
- [ ] Connect wallet (MetaMask)
- [ ] Connect wallet (Coinbase Wallet)
- [ ] Create test market (0.001 ETH)
- [ ] Submit prediction
- [ ] Place bet
- [ ] Check balance updates
- [ ] Verify events emitted
- [ ] Test Genesis NFT metadata

## Post-Deployment (First 24 Hours)

### Monitoring Setup
- [ ] Dashboard configured with real-time metrics
- [ ] Alert thresholds configured:
  - Gas price >100 gwei
  - Transaction failure rate >5%
  - Contract balance <0.1 ETH
  - API error rate >1%
- [ ] On-call rotation established
- [ ] Incident response plan reviewed

### Genesis NFT Distribution
- [ ] Team allocation minted (30 NFTs)
- [ ] Vesting contracts deployed (20 NFTs)
- [ ] Public minting announced on Twitter
- [ ] Minting page live and tested
- [ ] OpenSea collection visible
- [ ] Coinbase NFT verification submitted

### Communication
- [ ] Launch announcement on Twitter
- [ ] Discord server opened
- [ ] Blog post published
- [ ] Press release sent to crypto media
- [ ] Email to waitlist sent

## Week 1 Post-Launch

### System Health
- [ ] Zero critical bugs reported
- [ ] 95%+ transaction success rate
- [ ] Average gas cost <$1
- [ ] Response time <500ms
- [ ] No contract exploits detected

### User Metrics
- [ ] 500+ active users
- [ ] 50+ markets created
- [ ] $50k+ total volume
- [ ] Positive community feedback
- [ ] <10% user drop-off at each step

### Support
- [ ] Discord active with <1hr response time
- [ ] FAQ updated based on common questions
- [ ] Video tutorials published
- [ ] Known issues documented

## Emergency Procedures

### Critical Bug Response
1. **Detect**: Monitoring alerts trigger
2. **Assess**: Severity and impact evaluation
3. **Communicate**: Immediate Twitter + Discord announcement
4. **Respond**: Execute emergency procedure (if pause still enabled)
5. **Fix**: Deploy hotfix if needed
6. **Review**: Post-mortem within 48 hours

### Contact Information
- **Lead Developer**: [Contact info]
- **Security Lead**: [Contact info]
- **Community Manager**: [Contact info]
- **24/7 Incident Line**: [Number]

## Rollback Plan

If critical issues arise in first 6 hours:
1. Announce pause on all channels
2. Document issue in detail
3. Refund any affected transactions manually
4. Fix issue on testnet first
5. Re-audit if contract changes needed
6. Relaunch with fixed version

## Success Criteria

### Launch Success (Week 1)
- [ ] Zero contract exploits
- [ ] 500+ active users
- [ ] 50+ markets created
- [ ] $50k+ volume
- [ ] <5% transaction failure rate
- [ ] Positive media coverage (5+ articles)

### Growth Success (Month 1)
- [ ] 5,000+ users
- [ ] 500+ markets
- [ ] $500k+ volume
- [ ] Genesis NFT floor price established
- [ ] 10+ independent oracle nodes

## Documentation Links

- [GAP_CLOSING_PLAN.md](./GAP_CLOSING_PLAN.md) - Overall execution plan
- [ENGINEERING.md](./docs/ENGINEERING.md) - Technical architecture
- [GOVERNANCE.md](./docs/GOVERNANCE.md) - Governance model
- [API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md) - API reference

## Notes

- **Gas Price**: Always use 1 gwei on BASE mainnet for cost efficiency
- **Transaction Limits**: 500k gas for markets, 300k for submissions, 200k for bets
- **Oracle Requirement**: 1 minimum at UI level (auto-padded to 3 for contract)
- **Support Hours**: 24/7 for first week, then 12/7 ongoing

---

**Last Updated**: November 3, 2025
**Next Review**: Before mainnet deployment
**Status**: Ready for execution
