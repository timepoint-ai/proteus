# Genesis NFT Test Rig Setup Guide 🎯

## Overview
Complete test infrastructure for deploying and testing Genesis NFTs on BASE Sepolia testnet.

## Test Wallet Created ✅

Your new BASE Sepolia test wallet:
```
Address: 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF
Network: BASE Sepolia (Chain ID: 84532)
Status: Awaiting funding
```

## Quick Start Commands

### 1. Check Wallet Balance
```bash
node scripts/check-balance.js
```

### 2. Deploy Genesis NFT Contracts
```bash
npx hardhat run scripts/deploy-genesis-testnet.js --network baseSepolia
```

### 3. Mint Test NFTs
```bash
npx hardhat run scripts/mint-test-nfts.js --network baseSepolia
```

### 4. Run Integration Tests
```bash
npx hardhat run scripts/test-genesis-integration.js --network hardhat
```

## Get Test ETH (Required!)

Your wallet needs BASE Sepolia ETH to deploy contracts. Choose one:

### Option A: Coinbase Wallet Faucet (Recommended - Instant)
1. Visit: https://portal.cdp.coinbase.com/products/faucet
2. Sign in with Coinbase account
3. Select BASE Sepolia network
4. Paste address: `0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF`
5. Request 0.1 ETH

### Option B: Alchemy Faucet (Reliable)
1. Visit: https://www.alchemy.com/faucets/base-sepolia
2. Create free Alchemy account
3. Paste address: `0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF`
4. Complete captcha

### Option C: QuickNode Faucet (No signup)
1. Visit: https://faucet.quicknode.com/base/sepolia
2. Paste address: `0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF`
3. Request ETH (0.05 ETH daily limit)

## Estimated Costs

| Operation | Gas Units | Cost @ Current Price |
|-----------|-----------|---------------------|
| Deploy Contracts | ~2.5M | ~0.0025 ETH |
| Mint 10 NFTs | ~900k | ~0.0009 ETH |
| Single Transfer | ~90k | ~0.00009 ETH |
| **Total Needed** | **~3.5M** | **~0.0035 ETH** |

## Test NFT Distribution Plan

The test minting script will distribute NFTs as follows:
- 5 NFTs to deployer wallet
- 3 NFTs to test address #1
- 2 NFTs to test address #2  
- 5 NFTs to test address #3
- **Total: 15 test NFTs**

## What Gets Deployed

### 1. GenesisNFT Contract
- 100 fixed-supply NFTs
- On-chain SVG art generation
- No admin functions
- Auto-finalization after 24 hours

### 2. DistributedPayoutManager
- Handles 0.2% platform fee distribution
- 0.002% per Genesis NFT holder
- Automatic reward distribution

### 3. MockPredictionMarket
- Simulates market operations for testing
- Allows fee generation testing

## Verification Tools

### View on Basescan
- Wallet: https://sepolia.basescan.org/address/0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF
- After deployment, contracts will be viewable at their deployed addresses

### Check Deployment Status
```bash
cat deployments/genesis-phase1-testnet.json
```

## Test Scenarios

### 1. Basic Functionality
- ✅ Deploy all contracts
- ✅ Mint initial batch of NFTs
- ✅ Verify SVG generation
- ✅ Test NFT transfers

### 2. Edge Cases
- ✅ Attempt to mint > 10 NFTs (should fail)
- ✅ Try minting to zero address (should fail)
- ✅ Verify auto-finalization after 24 hours
- ✅ Test minting after max supply reached

### 3. Fee Distribution
- ✅ Create mock market volume
- ✅ Calculate expected distributions
- ✅ Verify Genesis holders receive 0.002% each

## Security Checklist

- [x] No owner/admin functions in GenesisNFT
- [x] Fixed supply of 100 NFTs
- [x] Auto-finalization mechanism
- [x] Rewards follow NFT ownership
- [x] No ability to pause or upgrade

## Files Created

1. **scripts/setup-test-wallet.js** - Creates new test wallet
2. **scripts/check-balance.js** - Checks wallet balance and estimates costs
3. **scripts/mint-test-nfts.js** - Mints test NFTs to multiple addresses
4. **scripts/deploy-genesis-testnet.js** - Deploys to BASE Sepolia
5. **scripts/test-genesis-integration.js** - Comprehensive test suite
6. **.test-wallet.json** - Stores test wallet info (git-ignored)

## Troubleshooting

### "No wallet found"
Run: `node scripts/setup-test-wallet.js`

### "Insufficient balance"
Get testnet ETH from one of the faucets above

### "Transaction failed"
Check gas price: `node scripts/check-balance.js`

### "Contract not found"
Deploy first: `npx hardhat run scripts/deploy-genesis-testnet.js --network baseSepolia`

## Next Steps After Testing

1. **External Audit**: Run Slither/Mythril security analysis
2. **Community Testing**: Share testnet addresses for community validation
3. **Bug Bounty**: Set up rewards for finding issues
4. **Mainnet Prep**: Prepare production deployment strategy

## Support

- View deployment docs: `docs/PHASE_1_COMPLETE_TESTED.md`
- Check governance plan: `docs/GOVERNANCE.md`
- Review test results: Run integration tests

---

**Status: Test rig fully configured and ready! Just need to fund the wallet with BASE Sepolia ETH to begin deployment.**