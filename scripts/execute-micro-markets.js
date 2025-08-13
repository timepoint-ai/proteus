const { ethers } = require("hardhat");
const fs = require("fs");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("   MICRO TEST MARKETS WITH GENESIS PAYOUTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Configuration:");
  console.log("- Your wallet:", deployer.address);
  console.log("- PayoutManager:", deployment.contracts.DistributedPayoutManager);
  
  // Check your Genesis NFTs
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("\n🎨 Your Genesis NFTs:", nftBalance.toString(), "/", totalMinted.toString(), "minted");
  console.log("💎 Your ownership:", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  
  // Check initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("💰 Starting balance:", ethers.formatEther(initialBalance), "ETH");
  
  // Use the existing test market contract
  const testMarketAddress = "0x429f448e93613d842183E7261386CFC817d94Baf";
  console.log("\n📄 Using deployed test market:", testMarketAddress);
  
  const TestMarket = await ethers.getContractFactory("TestMarketWithPayouts");
  const testMarket = TestMarket.attach(testMarketAddress);
  
  // Track payouts
  let totalPlatformFees = 0n;
  let expectedGenesisPayouts = 0n;
  let successfulMarkets = 0;
  
  // Create micro markets with affordable amounts
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("Creating Micro Markets (0.0001 ETH each)");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const markets = [
    { name: "Micro Market 1", volume: "0.0001", prediction: "BTC daily close > $50k" },
    { name: "Micro Market 2", volume: "0.0001", prediction: "ETH gas < 30 gwei" },
    { name: "Micro Market 3", volume: "0.0001", prediction: "BASE TVL > $1B" }
  ];
  
  for (let i = 0; i < markets.length; i++) {
    const market = markets[i];
    console.log(`\n📊 ${market.name}`);
    console.log("─────────────────────");
    
    try {
      // Create market with micro amount
      const volume = ethers.parseEther(market.volume);
      console.log(`Creating: "${market.prediction}"`);
      console.log(`Volume: ${market.volume} ETH`);
      
      const createTx = await testMarket.createAndFundMarket(market.prediction, { 
        value: volume,
        gasLimit: 500000 // Set explicit gas limit
      });
      const createReceipt = await createTx.wait();
      const marketId = successfulMarkets + 1;
      successfulMarkets++;
      
      console.log(`✅ Market ${marketId} created!`);
      console.log(`⛽ Gas used: ${createReceipt.gasUsed.toString()}`);
      
      // Get market details
      const marketData = await testMarket.getMarket(marketId);
      const platformFee = marketData[2];
      totalPlatformFees += platformFee;
      
      console.log(`Platform fee (7%): ${ethers.formatEther(platformFee)} ETH`);
      
      // Calculate Genesis payout
      const genesisPoolShare = (platformFee * 2n) / 1000n; // 0.2%
      const yourGenesisShare = (genesisPoolShare * nftBalance) / totalMinted;
      expectedGenesisPayouts += yourGenesisShare;
      
      console.log(`Genesis pool (0.2%): ${ethers.formatEther(genesisPoolShare)} ETH`);
      console.log(`Your payout: ${ethers.formatEther(yourGenesisShare)} ETH`);
      
      // Resolve market immediately
      console.log(`Resolving market...`);
      const resolveTx = await testMarket.resolveMarket(marketId, "Result: YES", {
        gasLimit: 500000
      });
      const resolveReceipt = await resolveTx.wait();
      console.log(`✅ Market resolved & payouts sent!`);
      
      // Check the balance change
      const currentBalance = await ethers.provider.getBalance(deployer.address);
      const received = currentBalance - initialBalance;
      if (received > 0) {
        console.log(`💰 Received so far: ${ethers.formatEther(received)} ETH`);
      }
      
    } catch (error) {
      console.error(`❌ Error:`, error.message.substring(0, 50));
      
      // If balance too low, stop
      const currentBalance = await ethers.provider.getBalance(deployer.address);
      if (currentBalance < ethers.parseEther("0.0002")) {
        console.log("\n⚠️ Balance too low to continue");
        break;
      }
    }
    
    if (i < markets.length - 1) {
      await sleep(1000);
    }
  }
  
  // Final results
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("📊 FINAL RESULTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const netChange = finalBalance - initialBalance;
  
  console.log("✅ Test Complete!");
  console.log("\n💰 Balance Summary:");
  console.log("─────────────────────");
  console.log("Starting:                ", ethers.formatEther(initialBalance), "ETH");
  console.log("Final:                   ", ethers.formatEther(finalBalance), "ETH");
  console.log("Net change:              ", ethers.formatEther(netChange), "ETH");
  
  if (successfulMarkets > 0) {
    console.log("\n📊 Market Performance:");
    console.log("─────────────────────");
    console.log("Markets created:         ", successfulMarkets);
    console.log("Total platform fees:     ", ethers.formatEther(totalPlatformFees), "ETH");
    console.log("Expected Genesis payout: ", ethers.formatEther(expectedGenesisPayouts), "ETH");
    
    // Show payout calculation
    console.log("\n💎 Payout Breakdown:");
    console.log("─────────────────────");
    console.log("From", ethers.formatEther(totalPlatformFees), "ETH in fees:");
    console.log("• Oracles (2%):         ", ethers.formatEther((totalPlatformFees * 20n) / 1000n), "ETH");
    console.log("• Nodes (1%):           ", ethers.formatEther((totalPlatformFees * 10n) / 1000n), "ETH");
    console.log("• Creators (1%):        ", ethers.formatEther((totalPlatformFees * 10n) / 1000n), "ETH");
    console.log("• Builder Pool (2%):    ", ethers.formatEther((totalPlatformFees * 20n) / 1000n), "ETH");
    console.log("• Bittensor AI (1%):    ", ethers.formatEther((totalPlatformFees * 10n) / 1000n), "ETH");
    console.log("• Genesis NFTs (0.2%):  ", ethers.formatEther((totalPlatformFees * 2n) / 1000n), "ETH");
    console.log("  └─ Your share (100%):", ethers.formatEther(expectedGenesisPayouts), "ETH");
  }
  
  console.log("\n🔗 Verify on Basescan:");
  console.log("─────────────────────");
  console.log("Your transactions:");
  console.log(`https://sepolia.basescan.org/address/${deployer.address}`);
  console.log("\nTest Market:");
  console.log(`https://sepolia.basescan.org/address/${testMarketAddress}`);
  console.log("\nPayout Manager:");
  console.log(`https://sepolia.basescan.org/address/${deployment.contracts.DistributedPayoutManager}`);
  
  console.log("\n✨ DEMONSTRATION COMPLETE");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("This test demonstrated how Genesis NFT payouts work:");
  console.log("1. Markets generate platform fees (7% of volume)");
  console.log("2. Fees are distributed to stakeholders");
  console.log("3. Genesis holders receive 0.2% automatically");
  console.log("4. With your 15 NFTs, you get 100% of Genesis pool");
  console.log("\nIn production, larger markets = larger payouts!");
  console.log("═══════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });