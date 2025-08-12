const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🔐 Setting up BASE Sepolia Test Wallet...\n");
  
  // Create a new random wallet
  const wallet = ethers.Wallet.createRandom();
  
  console.log("✅ New test wallet created!");
  console.log("=====================================");
  console.log("Address:", wallet.address);
  console.log("Private Key:", wallet.privateKey);
  console.log("=====================================\n");
  
  // Save wallet info to a file (git-ignored)
  const walletInfo = {
    address: wallet.address,
    privateKey: wallet.privateKey,
    network: "BASE Sepolia",
    chainId: 84532,
    created: new Date().toISOString()
  };
  
  const walletPath = path.join(__dirname, "..", ".test-wallet.json");
  fs.writeFileSync(walletPath, JSON.stringify(walletInfo, null, 2));
  console.log("💾 Wallet info saved to .test-wallet.json (git-ignored)\n");
  
  // Create .env file if it doesn't exist
  const envPath = path.join(__dirname, "..", ".env");
  let envContent = "";
  
  if (fs.existsSync(envPath)) {
    envContent = fs.readFileSync(envPath, "utf8");
  }
  
  // Update or add the DEPLOYER_PRIVATE_KEY
  if (envContent.includes("DEPLOYER_PRIVATE_KEY=")) {
    envContent = envContent.replace(/DEPLOYER_PRIVATE_KEY=.*/, `DEPLOYER_PRIVATE_KEY=${wallet.privateKey}`);
  } else {
    envContent += `\n# Test wallet for BASE Sepolia deployment\nDEPLOYER_PRIVATE_KEY=${wallet.privateKey}\n`;
  }
  
  fs.writeFileSync(envPath, envContent);
  console.log("✅ Updated .env with DEPLOYER_PRIVATE_KEY\n");
  
  // Instructions for getting testnet ETH
  console.log("📋 NEXT STEPS:");
  console.log("=====================================");
  console.log("1. Get BASE Sepolia ETH from faucets:\n");
  console.log("   Option A: Coinbase Wallet Faucet (Recommended)");
  console.log("   https://portal.cdp.coinbase.com/products/faucet");
  console.log("   - Sign in with Coinbase account");
  console.log("   - Select BASE Sepolia network");
  console.log("   - Enter wallet address:", wallet.address);
  console.log("   - Request 0.1 ETH (usually instant)\n");
  
  console.log("   Option B: Alchemy Faucet");
  console.log("   https://www.alchemy.com/faucets/base-sepolia");
  console.log("   - Create free Alchemy account");
  console.log("   - Enter wallet address:", wallet.address);
  console.log("   - Complete captcha\n");
  
  console.log("   Option C: QuickNode Faucet");
  console.log("   https://faucet.quicknode.com/base/sepolia");
  console.log("   - Connect wallet or paste address");
  console.log("   - Limited to 0.05 ETH per day\n");
  
  console.log("2. Check your balance:");
  console.log("   npm run check-balance\n");
  
  console.log("3. Deploy Genesis NFT contracts:");
  console.log("   npm run deploy:genesis-testnet\n");
  
  console.log("4. View on Basescan:");
  console.log(`   https://sepolia.basescan.org/address/${wallet.address}\n`);
  
  console.log("⚠️  IMPORTANT: Keep your private key secure!");
  console.log("This is a test wallet for BASE Sepolia only.\n");
  
  // Check current provider connection
  console.log("🔍 Checking BASE Sepolia connection...");
  try {
    const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");
    const blockNumber = await provider.getBlockNumber();
    console.log("✅ Connected to BASE Sepolia - Block #" + blockNumber);
    
    const balance = await provider.getBalance(wallet.address);
    console.log("Current balance:", ethers.formatEther(balance), "ETH");
    
    if (balance > 0n) {
      console.log("✅ Wallet already has funds! Ready to deploy.");
    } else {
      console.log("⚠️  Wallet needs funding. Use one of the faucets above.");
    }
  } catch (error) {
    console.log("❌ Error connecting to BASE Sepolia:", error.message);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });