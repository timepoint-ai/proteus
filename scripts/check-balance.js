const { ethers } = require("ethers");
const fs = require("fs");
const path = require("path");
require("dotenv").config();

async function main() {
  console.log("💰 Checking BASE Sepolia Wallet Balance...\n");
  
  // Get wallet from environment or test wallet file
  let privateKey = process.env.DEPLOYER_PRIVATE_KEY;
  let walletAddress;
  
  if (!privateKey) {
    // Try to load from test wallet file
    const walletPath = path.join(__dirname, "..", ".test-wallet.json");
    if (fs.existsSync(walletPath)) {
      const walletInfo = JSON.parse(fs.readFileSync(walletPath, "utf8"));
      privateKey = walletInfo.privateKey;
      walletAddress = walletInfo.address;
      console.log("📂 Loaded wallet from .test-wallet.json");
    } else {
      console.log("❌ No wallet found! Run: npm run setup:wallet");
      process.exit(1);
    }
  }
  
  // Connect to BASE Sepolia
  const provider = new ethers.JsonRpcProvider("https://sepolia.base.org");
  
  try {
    const wallet = new ethers.Wallet(privateKey, provider);
    walletAddress = wallet.address;
    
    // Get balance
    const balance = await provider.getBalance(walletAddress);
    const balanceInEth = ethers.formatEther(balance);
    
    // Get current block
    const blockNumber = await provider.getBlockNumber();
    
    // Get gas price
    const gasPrice = await provider.getFeeData();
    const gasPriceGwei = ethers.formatUnits(gasPrice.gasPrice, "gwei");
    
    console.log("🔗 Network: BASE Sepolia");
    console.log("📦 Current Block:", blockNumber);
    console.log("⛽ Gas Price:", gasPriceGwei, "gwei\n");
    
    console.log("=====================================");
    console.log("Wallet Address:", walletAddress);
    console.log("Balance:", balanceInEth, "ETH");
    console.log("=====================================\n");
    
    // Calculate deployment costs
    const deploymentGas = 2527892n; // From our tests
    const mintingGas = 907882n; // For 10 NFTs
    const totalGas = deploymentGas + mintingGas;
    const estimatedCost = (totalGas * gasPrice.gasPrice) / 10n**18n;
    
    console.log("📊 Estimated Deployment Costs:");
    console.log("- Contract Deployment:", (deploymentGas * gasPrice.gasPrice / 10n**18n).toString(), "ETH");
    console.log("- Minting 10 NFTs:", (mintingGas * gasPrice.gasPrice / 10n**18n).toString(), "ETH");
    console.log("- Total Estimated:", ethers.formatEther(totalGas * gasPrice.gasPrice), "ETH\n");
    
    if (balance === 0n) {
      console.log("⚠️  WALLET NEEDS FUNDING!");
      console.log("\nGet BASE Sepolia ETH from:");
      console.log("1. https://portal.cdp.coinbase.com/products/faucet");
      console.log("2. https://www.alchemy.com/faucets/base-sepolia");
      console.log("3. https://faucet.quicknode.com/base/sepolia\n");
      console.log("Copy this address:", walletAddress);
    } else if (balance < totalGas * gasPrice.gasPrice) {
      console.log("⚠️  Balance might be insufficient for full deployment");
      console.log("Consider getting more testnet ETH");
    } else {
      console.log("✅ Wallet has sufficient balance for deployment!");
      console.log("\nReady to deploy with: npm run deploy:genesis-testnet");
    }
    
    console.log("\n🔍 View on Basescan:");
    console.log(`https://sepolia.basescan.org/address/${walletAddress}`);
    
  } catch (error) {
    console.log("❌ Error:", error.message);
    if (error.message.includes("invalid private key")) {
      console.log("\n⚠️  Invalid private key format");
      console.log("Run: npm run setup:wallet");
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });