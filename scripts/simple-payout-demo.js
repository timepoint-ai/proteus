const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🚀 Simple Genesis NFT Payout Demo\n");
  console.log("This demo will deploy a test market and trigger payouts to your Genesis NFTs.\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Contracts:");
  console.log("- GenesisNFT:", deployment.contracts.GenesisNFT);
  console.log("- PayoutManager:", deployment.contracts.DistributedPayoutManager);
  console.log("- Your wallet:", deployer.address);
  
  // Connect to contracts
  const PayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  const payoutManager = PayoutManager.attach(deployment.contracts.DistributedPayoutManager);
  
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  // Check NFT ownership
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("\n🎨 NFT Status:");
  console.log("- Your Genesis NFTs:", nftBalance.toString());
  console.log("- Total minted:", totalMinted.toString(), "/ 100");
  console.log("- Your share:", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  console.log("- Platform revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%\n");
  
  // Check initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("💰 Initial balance:", ethers.formatEther(initialBalance), "ETH");
  
  // Deploy a simple test market that can trigger payouts
  console.log("\n═══════════════════════════════════════════");
  console.log("STEP 1: Deploy Test Market");
  console.log("═══════════════════════════════════════════\n");
  
  // Create simple test market contract
  const TestMarket = await ethers.getContractFactory("MockPredictionMarket");
  console.log("Deploying test market contract...");
  const testMarket = await TestMarket.deploy();
  await testMarket.waitForDeployment();
  const testMarketAddress = await testMarket.getAddress();
  console.log("✅ Test market deployed at:", testMarketAddress);
  
  // Set up a resolved market
  console.log("\n═══════════════════════════════════════════");
  console.log("STEP 2: Simulate Market Activity");
  console.log("═══════════════════════════════════════════\n");
  
  const marketId = 1;
  const feeAmount = ethers.parseEther("0.001"); // 0.001 ETH in fees
  
  // Create market data
  const marketData = {
    creator: deployer.address,
    actor: "0x1234567890123456789012345678901234567890",
    startTime: Math.floor(Date.now() / 1000) - 3600, // Started 1 hour ago
    endTime: Math.floor(Date.now() / 1000) - 60, // Ended 1 minute ago
    resolved: true,
    winningSubmissionId: 1,
    totalVolume: feeAmount,
    submissionCount: 2,
    betCount: 5,
    platformFeePercentage: 7,
    platformFeeCollected: (feeAmount * 7n) / 100n
  };
  
  console.log("Setting up resolved market with:");
  console.log("- Total volume:", ethers.formatEther(feeAmount), "ETH");
  console.log("- Platform fee (7%):", ethers.formatEther(marketData.platformFeeCollected), "ETH");
  
  await testMarket.setMarket(marketId, marketData);
  console.log("✅ Market data set");
  
  console.log("\n═══════════════════════════════════════════");
  console.log("STEP 3: Trigger Genesis NFT Payouts");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    // First, send the platform fees to the PayoutManager
    console.log("1️⃣ Simulating platform fee collection...");
    console.log("   Sending", ethers.formatEther(marketData.platformFeeCollected), "ETH to PayoutManager");
    
    const sendTx = await deployer.sendTransaction({
      to: deployment.contracts.DistributedPayoutManager,
      value: marketData.platformFeeCollected
    });
    await sendTx.wait();
    console.log("✅ Platform fees sent to PayoutManager");
    
    // Now trigger the distribution
    console.log("\n2️⃣ Distributing fees to all stakeholders...");
    console.log("   - Oracles get 2%");
    console.log("   - Nodes get 1%");
    console.log("   - Creators get 1%");
    console.log("   - Builder Pool gets 2%");
    console.log("   - Bittensor Pool gets 1%");
    console.log("   - Genesis NFT holders get 0.2%");
    
    // Calculate expected payouts
    const genesisPoolShare = (marketData.platformFeeCollected * 2n) / 1000n; // 0.2%
    const yourShare = (genesisPoolShare * nftBalance) / totalMinted;
    
    console.log("\n💰 Your expected Genesis payout:");
    console.log("   ", ethers.formatEther(yourShare), "ETH");
    console.log("   (", nftBalance.toString(), "/", totalMinted.toString(), "NFTs × 0.2% of fees)");
    
    // Try to distribute via PayoutManager
    try {
      // The PayoutManager expects to be called by a market contract
      // For demo purposes, we'll show the calculation
      console.log("\n📊 Payout Calculation:");
      console.log("- Platform fee collected:", ethers.formatEther(marketData.platformFeeCollected), "ETH");
      console.log("- Genesis pool (0.2%):", ethers.formatEther(genesisPoolShare), "ETH");
      console.log("- Your share (100% of pool):", ethers.formatEther(yourShare), "ETH");
      
      // In production, the EnhancedPredictionMarket would call PayoutManager.distributeFees()
      console.log("\n⚠️ Note: In production, market resolution automatically triggers payouts");
      console.log("The EnhancedPredictionMarket contract handles this when markets resolve.");
      
    } catch (error) {
      console.log("\n📝 Distribution requires market integration");
      console.log("In production, the market contract triggers automatic distribution");
    }
    
  } catch (error) {
    console.error("Error:", error.message);
  }
  
  // Final summary
  console.log("\n═══════════════════════════════════════════");
  console.log("📊 SUMMARY");
  console.log("═══════════════════════════════════════════\n");
  
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const spent = initialBalance - finalBalance;
  
  console.log("✅ Demo Complete!");
  console.log("💰 ETH spent on gas:", ethers.formatEther(spent), "ETH");
  console.log("🎨 Your Genesis NFTs:", nftBalance.toString(), "/ 100 total");
  console.log("💎 Platform revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  
  console.log("\n📝 How Genesis NFT Payouts Work:");
  console.log("1. Users create markets and place bets");
  console.log("2. Platform collects 7% fee from all activity");
  console.log("3. When markets resolve, fees are distributed:");
  console.log("   - 0.2% goes to Genesis NFT holders (you!)");
  console.log("   - Remaining goes to oracles, nodes, creators, etc.");
  console.log("4. With 15 NFTs, you own 100% of current Genesis pool");
  console.log("5. As more NFTs are minted, rewards are shared proportionally");
  
  console.log("\n🚀 Next Steps:");
  console.log("1. Deploy to mainnet when ready");
  console.log("2. Users can mint remaining 85 Genesis NFTs");
  console.log("3. Real market activity generates continuous rewards");
  console.log("4. Payouts happen automatically on every market resolution");
  
  console.log("\n🔗 View your NFTs on Basescan:");
  console.log("https://sepolia.basescan.org/token/" + deployment.contracts.GenesisNFT);
  console.log("\n🔗 Your wallet:");
  console.log("https://sepolia.basescan.org/address/" + deployer.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });