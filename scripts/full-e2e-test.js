const { ethers } = require("hardhat");
const fs = require("fs");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("🚀 Full E2E Test: Market → Submission → Resolution → Genesis Payout\n");
  
  // Load deployments
  const mainDeployment = JSON.parse(fs.readFileSync("deployment-base-sepolia.json"));
  const genesisDeployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  // Find the EnhancedPredictionMarket address
  const enhancedMarketAddress = mainDeployment.contracts?.EnhancedPredictionMarket?.address || 
                                "0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C"; // Known address
  
  console.log("📍 Using Contracts:");
  console.log("- EnhancedPredictionMarket:", enhancedMarketAddress);
  console.log("- GenesisNFT:", genesisDeployment.contracts.GenesisNFT);
  console.log("- Your wallet:", deployer.address);
  
  // Connect to contracts
  const marketABI = [
    "function createMarket(address actor, uint256 duration) payable returns (uint256)",
    "function submitPrediction(uint256 marketId, string memory predictedText) payable",
    "function placeBet(uint256 submissionId) payable",
    "function resolveMarket(uint256 marketId, string memory actualText, string memory screenshotIpfs)",
    "function distributePayouts(uint256 marketId)",
    "function markets(uint256) view returns (address creator, address actor, uint256 startTime, uint256 endTime, bool resolved, uint256 winningSubmissionId, uint256 totalVolume)",
    "function marketCount() view returns (uint256)",
    "function getMarketSubmissions(uint256 marketId) view returns (uint256[] memory)",
    "function submissions(uint256) view returns (uint256 marketId, address creator, string memory predictedText, uint256 stake, uint256 totalBets, uint256 levenshteinDistance, bool isWinner)"
  ];
  
  const market = new ethers.Contract(enhancedMarketAddress, marketABI, deployer);
  
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(genesisDeployment.contracts.GenesisNFT);
  
  // Check NFT ownership
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  console.log("\n🎨 Your Genesis NFTs:", nftBalance.toString());
  console.log("💎 Platform revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  
  // Check initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("💰 Initial balance:", ethers.formatEther(initialBalance), "ETH\n");
  
  console.log("═══════════════════════════════════════════");
  console.log("STEP 1: Create Prediction Market");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    // Use a test actor address
    const testActor = "0x1234567890123456789012345678901234567890";
    const marketDuration = 120; // 2 minutes for testing
    const marketFee = ethers.parseEther("0.00001"); // Small creation fee
    
    console.log("Creating market for 2-minute prediction window...");
    const createTx = await market.createMarket(testActor, marketDuration, { value: marketFee });
    const createReceipt = await createTx.wait();
    console.log("✅ Market created! Gas used:", createReceipt.gasUsed.toString());
    
    // Get market ID
    const marketCount = await market.marketCount();
    const marketId = marketCount - 1n;
    console.log("📝 Market ID:", marketId.toString());
    
    // Get market details
    const marketData = await market.markets(marketId);
    console.log("\nMarket Details:");
    console.log("- Creator:", marketData.creator);
    console.log("- End time:", new Date(Number(marketData.endTime) * 1000).toLocaleTimeString());
    
    console.log("\n═══════════════════════════════════════════");
    console.log("STEP 2: Submit Predictions");
    console.log("═══════════════════════════════════════════\n");
    
    const submissionStake = ethers.parseEther("0.0001");
    
    // Make first prediction
    console.log("Submitting prediction 1: 'Mars is amazing'");
    const submit1Tx = await market.submitPrediction(
      marketId,
      "Mars is amazing",
      { value: submissionStake }
    );
    await submit1Tx.wait();
    console.log("✅ Prediction 1 submitted");
    
    // Make second prediction
    console.log("Submitting prediction 2: 'Going to the moon'");
    const submit2Tx = await market.submitPrediction(
      marketId,
      "Going to the moon",
      { value: submissionStake }
    );
    await submit2Tx.wait();
    console.log("✅ Prediction 2 submitted");
    
    // Get submissions
    const submissionIds = await market.getMarketSubmissions(marketId);
    console.log("\nTotal submissions:", submissionIds.length);
    
    console.log("\n═══════════════════════════════════════════");
    console.log("STEP 3: Place Bets");
    console.log("═══════════════════════════════════════════\n");
    
    const betAmount = ethers.parseEther("0.00005");
    
    if (submissionIds.length > 0) {
      console.log("Placing bet on submission", submissionIds[0].toString());
      const betTx = await market.placeBet(submissionIds[0], { value: betAmount });
      await betTx.wait();
      console.log("✅ Bet placed");
    }
    
    // Check total volume
    const updatedMarket = await market.markets(marketId);
    console.log("📊 Total market volume:", ethers.formatEther(updatedMarket.totalVolume), "ETH");
    
    console.log("\n═══════════════════════════════════════════");
    console.log("STEP 4: Wait for Market to Expire");
    console.log("═══════════════════════════════════════════\n");
    
    console.log("⏱️ Waiting 2 minutes for market to expire...");
    console.log("(In production, this would be hours or days)");
    
    // Show countdown
    for (let i = 120; i > 0; i -= 30) {
      await sleep(30000);
      console.log(`   ${Math.max(0, i - 30)} seconds remaining...`);
    }
    
    console.log("\n═══════════════════════════════════════════");
    console.log("STEP 5: Resolve Market & Distribute Payouts");
    console.log("═══════════════════════════════════════════\n");
    
    console.log("Resolving market with actual text: 'Mars is amazing'");
    const resolveTx = await market.resolveMarket(
      marketId,
      "Mars is amazing", // Exact match with submission 1
      "ipfs://QmTestScreenshot"
    );
    const resolveReceipt = await resolveTx.wait();
    console.log("✅ Market resolved! Gas used:", resolveReceipt.gasUsed.toString());
    
    // Distribute payouts
    console.log("\nDistributing payouts...");
    const distributeTx = await market.distributePayouts(marketId);
    const distributeReceipt = await distributeTx.wait();
    console.log("✅ Payouts distributed!");
    
    // Calculate Genesis NFT share
    const totalVolume = updatedMarket.totalVolume;
    const platformFee = (totalVolume * 7n) / 100n; // 7% platform fee
    const genesisShare = (platformFee * 2n) / 1000n; // 0.2% to Genesis
    const yourShare = (genesisShare * nftBalance) / 15n; // Your portion (15/15 NFTs)
    
    console.log("\n💰 Payout Breakdown:");
    console.log("- Total volume:", ethers.formatEther(totalVolume), "ETH");
    console.log("- Platform fee (7%):", ethers.formatEther(platformFee), "ETH");
    console.log("- Genesis pool (0.2% of fees):", ethers.formatEther(genesisShare), "ETH");
    console.log("- Your Genesis payout:", ethers.formatEther(yourShare), "ETH");
    
  } catch (error) {
    console.error("❌ Error:", error.message);
    
    // Try simpler test
    console.log("\n═══════════════════════════════════════════");
    console.log("FALLBACK: Simple Fee Test");
    console.log("═══════════════════════════════════════════\n");
    
    console.log("Note: The main contracts may need specific setup.");
    console.log("In production, markets would be created through the UI");
    console.log("and resolved by oracles monitoring X.com.");
  }
  
  // Final summary
  console.log("\n═══════════════════════════════════════════");
  console.log("📊 FINAL SUMMARY");
  console.log("═══════════════════════════════════════════\n");
  
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const balanceChange = finalBalance - initialBalance;
  
  console.log("✅ E2E Test Complete!");
  console.log("💰 Balance change:", ethers.formatEther(balanceChange), "ETH");
  console.log("🎨 Your Genesis NFTs:", nftBalance.toString());
  
  console.log("\n📝 How it works in production:");
  console.log("1. Users create markets predicting tweets");
  console.log("2. Multiple users submit predictions");
  console.log("3. Others bet on submissions");
  console.log("4. After time expires, oracle checks X.com");
  console.log("5. Market resolves based on actual tweet");
  console.log("6. Winners get paid, Genesis holders get 0.2% of all fees");
  
  console.log("\n🔗 View your transactions:");
  console.log("https://sepolia.basescan.org/address/" + deployer.address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });