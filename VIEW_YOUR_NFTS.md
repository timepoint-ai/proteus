# How to View Your Genesis NFTs

## ✅ Your NFTs Are Confirmed On-Chain

**You own: 15 Genesis NFTs**
- Contract: `0x1A5D4475881B93e876251303757E60E524286A24`
- Your wallet (dev1): `0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF`
- Token IDs: #1 through #15

## Method 1: View on Basescan (BEST)
Click this link to see your NFTs:
https://sepolia.basescan.org/token/0x1A5D4475881B93e876251303757E60E524286A24?a=0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF

## Method 2: Add to MetaMask Manually

1. Open MetaMask
2. Make sure you're on **BASE Sepolia** network
3. Switch to the **dev1 wallet** (0x2b5fB...6b6EF)
4. Click "NFTs" tab
5. Click "Import NFTs"
6. Enter:
   - Contract address: `0x1A5D4475881B93e876251303757E60E524286A24`
   - Token ID: `1` (then repeat for 2, 3, etc.)

## Method 3: View with Script
Run this anytime to check your NFTs:
```bash
npx hardhat run scripts/check-nfts.js --network baseSepolia
```

## Why They Don't Show Automatically:

| Platform | Reason |
|----------|--------|
| **MetaMask** | Doesn't auto-detect testnet NFTs |
| **OpenSea** | Only supports mainnet, not BASE Sepolia |
| **Coinbase Wallet** | Limited testnet NFT support |

## Important Notes:

- **These are TEST NFTs** on BASE Sepolia testnet
- **Real NFTs** will be on BASE mainnet (future)
- **Mainnet NFTs** will show on OpenSea automatically
- **Your test NFTs** prove the system works!

## What Your NFTs Look Like:
Each Genesis NFT has:
- Unique on-chain SVG art
- Token ID (#1-#15 are yours)
- 0.002% platform revenue share
- Fully decentralized ownership

## For Mainnet (Future):
When we deploy to mainnet:
1. NFTs will appear in wallets automatically
2. OpenSea will display them with images
3. You'll use a different wallet (not test wallet)
4. Real ETH required (not test ETH)