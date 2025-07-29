# CRYPTO_PLAN.md - BASE Blockchain Integration for Clockchain Prediction Market

## Executive Summary

This plan outlines the transformation of Clockchain from a multi-currency (ETH/BTC) prediction market to a BASE-exclusive platform with enhanced X.com post oracle resolution and fully decentralized architecture. The implementation prioritizes crypto culture, avoids KYC requirements, and optimizes for immediate functionality with transparent error reporting.

## Key Architectural Changes

1. **Blockchain Migration**: Replace ETH/BTC dual support with BASE Layer 2 exclusive integration
2. **Oracle Enhancement**: X.com posts become primary oracle source with base64 screenshot caching
3. **Smart Wallet Integration**: Implement account abstraction with no-KYC wallets
4. **Decentralization**: Remove any centralized elements, implement full peer-to-peer node reconciliation
5. **Smart Contract Architecture**: Deploy prediction market contracts on BASE Sepolia/Mainnet

---

## Phase 1: Infrastructure & Smart Contract Development

### Smart Contract Architecture

| Component | File | Description | Goals | Tests |
|-----------|------|-------------|-------|-------|
| **PredictionMarket.sol** | `contracts/PredictionMarket.sol` | Core market logic with X.com post integration | - Create markets for linguistic predictions<br>- Store base64 screenshot proofs<br>- Handle submission competition<br>- Calculate Levenshtein distances | - Market creation<br>- Submission handling<br>- Oracle resolution<br>- Payout distribution |
| **ClockchainOracle.sol** | `contracts/ClockchainOracle.sol` | X.com post verification oracle | - Verify X.com post authenticity<br>- Store screenshot proofs on-chain<br>- Multi-node consensus validation<br>- Time-locked resolution | - Post verification<br>- Screenshot storage<br>- Consensus mechanism<br>- Time validation |
| **NodeRegistry.sol** | `contracts/NodeRegistry.sol` | Decentralized node management | - Node registration/staking<br>- Reputation tracking<br>- Byzantine fault tolerance<br>- Reward distribution | - Node registration<br>- Voting mechanics<br>- Slash conditions<br>- Reward claims |
| **PayoutManager.sol** | `contracts/PayoutManager.sol` | Automated payout system | - Calculate winner shares<br>- Distribute rewards<br>- Handle platform fees<br>- Emergency withdrawals | - Payout calculations<br>- Fee distribution<br>- Edge cases<br>- Gas optimization |

### Contract Deployment Workflow

| Step | Action | Files | Verification |
|------|--------|-------|--------------|
| 1 | Deploy to BASE Sepolia | `scripts/deploy.js` | Transaction hash logged |
| 2 | Verify contracts | `scripts/verify.js` | Basescan verification |
| 3 | Initialize parameters | `scripts/initialize.js` | State validation |
| 4 | Deploy to BASE Mainnet | `scripts/deploy-mainnet.js` | Multi-sig deployment |

---

## Phase 2: Backend Migration to BASE

### Database Schema Updates

| Model | Changes | Migration | Purpose |
|-------|---------|-----------|---------|
| **Bet** | Remove `currency` field, add `base_tx_hash` | `migrations/001_base_migration.py` | BASE-only transactions |
| **Submission** | Add `tweet_id`, `screenshot_ipfs`, `screenshot_base64` | `migrations/002_xcom_oracle.py` | X.com post tracking |
| **Transaction** | Remove BTC fields, add BASE-specific data | `migrations/003_base_transactions.py` | Simplified blockchain tracking |
| **OracleSubmission** | Add `tweet_verification`, `screenshot_proof` | `migrations/004_oracle_enhancement.py` | X.com verification data |

### Service Layer Updates

| Service | File | Updates | Testing Strategy |
|---------|------|---------|------------------|
| **BlockchainService** | `services/blockchain.py` | - Remove BTC validation<br>- Add BASE Web3 provider<br>- Implement smart wallet support<br>- Gas sponsorship integration | - Mock BASE transactions<br>- Test gas estimation<br>- Verify contract calls |
| **OracleService** | `services/oracle.py` | - X.com API integration<br>- Screenshot capture service<br>- Base64 encoding/storage<br>- Tweet verification logic | - Mock X.com responses<br>- Test screenshot capture<br>- Verify consensus logic |
| **PayoutService** | `services/payout.py` | - Smart contract payout calls<br>- Gas optimization<br>- Batch processing<br>- Fee calculations | - Test payout scenarios<br>- Gas usage analysis<br>- Edge case handling |
| **NodeSyncService** | `services/node_sync.py` | - P2P node discovery<br>- State reconciliation<br>- Conflict resolution<br>- Byzantine consensus | - Multi-node simulation<br>- Network partition tests<br>- Consensus verification |

