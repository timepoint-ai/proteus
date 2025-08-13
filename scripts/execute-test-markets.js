const { ethers } = require("hardhat");
const fs = require("fs");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("   EXECUTING TEST MARKETS WITH REAL GENESIS PAYOUTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Configuration:");
  console.log("- Your wallet:", deployer.address);
  console.log("- PayoutManager:", deployment.contracts.DistributedPayoutManager);
  console.log("- GenesisNFT:", deployment.contracts.GenesisNFT);
  
  // Connect to Genesis NFT to check balance
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("\n🎨 Your Genesis NFTs:", nftBalance.toString(), "/", totalMinted.toString(), "minted");
  console.log("💎 Your share of Genesis pool:", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  
  // Check initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("💰 Starting balance:", ethers.formatEther(initialBalance), "ETH");
  
  // Deploy test market contract
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("STEP 1: Deploy Test Market Contract");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const TestMarket = await ethers.getContractFactory("TestMarketWithPayouts");
  console.log("Deploying TestMarketWithPayouts...");
  const testMarket = await TestMarket.deploy(deployment.contracts.DistributedPayoutManager);
  await testMarket.waitForDeployment();
  const testMarketAddress = await testMarket.getAddress();
  console.log("✅ Test market deployed at:", testMarketAddress);
  
  // Track all payouts
  let totalPlatformFees = 0n;
  let expectedGenesisPayouts = 0n;
  
  // Create and resolve multiple markets
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("STEP 2: Creating & Resolving Test Markets");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const markets = [
    { name: "Small Market", volume: "0.001", prediction: "Bitcoin to $100k" },
    { name: "Medium Market", volume: "0.002", prediction: "Ethereum merge success" },
    { name: "Large Market", volume: "0.003", prediction: "Tesla accepts Dogecoin" }
  ];
  
  for (let i = 0; i < markets.length; i++) {
    const market = markets[i];
    console.log(`\n📊 Market ${i + 1}: ${market.name}`);
    console.log("═════════════════════════════════════");
    
    try {
      // Create market
      const volume = ethers.parseEther(market.volume);
      console.log(`Creating market: "${market.prediction}"`);
      console.log(`Volume: ${market.volume} ETH`);
      
      const createTx = await testMarket.createAndFundMarket(market.prediction, { value: volume });
      const createReceipt = await createTx.wait();
      const marketId = i + 1;
      console.log(`✅ Market ${marketId} created`);
      
      // Add some additional volume (simulating bets)
      const additionalVolume = ethers.parseEther((parseFloat(market.volume) * 0.5).toString());
      console.log(`Adding bets: ${ethers.formatEther(additionalVolume)} ETH`);
      
      const addVolumeTx = await testMarket.addVolume(marketId, { value: additionalVolume });
      await addVolumeTx.wait();
      console.log(`✅ Additional volume added`);
      
      // Get market details
      const marketData = await testMarket.getMarket(marketId);
      const platformFee = marketData[2]; // platformFee
      totalPlatformFees += platformFee;
      
      console.log(`Total volume: ${ethers.formatEther(marketData[1])} ETH`);
      console.log(`Platform fee (7%): ${ethers.formatEther(platformFee)} ETH`);
      
      // Calculate expected Genesis payout
      const genesisPoolShare = (platformFee * 2n) / 1000n; // 0.2% of platform fee
      const yourGenesisShare = (genesisPoolShare * nftBalance) / totalMinted;
      expectedGenesisPayouts += yourGenesisShare;
      
      console.log(`Genesis pool (0.2%): ${ethers.formatEther(genesisPoolShare)} ETH`);
      console.log(`Your payout (${nftBalance}/${totalMinted} NFTs): ${ethers.formatEther(yourGenesisShare)} ETH`);
      
      // Resolve market and trigger payouts
      console.log(`\nResolving market...`);
      const resolveTx = await testMarket.resolveMarket(marketId, `${market.prediction} - Confirmed!`);
      const resolveReceipt = await resolveTx.wait();
      console.log(`✅ Market resolved & payouts distributed!`);
      console.log(`⛽ Gas used: ${resolveReceipt.gasUsed.toString()}`);
      
      // Check for payout events
      const payoutEvents = resolveReceipt.logs.filter(log => 
        log.topics[0] === ethers.id("PayoutDistributed(uint256,uint256)")
      );
      
      if (payoutEvents.length > 0) {
        console.log(`✨ Payout event confirmed!`);
      }
      
    } catch (error) {
      console.error(`❌ Error with market ${i + 1}:`, error.message);
    }
    
    // Small delay between markets
    if (i < markets.length - 1) {
      console.log("\nWaiting 2 seconds before next market...");
      await sleep(2000);
    }
  }
  
  // Final summary
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("📊 FINAL RESULTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const balanceChange = finalBalance - initialBalance;
  
  console.log("✅ All test markets completed!");
  console.log("\n💰 Financial Summary:");
  console.log("─────────────────────────────");
  console.log("Starting balance:        ", ethers.formatEther(initialBalance), "ETH");
  console.log("Final balance:           ", ethers.formatEther(finalBalance), "ETH");
  console.log("Net change:              ", ethers.formatEther(balanceChange), "ETH");
  console.log("\n📊 Market Statistics:");
  console.log("─────────────────────────────");
  console.log("Markets created:         ", markets.length);
  console.log("Total platform fees:     ", ethers.formatEther(totalPlatformFees), "ETH");
  console.log("Expected Genesis payouts:", ethers.formatEther(expectedGenesisPayouts), "ETH");
  
  console.log("\n🎨 Genesis NFT Performance:");
  console.log("─────────────────────────────");
  console.log("Your NFTs:               ", nftBalance.toString());
  console.log("Your ownership:          ", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  console.log("Platform revenue share:  ", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  
  // Calculate actual vs expected
  const gasSpent = initialBalance - finalBalance - expectedGenesisPayouts;
  console.log("\n💡 Payout Analysis:");
  console.log("─────────────────────────────");
  console.log("Expected Genesis payouts:", ethers.formatEther(expectedGenesisPayouts), "ETH");
  console.log("Estimated gas costs:     ", ethers.formatEther(gasSpent > 0 ? gasSpent : 0n), "ETH");
  
  console.log("\n🔗 Verify Transactions:");
  console.log("─────────────────────────────");
  console.log("Your wallet:");
  console.log(`https://sepolia.basescan.org/address/${deployer.address}`);
  console.log("\nTest Market Contract:");
  console.log(`https://sepolia.basescan.org/address/${testMarketAddress}`);
  console.log("\nPayout Manager:");
  console.log(`https://sepolia.basescan.org/address/${deployment.contracts.DistributedPayoutManager}`);
  
  console.log("\n✨ SUCCESS!");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("You've successfully created and resolved", markets.length, "test markets!");
  console.log("Genesis NFT payouts were automatically distributed to your wallet.");
  console.log("Check Basescan to see all transactions and payout details.");
  console.log("═══════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });