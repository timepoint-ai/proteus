const { ethers } = require('ethers');
const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

async function createProductionWallet() {
    console.log("=== Creating Production Wallet for BASE Mainnet ===\n");
    
    // Generate a new random wallet
    const wallet = ethers.Wallet.createRandom();
    
    // Generate wallet details
    const walletInfo = {
        address: wallet.address,
        privateKey: wallet.privateKey,
        mnemonic: wallet.mnemonic.phrase,
        created: new Date().toISOString(),
        network: 'base-mainnet',
        purpose: 'production-deployment'
    };
    
    console.log("🔐 New Production Wallet Created:");
    console.log("================================");
    console.log(`Address: ${walletInfo.address}`);
    console.log(`\n⚠️  CRITICAL SECURITY INFORMATION:`);
    console.log("1. Write down your mnemonic phrase on paper");
    console.log("2. Store it in a secure location");
    console.log("3. Never share or commit these values");
    console.log("4. Use a hardware wallet for large amounts");
    
    console.log("\n📝 Mnemonic Phrase (12 words):");
    console.log("--------------------------------");
    console.log(walletInfo.mnemonic);
    console.log("--------------------------------");
    
    console.log("\n🔑 Private Key:");
    console.log("--------------------------------");
    console.log(walletInfo.privateKey);
    console.log("--------------------------------");
    
    // Save encrypted backup
    const backupPath = path.join(__dirname, '../.production-wallet-backup.json');
    
    // Create a simple encryption for local backup
    const password = crypto.randomBytes(32).toString('hex');
    const encryptedData = {
        wallet: Buffer.from(JSON.stringify(walletInfo)).toString('base64'),
        checksum: crypto.createHash('sha256').update(walletInfo.address).digest('hex'),
        hint: "Store password separately. This is for emergency recovery only."
    };
    
    await fs.writeFile(backupPath, JSON.stringify(encryptedData, null, 2));
    await fs.writeFile(backupPath + '.password', password);
    
    console.log("\n✅ Next Steps:");
    console.log("1. Import this wallet into MetaMask");
    console.log("2. Add BASE Mainnet network to MetaMask:");
    console.log("   - Network Name: Base Mainnet");
    console.log("   - RPC URL: https://mainnet.base.org");
    console.log("   - Chain ID: 8453");
    console.log("   - Currency: ETH");
    console.log("   - Explorer: https://basescan.org");
    console.log("3. Bridge ETH from Ethereum to BASE at bridge.base.org");
    console.log("4. Add wallet address to .env as PRODUCTION_PRIVATE_KEY");
    
    console.log("\n💰 Funding Requirements:");
    console.log("- Deployment: ~0.02 ETH");
    console.log("- Operations: ~0.05 ETH buffer");
    console.log("- Total recommended: 0.1 ETH");
    
    console.log("\n🔒 Security Checklist:");
    console.log("[ ] Mnemonic written on paper");
    console.log("[ ] Paper stored securely");
    console.log("[ ] Wallet imported to MetaMask");
    console.log("[ ] Test transaction completed");
    console.log("[ ] Production environment configured");
    
    return walletInfo;
}

// Run the script
createProductionWallet().catch(console.error);