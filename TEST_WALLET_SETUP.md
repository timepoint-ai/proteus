# TEST WALLET SETUP GUIDE

## Overview

This guide explains how to configure test wallets for the Clockchain E2E test manager on BASE Sepolia testnet. These wallets are essential for running automated tests of the prediction market functionality.

## Automated Wallet Setup (Recommended)

The Test Manager now includes automated wallet setup functionality:

1. Go to the Test Manager Dashboard (`/test-manager`)
2. In the "Test Management" section, click **"Setup Test Wallets"**
3. The system will automatically:
   - Generate a main test wallet and 3 oracle wallets
   - Configure environment variables
   - Save wallet configuration to `.test_wallets.json`
   - Validate all addresses
   - Check wallet balances
   - Provide funding instructions

This is the recommended approach as it ensures proper configuration and security.

## Required Wallet Configuration

### 1. TEST_WALLET_ADDRESS
**Purpose**: Main wallet used to create prediction markets and initial submissions  
**Format**: `0x` followed by 40 hexadecimal characters  
**Example**: `0x742d35Cc6634C0532925a3b844Bc9e7595f2BDaE`  
**Usage**: This wallet pays for market creation transactions and initial stakes

### 2. TEST_WALLET_PRIVATE_KEY
**Purpose**: Private key for signing transactions from the main test wallet  
**Format**: `0x` followed by 64 hexadecimal characters  
**Example**: `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`  
**SECURITY**: Never use a private key from a wallet with real funds!

### 3. TEST_ORACLE_WALLETS
**Purpose**: Array of oracle wallet addresses for submitting X.com verification data  
**Format**: JSON array of wallet addresses  
**Example**: `["0x70997970C51812dc3A010C7d01b50e0d17dc79C8", "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"]`  
**Requirement**: Minimum 3 oracles for consensus

### 4. TEST_NETWORK_RPC (Optional)
**Purpose**: Custom RPC endpoint for BASE Sepolia  
**Default**: `https://base-sepolia.g.alchemy.com/public`  
**Custom Example**: `https://base-sepolia.g.alchemy.com/v2/YOUR-API-KEY`  
**Note**: Public endpoint works but may be rate-limited

### 5. TEST_CHAIN_ID (Optional)
**Purpose**: Chain ID verification  
**Value**: `84532` (BASE Sepolia)  
**Note**: Do NOT use 11155111 (that's Ethereum Sepolia)

## Step-by-Step Setup Instructions

### Step 1: Generate Test Wallets

You can generate test wallets using any of these methods:

#### Option A: Using ethers.js (Recommended)
```javascript
// Run in browser console or Node.js
const { ethers } = require('ethers');
const wallet = ethers.Wallet.createRandom();
console.log('Address:', wallet.address);
console.log('Private Key:', wallet.privateKey);
```

#### Option B: Using Web3.js
```javascript
const Web3 = require('web3');
const web3 = new Web3();
const account = web3.eth.accounts.create();
console.log('Address:', account.address);
console.log('Private Key:', account.privateKey);
```

#### Option C: Using MetaMask
1. Install MetaMask browser extension
2. Create a new account
3. Export private key (Settings → Account Details → Export Private Key)
4. **Important**: Only use accounts created specifically for testing

### Step 2: Get BASE Sepolia Test Tokens

You need BASE Sepolia ETH to pay for transactions. Get free test tokens from:

1. **BASE Sepolia Faucet**: https://faucet.quicknode.com/base/sepolia
   - Requires 0.001 ETH on mainnet
   - Provides 0.05 BASE Sepolia ETH

2. **Coinbase Faucet**: https://faucet.coinbase.com/base-sepolia
   - Requires Coinbase account
   - Provides 0.1 BASE Sepolia ETH daily

3. **Bridge from Ethereum Sepolia**:
   - Get Sepolia ETH from: https://sepoliafaucet.com/
   - Bridge to BASE Sepolia: https://bridge.base.org/

### Step 3: Configure Replit Secrets

1. Go to your Replit project
2. Click the "Secrets" tab (🔐 icon)
3. Add each secret:

```
TEST_WALLET_ADDRESS = 0x742d35Cc6634C0532925a3b844Bc9e7595f2BDaE
TEST_WALLET_PRIVATE_KEY = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
TEST_ORACLE_WALLETS = ["0x70997970C51812dc3A010C7d01b50e0d17dc79C8", "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"]
TEST_NETWORK_RPC = https://base-sepolia.g.alchemy.com/public
TEST_CHAIN_ID = 84532
```

### Step 4: Fund Your Test Wallets

Ensure each wallet has sufficient BASE Sepolia ETH:
- Main wallet: At least 0.1 BASE ETH
- Oracle wallets: At least 0.01 BASE ETH each

### Step 5: Verify Configuration

Run the wallet connection test in the Test Manager:
1. Navigate to `/test-manager/login`
2. Enter your TEST_MANAGER_PASSCODE
3. Click "Run Test" → "Wallet Connection"
4. Verify all wallets are properly configured

## Example Test Wallet Generation Script

Here's a complete script to generate all required test wallets:

```javascript
// generate-test-wallets.js
const { ethers } = require('ethers');

// Generate main test wallet
const mainWallet = ethers.Wallet.createRandom();
console.log('TEST_WALLET_ADDRESS =', mainWallet.address);
console.log('TEST_WALLET_PRIVATE_KEY =', mainWallet.privateKey);
console.log('');

// Generate oracle wallets
const oracleWallets = [];
for (let i = 0; i < 3; i++) {
    const oracle = ethers.Wallet.createRandom();
    oracleWallets.push(oracle.address);
    console.log(`Oracle ${i + 1} Address:`, oracle.address);
    console.log(`Oracle ${i + 1} Private Key:`, oracle.privateKey);
    console.log('');
}

console.log('TEST_ORACLE_WALLETS =', JSON.stringify(oracleWallets));
console.log('TEST_NETWORK_RPC = https://base-sepolia.g.alchemy.com/public');
console.log('TEST_CHAIN_ID = 84532');
```

## Security Best Practices

1. **Never use mainnet wallets** for testing
2. **Create dedicated test wallets** that are only used for this purpose
3. **Keep private keys secure** even for test wallets
4. **Use minimal funds** - only what's needed for testing
5. **Rotate test wallets** periodically
6. **Don't commit secrets** to version control

## Troubleshooting

### "Invalid wallet address" error
- Ensure addresses start with `0x`
- Verify addresses are exactly 42 characters (0x + 40 hex)
- Check for typos or extra spaces

### "Insufficient funds" error
- Get more BASE Sepolia ETH from faucets
- Check wallet balance: https://sepolia.basescan.org/
- Ensure you're on BASE Sepolia, not Ethereum Sepolia

### "Wrong chain ID" error
- Verify TEST_CHAIN_ID is set to `84532`
- Check your RPC endpoint is for BASE Sepolia
- Don't use Ethereum Sepolia (11155111)

### "Rate limit exceeded" error
- Use a custom RPC endpoint with API key
- Reduce test frequency
- Consider using multiple RPC endpoints

## Test Wallet Roles

1. **Market Creator Wallet**: Creates prediction markets
2. **Bettor Wallets**: Place bets on submissions
3. **Oracle Wallets**: Submit X.com verification data
4. **Payout Receiver**: Receives winnings (can be same as bettor)

## Next Steps

Once your wallets are configured:
1. Run the E2E test suite at `/test-manager`
2. Monitor transactions on BASE Sepolia explorer
3. Check gas usage and optimize if needed
4. Report any issues with wallet configuration