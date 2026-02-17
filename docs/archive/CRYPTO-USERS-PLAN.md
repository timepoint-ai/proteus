# Proteus Crypto User Experience Plan
## Coinbase Embedded Wallet & Onramp Integration

### Executive Summary
This document outlines the integration of Coinbase's embedded wallet and onramp solutions to create a seamless, crypto-native prediction market platform where users don't need to understand blockchain technology. The platform will operate fully on-chain to bypass KYC requirements while providing a familiar web2 user experience.

### Implementation Status (January 28, 2025)

#### ✅ Phase 1: Authentication Foundation (COMPLETED)
- Firebase Authentication integration for real email OTP
- Embedded wallet service architecture (`services/embedded_wallet.py`)
- API credentials configured (Coinbase & Firebase)
- Test interface at `/api/embedded/test`
- Firebase setup documentation created

#### 🚧 Phase 2: Frontend Wallet Migration (IN PROGRESS)
**Current State**: Frontend uses MetaMask exclusively via `window.ethereum`
**Target State**: Replace with Coinbase Embedded Wallet SDK

**Files Requiring Updates:**
- `static/js/wallet.js` - Main wallet connection logic
- `static/js/wallet-auth.js` - Authentication flow
- `static/js/betting-contract.js` - Smart contract interactions
- `static/js/market-blockchain.js` - Market operations
- `static/js/base-blockchain.js` - BASE network operations

#### ⏳ Phase 3: Coinbase Onramp Integration (PLANNED)
- Implement funding widget in UI
- Support Apple Pay, bank transfer, Coinbase account
- USDC direct purchase on BASE
- Zero-fee strategy for USDC purchases

#### ❌ Phase 4: Transaction Signing (TODO)
- Replace MetaMask transaction prompts with embedded wallet
- Implement policy-based transaction limits
- Add 2FA for high-value transactions

#### ❌ Phase 5: Production Deployment (TODO)
- Remove MetaMask dependencies completely
- Hide advanced mode toggle
- Production testing and optimization  

---

## 🎯 Strategic Goals

### Primary Objectives
1. **Remove Crypto Friction**: Users login with email/SMS, not seed phrases ✅ ACTIVE
2. **Simplify Funding**: Apple Pay, bank transfer, or Coinbase account - no complex bridges ⏳
3. **Hide Blockchain Complexity**: Users bet in USD values, system handles crypto conversion ⏳
4. **Maintain Decentralization**: All betting and settlement remains on-chain (BASE) ✅ 
5. **Bypass KYC Requirements**: Fully on-chain operations avoid regulatory overhead ✅

### User Experience Vision
- **Feels Like**: A normal betting website with email login
- **Works Like**: A fully decentralized blockchain application
- **Result**: Mainstream adoption without crypto knowledge barriers

---

## 📋 Implementation Phases

### Phase 2: Frontend Wallet Migration (Detailed)

#### Phase 2.1: Create Coinbase Wallet Adapter
Create new file: `static/js/coinbase-wallet.js`
```javascript
// Coinbase Embedded Wallet wrapper
class CoinbaseEmbeddedWallet {
  constructor() {
    this.wallet = null;
    this.address = null;
    this.provider = null;
    this.isConnected = false;
  }
  
  async init() {
    // Load Coinbase SDK
    const { Wallet } = await import('@coinbase/waas-sdk-web');
    
    this.wallet = await Wallet.create({
      projectId: window.COINBASE_PROJECT_ID,
      enableHostedBackups: true,
      prod: false  // Use true for mainnet
    });
    
    // Create provider for Web3 compatibility
    this.provider = this.wallet.getEthereumProvider();
    
    return this;
  }
  
  async authenticate(email) {
    // User already authenticated via Firebase
    // Link wallet to authenticated user
    const result = await fetch('/api/embedded/link-wallet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    
    const data = await result.json();
    this.address = data.wallet_address;
    this.isConnected = true;
    
    return this.address;
  }
  
  // MetaMask-compatible methods
  async request(args) {
    return this.provider.request(args);
  }
  
  async sendTransaction(tx) {
    // Apply transaction policies
    const policies = await this.getTransactionPolicies();
    
    if (tx.value > policies.daily_limit) {
      throw new Error('Transaction exceeds daily limit');
    }
    
    if (tx.value > policies.require_2fa_above) {
      await this.request2FA();
    }
    
    return this.provider.request({
      method: 'eth_sendTransaction',
      params: [tx]
    });
  }
}
```

