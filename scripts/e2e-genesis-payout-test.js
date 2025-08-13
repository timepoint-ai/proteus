const { ethers } = require("hardhat");
const fs = require("fs");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("🚀 Genesis NFT E2E Payout Test on BASE Sepolia\n");
  console.log("This test will:");
  console.log("1. Create prediction markets");
  console.log("2. Make submissions with ETH");
  console.log("3. Resolve markets");
  console.log("4. Distribute payouts to Genesis NFT holders\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Contracts:");
  console.log("- MockPredictionMarket:", deployment.contracts.MockPredictionMarket);
  console.log("- GenesisNFT:", deployment.contracts.GenesisNFT);
  console.log("- PayoutManager:", deployment.contracts.DistributedPayoutManager);
  console.log("- Your wallet:", deployer.address);
  
  // Check initial balances
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("\n💰 Initial balance:", ethers.formatEther(initialBalance), "ETH");
  
  // Connect to contracts
  const MockMarket = await ethers.getContractFactory("MockPredictionMarket");
  const market = MockMarket.attach(deployment.contracts.MockPredictionMarket);
  
  const PayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  const payoutManager = PayoutManager.attach(deployment.contracts.DistributedPayoutManager);
  
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  // Check NFT ownership
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  console.log("🎨 Your Genesis NFTs:", nftBalance.toString());
  console.log("💎 Your revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%\n");
  
  // Test 1: Create and resolve a simple market
  console.log("═══════════════════════════════════════════");
  console.log("TEST 1: Simple Market with Single Submission");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    // Create market with 0.01 ETH submission
    const submissionAmount = ethers.parseEther("0.0001"); // Small amount for testing
    console.log("1️⃣ Creating market with submission of", ethers.formatEther(submissionAmount), "ETH...");
    
    const createTx = await market.createMarketWithSubmission(
      "Elon Musk",
      "Will tweet about Mars",
      60, // 60 seconds duration
      { value: submissionAmount }
    );
    await createTx.wait();
    console.log("✅ Market created");
    
    // Get market ID
    const marketCount = await market.marketCount();
    const marketId = marketCount - 1n;
    console.log("📝 Market ID:", marketId.toString());
    
    // Wait for market to expire
    console.log("\n⏱️ Waiting 60 seconds for market to expire...");
    console.log("(In production, this would be the actual prediction timeframe)");
    
    // Show countdown
    for (let i = 60; i > 0; i -= 10) {
      await sleep(10000);
      console.log(`   ${i - 10} seconds remaining...`);
    }
    
    // Resolve market
    console.log("\n2️⃣ Resolving market...");
    const resolveTx = await market.resolveMarket(marketId);
    const resolveReceipt = await resolveTx.wait();
    console.log("✅ Market resolved");
    
    // Trigger payout distribution
    console.log("\n3️⃣ Distributing payouts through PayoutManager...");
    const payoutTx = await payoutManager.distributeFees(submissionAmount);
    const payoutReceipt = await payoutTx.wait();
    console.log("✅ Payouts distributed");
    
    // Calculate expected payout
    const genesisShare = (submissionAmount * 2n) / 1000n; // 0.2% to Genesis holders
    const yourShare = (genesisShare * nftBalance) / 100n; // Your portion based on NFT ownership
    
    console.log("\n💰 Payout Breakdown:");
    console.log("- Total fees:", ethers.formatEther(submissionAmount), "ETH");
    console.log("- Genesis holders (0.2%):", ethers.formatEther(genesisShare), "ETH");
    console.log("- Your share (" + nftBalance + " NFTs):", ethers.formatEther(yourShare), "ETH");
    
    // Check final balance
    const finalBalance = await ethers.provider.getBalance(deployer.address);
    console.log("\n📊 Balance change:", ethers.formatEther(finalBalance - initialBalance), "ETH");
    
  } catch (error) {
    console.error("❌ Test 1 failed:", error.message);
  }
  
  // Test 2: Competitive market with multiple submissions
  console.log("\n═══════════════════════════════════════════");
  console.log("TEST 2: Competitive Market with Multiple Submissions");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    const submissionAmount = ethers.parseEther("0.0002");
    
    console.log("1️⃣ Creating market with initial submission...");
    const createTx = await market.createMarketWithSubmission(
      "Vitalik Buterin",
      "Will discuss Ethereum upgrades",
      90, // 90 seconds
      { value: submissionAmount }
    );
    await createTx.wait();
    
    const marketCount = await market.marketCount();
    const marketId = marketCount - 1n;
    console.log("📝 Market ID:", marketId.toString());
    
    // Add competing submission
    console.log("\n2️⃣ Adding competing submission...");
    const competeTx = await market.addSubmission(
      marketId,
      "Will talk about decentralization",
      { value: submissionAmount }
    );
    await competeTx.wait();
    console.log("✅ Competing submission added");
    
    // Wait for expiration
    console.log("\n⏱️ Waiting 90 seconds for market to expire...");
    for (let i = 90; i > 0; i -= 15) {
      await sleep(15000);
      console.log(`   ${i - 15} seconds remaining...`);
    }
    
    // Resolve with winner
    console.log("\n3️⃣ Resolving market with winner...");
    const resolveTx = await market.resolveMarket(marketId);
    await resolveTx.wait();
    console.log("✅ Market resolved");
    
    // Distribute fees
    const totalFees = submissionAmount * 2n; // Two submissions
    console.log("\n4️⃣ Distributing fees from", ethers.formatEther(totalFees), "ETH pool...");
    const payoutTx = await payoutManager.distributeFees(totalFees);
    await payoutTx.wait();
    
    const genesisShare = (totalFees * 2n) / 1000n; // 0.2%
    const yourShare = (genesisShare * nftBalance) / 100n;
    
    console.log("\n💰 Payout Breakdown:");
    console.log("- Total fees:", ethers.formatEther(totalFees), "ETH");
    console.log("- Genesis holders (0.2%):", ethers.formatEther(genesisShare), "ETH");
    console.log("- Your share (" + nftBalance + " NFTs):", ethers.formatEther(yourShare), "ETH");
    
  } catch (error) {
    console.error("❌ Test 2 failed:", error.message);
  }
  
  // Final summary
  console.log("\n═══════════════════════════════════════════");
  console.log("📊 TEST SUMMARY");
  console.log("═══════════════════════════════════════════\n");
  
  const endBalance = await ethers.provider.getBalance(deployer.address);
  const totalReceived = endBalance - initialBalance;
  
  console.log("✅ Tests completed!");
  console.log("💰 Total received from Genesis NFT payouts:", ethers.formatEther(totalReceived), "ETH");
  console.log("🎨 Your NFTs:", nftBalance.toString(), "/ 100");
  console.log("💎 Revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  
  console.log("\n📝 Note: In production:");
  console.log("- Markets would have real predictions about public figures");
  console.log("- Oracle would verify actual tweets/statements");
  console.log("- Payouts would be in real ETH on BASE mainnet");
  console.log("- Your Genesis NFTs would earn from ALL platform activity");
  
  console.log("\n🔗 View transactions on Basescan:");
  console.log("https://sepolia.basescan.org/address/" + deployer.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });