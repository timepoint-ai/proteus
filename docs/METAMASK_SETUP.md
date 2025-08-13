# MetaMask Setup Guide for Test Wallet

## Your Test Wallet Details
```
Address: 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF
Private Key: Already stored in DEPLOYER_PRIVATE_KEY secret
Network: BASE Sepolia (testnet)
```

## Adding Test Wallet to MetaMask

### Step 1: Import the Wallet
1. Open MetaMask browser extension
2. Click your account icon (top-right circle)
3. Select "Import Account"
4. Choose "Private Key" as import type
5. Paste the private key from your Replit secret (DEPLOYER_PRIVATE_KEY)
6. Click "Import"
7. Your test wallet will appear as a new account

### Step 2: Add BASE Sepolia Network
1. In MetaMask, click the network dropdown (top-left)
2. Click "Add Network" or "Add Network Manually"
3. Enter these details:
   - **Network Name**: BASE Sepolia
   - **RPC URL**: https://sepolia.base.org
   - **Chain ID**: 84532
   - **Currency Symbol**: ETH
   - **Block Explorer**: https://sepolia.basescan.org
4. Click "Save"
5. Switch to BASE Sepolia network

### Step 3: Get Test ETH
1. Visit: https://portal.cdp.coinbase.com/products/faucet
2. Select BASE Sepolia
3. Your wallet address will auto-fill if MetaMask is connected
4. Request 0.1 ETH (free testnet tokens)

## Test NFTs vs Real NFTs

### Test NFTs (BASE Sepolia - Current Stage)
- **Network**: BASE Sepolia testnet
- **Cost**: Free (uses test ETH)
- **Purpose**: Testing and validation
- **Value**: No real value, for testing only
- **Wallet**: Test wallet (0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF)

### Real NFTs (BASE Mainnet - Future)
When we deploy to mainnet, here's what you'll need:

1. **Real Wallet Setup**
   - Use your personal MetaMask wallet (NOT the test wallet)
   - Add BASE Mainnet to MetaMask:
     - Network Name: BASE
     - RPC URL: https://mainnet.base.org
     - Chain ID: 8453
     - Currency Symbol: ETH
     - Block Explorer: https://basescan.org

2. **Funding Requirements**
   - Real ETH on BASE network (about $10-20 for gas)
   - Bridge ETH from Ethereum to BASE using: https://bridge.base.org

3. **Getting Your Genesis NFTs**
   - After mainnet deployment, we'll announce the contract address
   - Visit the minting website or interact directly with the contract
   - Each wallet can mint up to 10 NFTs (out of 100 total)
   - Cost: Only gas fees (NFTs are free to mint)
   - Each NFT = 0.002% of platform revenue forever

## Security Notes

### Test Wallet (Current)
- ✅ Safe to share address: 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF
- ⚠️ Keep private key secret (already in Replit secrets)
- ✅ Only for testnet use
- ✅ No real value at risk

### Real Wallet (Mainnet)
- ⚠️ NEVER share your real wallet's private key
- ⚠️ NEVER store real wallet private key in code
- ✅ Use hardware wallet if possible (Ledger, Trezor)
- ✅ Always verify contract addresses before minting

## Replit Secrets Status

Your test wallet is already configured:
- **DEPLOYER_PRIVATE_KEY**: Contains test wallet private key ✅
- This is the wallet we just created for BASE Sepolia testing
- Address: 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF

No additional secrets needed for test deployment!

## Next Steps

### For Testing (Now)
1. Import test wallet to MetaMask using steps above
2. Add BASE Sepolia network
3. Get test ETH from faucet
4. Deploy contracts: `npx hardhat run scripts/deploy-genesis-testnet.js --network baseSepolia`
5. Mint test NFTs: `npx hardhat run scripts/mint-test-nfts.js --network baseSepolia`

### For Mainnet (Later)
1. Complete all testing on Sepolia
2. Get security audit
3. Prepare mainnet deployment wallet (different from test)
4. Announce minting date to community
5. Deploy to BASE mainnet
6. Open minting for 24 hours or until 100 NFTs minted

## FAQ

**Q: Can I use the same wallet for testnet and mainnet?**
A: You can, but it's better to use separate wallets for security.

**Q: How much will real NFTs cost?**
A: Free to mint! You only pay gas fees (usually $1-5 per mint on BASE).

**Q: When will mainnet launch?**
A: After successful testnet validation and security audit.

**Q: How many NFTs can I get?**
A: Maximum 10 per wallet, 100 total supply.

**Q: What benefits do NFT holders get?**
A: 0.002% of all platform volume, distributed automatically, forever.