#### Phase 2.2: Update wallet.js to Support Both Wallets
```javascript
// static/js/wallet.js modifications
class ClockchainWallet {
  constructor() {
    this.walletType = localStorage.getItem('wallet_type') || 'coinbase';
    this.adapter = null;
  }
  
  async connect() {
    if (this.walletType === 'coinbase') {
      // Use Coinbase Embedded Wallet
      this.adapter = new CoinbaseEmbeddedWallet();
      await this.adapter.init();
      
      // Get email from Firebase auth
      const email = this.getCurrentUserEmail();
      this.address = await this.adapter.authenticate(email);
      
    } else if (this.walletType === 'metamask') {
      // Fallback to MetaMask (hidden feature)
      if (!window.ethereum) {
        throw new Error('MetaMask not installed');
      }
      this.adapter = window.ethereum;
      const accounts = await this.adapter.request({ 
        method: 'eth_requestAccounts' 
      });
      this.address = accounts[0];
    }
    
    this.isConnected = true;
    this.updateUI();
  }
}
```

#### Phase 2.3: Update Contract Interaction Files
Files to update:
- `betting-contract.js` - Replace `window.ethereum` with `clockchainWallet.adapter`
- `market-blockchain.js` - Use wallet adapter for Web3 provider
- `base-blockchain.js` - Update transaction methods

Example update for betting-contract.js:
```javascript
// Before (MetaMask only)
this.web3 = new Web3(window.ethereum);

// After (Wallet agnostic)
const wallet = window.clockchainWallet;
this.web3 = new Web3(wallet.adapter.provider || wallet.adapter);
```

#### Backend Integration
```python
# services/embedded_wallet.py
class EmbeddedWalletService:
    def __init__(self):
        self.coinbase_client = CoinbaseSDK(
            api_key=os.environ.get('COINBASE_API_KEY'),
            api_secret=os.environ.get('COINBASE_API_SECRET')
        )
    
    def verify_wallet_ownership(self, user_identifier, wallet_address):
        """Verify user owns the embedded wallet"""
        # TEE-secured verification through Coinbase API
        return self.coinbase_client.verify_wallet(
            identifier=user_identifier,
            address=wallet_address
        )
    
    def get_wallet_policy(self, wallet_address):
        """Define transaction policies for user protection"""
        return {
            "daily_limit": 1000,  # $1000 USD daily limit
            "require_2fa_above": 500,  # 2FA for >$500
            "allowed_contracts": [
                PREDICTION_MARKET_ADDRESS,
                GENESIS_NFT_ADDRESS
            ],
            "blocked_addresses": []  # Blacklist known scams
        }
```

### MetaMask Compatibility (Hidden Feature)

#### Toggle Implementation
```javascript
// config/wallet_config.js
const WALLET_CONFIG = {
  enableMetaMask: false,  // Default: disabled
  primaryWallet: 'coinbase-embedded',
  fallbackWallet: null,
  
  // Hidden toggle for power users
  toggleAdvancedMode() {
    if (localStorage.getItem('advanced_user_confirmed')) {
      this.enableMetaMask = true;
      this.fallbackWallet = 'metamask';
    }
  }
};
```

---

### Phase 3: Coinbase Onramp Integration (Detailed)

#### Phase 3.1: Add Onramp SDK
```html
<!-- Add to templates/base.html -->
<script src="https://pay.coinbase.com/sdk/v1/pay-sdk.js"></script>
```