---

## Phase 3: Frontend & User Experience

### UI Components Update

| Component | Location | Changes | User Flow |
|-----------|----------|---------|-----------|
| **WalletConnect** | `templates/components/wallet.html` | - Coinbase Smart Wallet SDK<br>- Best Wallet integration<br>- Account abstraction UI<br>- No seed phrase UX | 1. Click "Connect Wallet"<br>2. Choose wallet type<br>3. Instant connection<br>4. Ready to trade |
| **MarketCreation** | `templates/market/create.html` | - X.com post URL input<br>- Actor Twitter handle<br>- Time window selection<br>- Preview screenshot | 1. Enter X.com URL<br>2. Set prediction text<br>3. Define time window<br>4. Submit with BASE |
| **OracleSubmission** | `templates/oracle/submit.html` | - X.com post verification<br>- Screenshot preview<br>- Automated capture<br>- Consensus display | 1. Market expires<br>2. Submit X.com proof<br>3. Screenshot captured<br>4. Await consensus |
| **Timeline** | `templates/clockchain/timeline.html` | - BASE transaction links<br>- Tweet preview cards<br>- Real-time updates<br>- Gas cost display | Real-time market view with embedded tweets |

### API Endpoints Migration

| Endpoint | Changes | Authentication | Rate Limits |
|----------|---------|----------------|-------------|
| `/api/markets` | BASE-only market creation | Wallet signature | 10/minute |
| `/api/submit_oracle` | X.com verification required | Node operator key | 5/minute |
| `/api/payouts` | Smart contract interaction | Wallet ownership | 20/minute |
| `/api/tweets/verify` | New: X.com post validation | Public | 30/minute |

---

## Phase 4: X.com Oracle Integration

### X.com Integration Architecture

| Component | Implementation | Data Flow | Error Handling |
|-----------|----------------|-----------|----------------|
| **Tweet Fetcher** | `services/twitter_api.py` | 1. Fetch tweet by ID<br>2. Validate author<br>3. Extract text<br>4. Check timestamp | - API rate limits<br>- Invalid tweets<br>- Deleted posts<br>- Private accounts |
| **Screenshot Service** | `services/screenshot.py` | 1. Puppeteer capture<br>2. Base64 encoding<br>3. IPFS upload<br>4. On-chain storage | - Capture failures<br>- Size limits<br>- Encoding errors<br>- IPFS timeouts |
| **Verification Module** | `services/tweet_verify.py` | 1. Text extraction<br>2. Levenshtein calc<br>3. Time validation<br>4. Consensus check | - OCR failures<br>- Text mismatch<br>- Time disputes<br>- Split decisions |

### Screenshot Storage Strategy

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   X.com Post    │────▶│  Screenshot  │────▶│  Base64 + IPFS  │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │                       │
                               ▼                       ▼
                        ┌──────────────┐     ┌─────────────────┐
                        │ Local Cache  │     │ Smart Contract  │
                        └──────────────┘     └─────────────────┘
```

---

## Phase 5: Node Network & Consensus

### Multi-Node Architecture

| Node Type | Responsibilities | Requirements | Rewards |
|-----------|------------------|--------------|---------|
| **Full Node** | - Market validation<br>- Oracle consensus<br>- State replication<br>- API serving | - 100 BASE stake<br>- 99% uptime<br>- Public IP<br>- 10GB storage | - 5% of fees<br>- Oracle rewards<br>- Voting power |
| **Light Node** | - Read-only access<br>- Transaction relay<br>- Local validation | - No stake<br>- Basic hardware<br>- Internet access | - API access<br>- Network participation |
| **Archive Node** | - Full history<br>- Screenshot archive<br>- Data availability | - 500 BASE stake<br>- 1TB storage<br>- High bandwidth | - 10% of fees<br>- Storage rewards |

### Consensus Mechanism

```
Node A          Node B          Node C          Smart Contract
  │               │               │                    │
  ├──Propose──────┼───────────────┤                    │
  │               │               │                    │
  ├──Vote─────────▶               │                    │
  │               ├──Vote─────────▶                    │
  │               │               ├──Vote──────────────▶
  │               │               │                    │
  │◀──────────────┼───────────────┼──Consensus─────────┤
