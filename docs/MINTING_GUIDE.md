# How to Mint Genesis NFTs - Complete Guide

## Current Status
✅ Wallet has ETH (0.0001 ETH on BASE Sepolia)
❌ Contracts NOT deployed yet
⚠️ Need more ETH for deployment (need ~0.005 ETH, have 0.0001 ETH)

## Step 1: Get More Test ETH (Required)
Your wallet needs about 0.005 ETH to deploy. You only have 0.0001 ETH.

**Get more test ETH:**
1. Go to: https://portal.cdp.coinbase.com/products/faucet
2. Connect your MetaMask (or paste address: 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF)
3. Select BASE Sepolia
4. Request 0.1 ETH (you can request multiple times)

## Step 2: Deploy the Contracts
Once you have enough ETH (at least 0.005), run:
```bash
npx hardhat run scripts/deploy-genesis-testnet.js --network baseSepolia
```

This will deploy:
- GenesisNFT contract
- DistributedPayoutManager contract
- MockPredictionMarket contract

## Step 3: Mint Your NFTs
After successful deployment, run:
```bash
npx hardhat run scripts/mint-test-nfts.js --network baseSepolia
```

This will mint 15 test NFTs to different addresses.

## For BASE Mainnet (Real NFTs - Future)

### When We're Ready for Mainnet:
1. Complete all testing on testnet
2. Get security audit
3. Deploy to BASE mainnet (different contracts)

### How to Get Real NFTs:
1. **Use Your Real Wallet** (not the test wallet)
2. **Have Real ETH on BASE** (~$10-20 for gas)
3. **Wait for Announcement** - We'll share the minting website
4. **Mint Your NFTs** (max 10 per wallet, 100 total supply)
5. **Cost**: FREE! You only pay gas (~$2-5 per mint)

### What You Get:
- Each Genesis NFT = 0.002% of platform revenue
- Maximum 10 NFTs per wallet = 0.02% of platform revenue
- Automatic distribution forever
- No admin control - truly decentralized

## Quick Commands Reference

### Check Balance:
```bash
node scripts/check-balance.js
```

### Deploy (after funding):
```bash
npx hardhat run scripts/deploy-genesis-testnet.js --network baseSepolia
```

### Mint NFTs (after deploying):
```bash
npx hardhat run scripts/mint-test-nfts.js --network baseSepolia
```

### View on Basescan:
After deployment, contracts will be viewable at:
https://sepolia.basescan.org/address/[CONTRACT_ADDRESS]

## Current Issue
The deployment failed because you need more test ETH. Your wallet has 0.0001 ETH but needs about 0.005 ETH for deployment. Get more from the faucet first!