#### Phase 3.2: Create Funding Manager
Create new file: `static/js/funding-manager.js`
```javascript
class FundingManager {
  constructor() {
    this.onramp = null;
    this.userWallet = null;
  }
  
  async init(walletAddress) {
    this.userWallet = walletAddress;
    
    // Initialize Coinbase Onramp
    this.onramp = new window.CBPay({
      appId: window.COINBASE_PROJECT_ID,
      widget: 'buy',
      network: 'base',
      assets: ['USDC'],
      
      onSuccess: (transaction) => {
        this.handleFundingSuccess(transaction);
      },
      
      onExit: (error) => {
        if (error) {
          console.error('Funding error:', error);
          this.showError('Funding failed. Please try again.');
        }
      }
    });
  }
  
  async showFundingOptions(suggestedAmount = 100) {
    // Configure onramp widget
    const options = {
      destinationWalletAddress: this.userWallet,
      presetCryptoAmount: suggestedAmount,
      defaultAsset: 'USDC',
      defaultNetwork: 'base',
      defaultPaymentMethod: 'APPLE_PAY', // or 'ACH_BANK_ACCOUNT'
      
      // Zero-fee configuration for USDC
      handlingRequestedUrls: true,
      preserveUserSession: true
    };
    
    // Open funding widget
    this.onramp.open(options);
  }
  
  async createQuickBuyButtons() {
    // Add quick buy buttons to UI
    const amounts = [50, 100, 250, 500];
    const container = document.getElementById('quick-buy-container');
    
    amounts.forEach(amount => {
      const button = document.createElement('button');
      button.textContent = `Buy $${amount} USDC`;
      button.className = 'btn btn-primary quick-buy';
      button.onclick = () => this.showFundingOptions(amount);
      container.appendChild(button);
    });
  }
  
  handleFundingSuccess(transaction) {
    // Update UI with new balance
    const balanceElement = document.getElementById('wallet-balance');
    if (balanceElement) {
      // Fetch new balance from blockchain
      this.updateBalance();
    }
    
    // Show success message
    this.showSuccess(`Successfully added ${transaction.amount} USDC to your wallet!`);
    
    // Enable betting features
    this.enableBettingFeatures();
  }
  
  async updateBalance() {
    // Query USDC balance on BASE
    const usdcContract = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'; // USDC on BASE
    const balance = await window.clockchainWallet.getTokenBalance(usdcContract);
    
    // Display as USD (hide crypto complexity)
    document.getElementById('wallet-balance').textContent = `$${balance}`;
  }
}
```

#### Phase 3.3: Integrate with Main UI
Update main betting pages to include funding:
```javascript
// Add to market-detail.js or betting pages
async function checkAndPromptFunding() {
  const balance = await getUSDCBalance();
  const requiredAmount = getRequiredBettingAmount();
  
  if (balance < requiredAmount) {
    // Show funding prompt
    const fundingModal = `
      <div class="modal">
        <h3>Add Funds to Bet</h3>
        <p>You need $${requiredAmount} to place this bet.</p>
        <p>Your current balance: $${balance}</p>
        <button onclick="fundingManager.showFundingOptions(${requiredAmount - balance})">
          Add Funds with Apple Pay
        </button>
      </div>
    `;
    showModal(fundingModal);
  }
}
```

### Phase 4: Transaction Signing & Security

#### Phase 4.1: Implement Transaction Policies
```javascript
// static/js/transaction-policies.js
class TransactionPolicyManager {
  constructor() {
    this.policies = {
      daily_limit: 1000,      // $1000 USD daily
      require_2fa_above: 500, // 2FA for >$500
      max_gas_price: 50,      // 50 gwei max
      allowed_contracts: [
        '0x...', // PredictionMarket
        '0x...', // GenesisNFT
      ]
    };
  }
  
  async validateTransaction(tx) {
    // Check daily spending
    const dailySpent = await this.getDailySpending();
    if (dailySpent + tx.value > this.policies.daily_limit) {
      throw new Error('Daily spending limit exceeded');
    }
    
    // Check contract whitelist
    if (!this.policies.allowed_contracts.includes(tx.to)) {
      const approved = await this.requestUserApproval(tx);
      if (!approved) throw new Error('Transaction rejected');
    }
    
    // Check gas price
    if (tx.gasPrice > this.policies.max_gas_price) {
      tx.gasPrice = this.policies.max_gas_price;
    }
    
    return tx;
  }
  
  async request2FA(transaction) {
    // Show 2FA modal
    const modal = new TwoFactorModal();
    const code = await modal.getCode();
    
    // Verify with Firebase
    const verified = await firebase.verify2FA(code);
    if (!verified) throw new Error('2FA verification failed');
    
    return true;
  }
}
```

#### Phase 4.2: Replace MetaMask Transaction Prompts
```javascript
// Update all transaction sending code
// Before: MetaMask popup
const tx = await window.ethereum.request({
  method: 'eth_sendTransaction',
  params: [transaction]
});

// After: Embedded wallet with policies
const policyManager = new TransactionPolicyManager();
const validatedTx = await policyManager.validateTransaction(transaction);

// Show custom confirmation UI
const confirmed = await this.showTransactionConfirmation(validatedTx);
if (!confirmed) throw new Error('Transaction cancelled');

// Send via embedded wallet
const tx = await window.clockchainWallet.sendTransaction(validatedTx);
```

### Phase 5: Production Deployment

#### Phase 5.1: Remove MetaMask Dependencies
```javascript
// config/wallet-config.js
const WALLET_CONFIG = {
  // Remove MetaMask as default
  primaryWallet: 'coinbase-embedded',
  fallbackWallet: null,
  
  // Hide MetaMask option
  showMetaMaskOption: false,
  
  // Production settings
  requireEmailAuth: true,
  require2FA: true,
  enableTestMode: false
};
```

#### Phase 5.2: Update UI Components
- Remove "Connect MetaMask" buttons
- Replace with "Sign In" (email/phone)
- Update wallet status displays
- Add USDC balance displays (show as USD)

#### Phase 5.3: Production Testing Checklist
- [ ] Email authentication flow works
- [ ] Wallet creation after auth
- [ ] Funding via Onramp
- [ ] Transaction signing without popups
- [ ] Policy enforcement (limits, 2FA)
- [ ] Error handling and recovery
- [ ] Mobile responsiveness

---

## 📅 Migration Timeline

### Week 1-2: Foundation (COMPLETED ✅)
- Firebase authentication setup
- Backend wallet service
- API credentials configuration

### Week 3-4: Frontend Migration (CURRENT)
- Create Coinbase wallet adapter
- Update wallet.js for dual support
- Test with existing features

### Week 5-6: Onramp Integration
- Add Coinbase Pay SDK
- Implement funding manager
- Create quick buy UI

### Week 7-8: Security & Polish
- Transaction policies
- 2FA implementation
- Remove MetaMask code

### Week 9-10: Production Launch
- Final testing
- Gradual rollout
- Monitor and optimize

---

## 🧪 Testing Strategy

### Phase Testing Approach
1. **Parallel Testing**: Keep MetaMask working during development
2. **Feature Flags**: Use localStorage to toggle wallet types
3. **Staged Rollout**: Test with internal users first
4. **Monitoring**: Track success rates and errors

### Critical Test Cases
```javascript
// Test suite for wallet migration
describe('Coinbase Embedded Wallet', () => {
  it('should authenticate with email', async () => {
    const email = 'test@example.com';
    const wallet = await authenticateWithEmail(email);
    expect(wallet.address).toBeDefined();
  });
  
  it('should fund wallet via Onramp', async () => {
    const amount = 100; // $100 USDC
    const result = await fundWallet(amount);
    expect(result.success).toBe(true);
  });
  
  it('should sign transactions without popups', async () => {
    const tx = createTestTransaction();
    const signed = await wallet.signTransaction(tx);
    expect(signed).toBeDefined();
  });
});
```

---

## 🎯 Success Metrics

### User Experience Goals
- **Authentication Time**: <30 seconds from landing to wallet
- **Funding Success Rate**: >80% completion
- **Transaction Success**: >95% success rate
- **User Drop-off**: <10% at each step

### Technical Goals
- **Zero MetaMask Dependencies**: Complete removal
- **API Response Time**: <200ms for wallet operations
- **Error Rate**: <0.1% for critical paths
- **Security**: Zero unauthorized transactions

---

## 📝 Implementation Notes

### Current Blockers
1. **Frontend Files**: All use `window.ethereum` directly
2. **Web3 Integration**: Tightly coupled to MetaMask
3. **User Flow**: Assumes MetaMask is installed

### Solutions
1. **Abstraction Layer**: Create wallet adapter pattern
2. **Progressive Migration**: Support both wallets temporarily
3. **Feature Detection**: Check capabilities, not wallet type

### Next Immediate Steps
1. Create `coinbase-wallet.js` adapter
2. Update `wallet.js` to use adapter pattern
3. Test with existing betting flow
4. Add funding UI components
                'limits': {'min': 10, 'max': 10000}
            },
            'secondary': {
                'method': 'coinbase_account',
                'fees': 0,
                'speed': 'instant',
                'limits': {'min': 1, 'max': 50000}
            },
            'tertiary': {
                'method': 'bank_ach',
                'fees': 0,
                'speed': '2-3 days',
                'limits': {'min': 10, 'max': 25000}
            }
        }
        
        # Adjust for regional availability
        if user_region not in APPLE_PAY_REGIONS:
            options['primary'] = options['secondary']
            
        return options