```

---

## Phase 6: Testing & Deployment

### Test Sequence

| Phase | Test Type | Environment | Success Criteria |
|-------|-----------|-------------|------------------|
| **Unit Tests** | Contract functions | Hardhat | 100% coverage |
| **Integration** | API + Contracts | BASE Sepolia | All endpoints functional |
| **Load Testing** | 1000 concurrent users | Testnet | <2s response time |
| **Security Audit** | Smart contracts | Professional audit | No critical issues |
| **Beta Launch** | Limited users | Mainnet | 1 week stable operation |
| **Full Launch** | Public access | Mainnet | Marketing campaign |

### Deployment Checklist

- [ ] Smart contracts deployed and verified on BASE
- [ ] Backend services migrated to BASE-only
- [ ] X.com API integration tested
- [ ] Screenshot service operational
- [ ] Multi-node network established
- [ ] No-KYC wallet options integrated
- [ ] Documentation updated
- [ ] Monitoring and alerts configured

---

## Phase 7: Error Handling & Monitoring

### Error Reporting Strategy

| Component | Log Location | Alert Threshold | Recovery Action |
|-----------|--------------|-----------------|-----------------|
| **Smart Contracts** | On-chain events | Any revert | Manual intervention |
| **API Services** | `logs/api.log` | 5 errors/minute | Auto-restart |
| **Node Sync** | `logs/consensus.log` | Consensus failure | Resync from peers |
| **X.com Integration** | `logs/twitter.log` | API rate limit | Backoff + queue |

### Self-Reporting Features

```python
# Example self-reporting implementation
class HealthCheck:
    def __init__(self):
        self.checks = {
            'base_connection': self.check_base_rpc,
            'twitter_api': self.check_twitter_api,
            'node_consensus': self.check_node_health,
            'contract_state': self.check_contract_sync
        }
    
    async def run_all_checks(self):
        results = {}
        for name, check in self.checks.items():
            try:
                results[name] = await check()
            except Exception as e:
                results[name] = {'status': 'error', 'message': str(e)}
                logger.error(f"Health check failed: {name} - {e}")
        return results
```

---

## Implementation Timeline

| Week | Phase | Deliverables | Verification |
|------|-------|--------------|--------------|
| 1-2 | Smart Contracts | All contracts deployed to testnet | Passing tests |
| 3-4 | Backend Migration | Services updated for BASE | API functional |
| 5-6 | X.com Integration | Oracle system with screenshots | Tweet verification working |
| 7-8 | Frontend Updates | New UI with wallet integration | User testing complete |
| 9-10 | Multi-node Setup | 3+ nodes in test network | Consensus achieved |
| 11-12 | Security & Launch | Audit complete, mainnet deploy | Public beta live |

---

## Risk Mitigation

| Risk | Mitigation Strategy | Fallback Plan |
|------|---------------------|---------------|
| X.com API Changes | Multiple API endpoints, scraping backup | Manual oracle submission |
| BASE Network Issues | Multi-RPC redundancy, local caching | Temporary read-only mode |
| Screenshot Disputes | Multiple capture methods, consensus | Manual review process |
| Node Attacks | Stake slashing, reputation system | Emergency pause function |

---

## Success Metrics

- **Launch Week**: 100 active markets, 1,000 users
- **Month 1**: 10,000 transactions, $100K volume
- **Month 3**: 50 active nodes, $1M volume
- **Month 6**: Fully decentralized, self-sustaining network

---

## Appendix: Key File Deletions

### Files to Remove (BTC-related)
- `services/btc_validation.py`
- `routes/btc_transactions.py`
- `templates/btc/*`
- Any BTC demo code in `routes/test_data.py`

### Configuration Updates
- Remove `BTC_RPC_URL` from `.env`
- Update `config.py` to remove BTC references
- Clean up `requirements.txt` from BTC libraries

---

This plan ensures a smooth transition to BASE with X.com oracle integration while maintaining the decentralized ethos of the project. All components are designed for transparency, verifiability, and true decentralization without KYC requirements.