```

---

## 🎲 Betting Experience

### User-Facing Simplification

#### Balance Display
```javascript
// Show USD values, handle USDC in background
const BalanceDisplay = {
  formatBalance(usdcBalance) {
    // Users see "$100" not "100 USDC"
    return `$${usdcBalance.toFixed(2)}`;
  },
  
  convertBetAmount(usdAmount) {
    // Convert USD input to USDC for contract
    return ethers.utils.parseUnits(usdAmount.toString(), 6);
  }
};
```

#### Betting Interface
```javascript
// Frontend: betting-simplified.js
const SimplifiedBetting = {
  async placeBet(marketId, prediction, amountUSD) {
    // User enters "$50" 
    // System handles all crypto complexity
    
    const wallet = await this.getEmbeddedWallet();
    const amountUSDC = this.convertToUSDC(amountUSD);
    
    // Smart contract interaction (hidden from user)
    const tx = await marketContract.placeBet(
      marketId,
      prediction,
      amountUSDC,
      {
        from: wallet.address,
        value: 0,  // USDC, not ETH
        gasLimit: 200000,
        gasPrice: ethers.utils.parseUnits('1', 'gwei')
      }
    );
    
    // Show user-friendly confirmation
    this.showConfirmation({
      message: `You bet $${amountUSD} on "${prediction}"`,
      status: 'pending'
    });
    
    await tx.wait();
    
    this.showConfirmation({
      message: 'Bet placed successfully!',
      status: 'complete'
    });
  }
};
```

### Smart Contract Modifications

#### USDC-Native Contracts
```solidity
// contracts/USDCPredictionMarket.sol
contract USDCPredictionMarket {
    IERC20 public immutable USDC;
    
    constructor(address _usdcAddress) {
        USDC = IERC20(_usdcAddress);  // BASE USDC
    }
    
    function createMarket(
        string memory actor,
        string memory description,
        uint256 betAmountUSDC,  // In USDC (6 decimals)
        uint256 deadline
    ) external returns (uint256 marketId) {
        // Transfer USDC from user
        USDC.transferFrom(msg.sender, address(this), betAmountUSDC);
        
        // Create market (same logic, USDC instead of ETH)
        markets[marketId] = Market({
            creator: msg.sender,
            totalStake: betAmountUSDC,
            currency: "USDC",
            // ... rest of market data
        });
    }
}
```

---

## 🛡️ Security & Compliance

### Policy Engine Configuration

#### Transaction Policies
```javascript
// config/security_policies.js
const SecurityPolicies = {
  // Protect users from mistakes
  transactionLimits: {
    daily: 1000,      // $1000 daily limit
    perTx: 500,       // $500 per transaction
    cooling: 3600     // 1 hour between large bets
  },
  
  // Smart contract whitelist
  allowedContracts: [
    PREDICTION_MARKET_ADDRESS,
    GENESIS_NFT_ADDRESS,
    PAYOUT_MANAGER_ADDRESS
  ],
  
  // Suspicious activity detection
  riskRules: {
    flagRapidTransactions: true,
    blockKnownScams: true,
    require2FAForLarge: true
  }
};
```

#### KYC Avoidance Strategy
```python
# services/compliance_service.py
class ComplianceService:
    def check_transaction_compliance(self, tx_data):
        """
        Verify transaction is purely on-chain to avoid KYC
        - No fiat off-ramps
        - No regulated securities
        - Pure prediction market activity
        """
        compliance_check = {
            'is_prediction_market': True,
            'involves_fiat': False,
            'requires_kyc': False,
            'risk_score': self.calculate_risk_score(tx_data)
        }
        
        # Block if trying to off-ramp to fiat
        if tx_data.get('destination') in FIAT_OFFRAMP_ADDRESSES:
            compliance_check['blocked'] = True
            compliance_check['reason'] = 'Fiat off-ramp requires KYC'
            
        return compliance_check
```

---

## 📊 Migration Strategy

### Phase 1: Backend Preparation (Week 1-2)
- [ ] Integrate Coinbase SDK
- [ ] Create embedded wallet service
- [ ] Implement wallet policy engine
- [ ] Add USDC contract support

### Phase 2: Frontend Integration (Week 2-3)
- [ ] Build email/SMS onboarding flow
- [ ] Integrate Coinbase Onramp SDK
- [ ] Create simplified betting interface
- [ ] Hide MetaMask (make toggleable)

### Phase 3: Smart Contract Updates (Week 3-4)
- [ ] Deploy USDC-native market contracts
- [ ] Update payout manager for USDC
- [ ] Test with embedded wallets
- [ ] Verify gas optimization

### Phase 4: Testing & Launch (Week 4-5)
- [ ] Internal testing with team
- [ ] Beta launch to select users
- [ ] Monitor conversion metrics
- [ ] Full production rollout

---

## 💰 Business Impact

### User Acquisition Improvements
- **Current**: ~2% of visitors create wallets (MetaMask barrier)
- **Projected**: ~35% email signups (similar to web2 apps)
- **Result**: 17.5x increase in user acquisition

### Transaction Volume Impact
- **Simplified Funding**: 10x easier to add funds
- **No Gas Confusion**: Users pay in USD
- **USDC Rewards**: 4.1% APY incentive to hold funds
- **Projected**: 20-50x volume increase within 6 months

### Revenue Projections
With improved UX and 20x volume increase:
- Current: $50k daily volume
- Projected: $1M daily volume
- Platform fees (7%): $70,000 daily
- Genesis NFT holders (1.4%): $14,000 daily

---

## 🔧 Technical Requirements

### Environment Variables
```env
# Coinbase Integration
COINBASE_APP_ID=your_app_id
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_ONRAMP_KEY=your_onramp_key

# Network Configuration
NETWORK=base
USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913
RPC_URL=https://mainnet.base.org

# Security
ENABLE_ADVANCED_MODE=false
REQUIRE_2FA_AMOUNT=500
DAILY_LIMIT_USD=1000
```

### Dependencies
```json
{
  "dependencies": {
    "@coinbase/wallet-sdk": "^4.0.0",
    "@coinbase/onramp-sdk": "^2.0.0",
    "@coinbase/embedded-wallet": "^1.0.0",
    "ethers": "^6.0.0"
  }
}
```

```python
# requirements.txt additions
coinbase-python==2.1.0
coinbase-commerce==1.0.0
web3==6.0.0
```

---

## 📈 Success Metrics

### Key Performance Indicators
1. **User Onboarding Rate**: Target 35% of visitors
2. **Funding Conversion**: Target 50% of registered users
3. **Average Deposit**: Target $100 initial deposit
4. **Daily Active Users**: Target 10x increase
5. **Transaction Volume**: Target 20x increase

### Monitoring Dashboard
```python
# services/metrics_service.py
class MetricsService:
    def track_user_journey(self, user_id):
        return {
            'signup_method': 'email',  # vs 'metamask'
            'funding_method': 'apple_pay',  # Track most popular
            'time_to_first_bet': 300,  # Seconds
            'initial_deposit': 100,  # USD
            'wallet_type': 'embedded',
            'conversion_funnel': {
                'visited': True,
                'signed_up': True,
                'funded': True,
                'placed_bet': True,
                'returned': None  # Track retention
            }
        }
```

---

## 🚀 Implementation Timeline

### Week 1-2: Foundation
- Set up Coinbase developer account
- Integrate SDKs
- Create authentication flow

### Week 3-4: Core Features
- Implement onramp
- Update smart contracts
- Build simplified UI

### Week 5-6: Testing
- Internal testing
- Bug fixes
- Performance optimization

### Week 7-8: Launch
- Gradual rollout (10% → 50% → 100%)
- Monitor metrics
- Iterate based on feedback

---

## 🎯 Success Criteria

### Must Have (Launch Blockers)
- Email/SMS authentication working
- USDC funding via Onramp
- Simplified betting interface
- Hidden MetaMask option

### Should Have (Post-Launch)
- OAuth login (Google/Apple)
- In-app swap feature
- USDC rewards display
- Mobile app

### Nice to Have (Future)
- Multi-chain support
- Fiat off-ramp (with KYC)
- Advanced trading features
- Social features

---

## 📝 Conclusion

By integrating Coinbase's embedded wallet and onramp solutions, Proteus can achieve mainstream adoption while maintaining its decentralized, on-chain architecture. Users get a familiar web2 experience while participating in a fully decentralized prediction market, bypassing traditional KYC requirements through pure crypto operations.

The key insight: Make crypto invisible to users while keeping everything on-chain. This approach could increase user acquisition by 17.5x and transaction volume by 20-50x, positioning Proteus as the most accessible prediction market platform in the crypto space.

---

*Document Version: 1.0*  
*Last Updated: January 28, 2025*  
*Next Review: February 15, 2025*