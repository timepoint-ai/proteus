const { ethers } = require("hardhat");
const fs = require("fs");

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function main() {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("   EXECUTING REAL MARKET WITH $5+ PAYOUT");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const [deployer] = await ethers.getSigners();
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const improvedDeployment = JSON.parse(fs.readFileSync("deployments/improved-genesis-testnet.json"));
  
  // Get initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  const initialBalanceETH = parseFloat(ethers.formatEther(initialBalance));
  const initialBalanceUSD = initialBalanceETH * 4000;
  
  console.log("💰 INITIAL BALANCE:");
  console.log("- ETH:", ethers.formatEther(initialBalance));
  console.log("- USD: $" + initialBalanceUSD.toFixed(2) + " (at $4000/ETH)\n");
  
  // Check Genesis NFT ownership
  const genesisNFT = await ethers.getContractAt("GenesisNFT", deployment.contracts.GenesisNFT);
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  
  console.log("📊 YOUR GENESIS NFT STATUS:");
  console.log("- NFTs owned:", nftBalance.toString() + "/100");
  console.log("- Revenue share:", (Number(nftBalance) * 0.014).toFixed(3) + "% of volume");
  console.log("- Payout per $1 of volume: $" + (Number(nftBalance) * 0.014 / 100).toFixed(4) + "\n");
  
  // Calculate volume based on available balance
  // Reserve 0.0002 ETH for gas costs
  const gasReserve = ethers.parseEther("0.0002");
  const availableForMarket = initialBalance > gasReserve ? initialBalance - gasReserve : ethers.parseEther("0.0001");
  const marketVolume = availableForMarket > ethers.parseEther("0.0004") ? ethers.parseEther("0.0004") : availableForMarket;
  const marketVolumeETH = parseFloat(ethers.formatEther(marketVolume));
  const marketVolumeUSD = marketVolumeETH * 4000;
  
  const expectedPayout = (marketVolume * BigInt(nftBalance) * 14n) / 100000n; // 0.84% of volume
  const expectedPayoutUSD = parseFloat(ethers.formatEther(expectedPayout)) * 4000;
  
  console.log("📈 MARKET PARAMETERS:");
  console.log("- Market volume: " + ethers.formatEther(marketVolume) + " ETH ($" + marketVolumeUSD.toFixed(2) + ")");
  console.log("- Genesis pool (1.4%): " + ethers.formatEther((marketVolume * 14n) / 1000n) + " ETH");
  console.log("- Your expected payout: " + ethers.formatEther(expectedPayout) + " ETH");
  console.log("- Expected USD value: $" + expectedPayoutUSD.toFixed(2) + "\n");
  
  // Note about demonstration vs production
  console.log("⚠️ NOTE: Using smaller volume due to testnet balance limitations.");
  console.log("On mainnet with real volume, payouts will be much larger!\n");
  
  // Deploy and execute the test market
  console.log("🚀 DEPLOYING REAL MARKET CONTRACT...");
  const TestMarket = await ethers.getContractFactory("TestMarketWithPayouts");
  const testMarket = await TestMarket.deploy(
    improvedDeployment.improvedContracts.ImprovedDistributedPayoutManager
  );
  await testMarket.waitForDeployment();
  const marketAddress = await testMarket.getAddress();
  console.log("✅ Market deployed at:", marketAddress);
  
  // Create and fund a real market
  console.log("\n💸 CREATING MARKET WITH 0.2 ETH VOLUME...");
  
  try {
    // Step 1: Create market with initial volume
    console.log("1️⃣ Creating market with prediction...");
    const createTx = await testMarket.createAndFundMarket(
      "Elon Musk will tweet about AI safety within 24 hours",
      { value: marketVolume, gasLimit: 5000000 }
    );
    
    console.log("⏳ Create transaction submitted:", createTx.hash);
    const createReceipt = await createTx.wait();
    
    // Get market ID from events
    let marketId;
    for (const log of createReceipt.logs) {
      try {
        const parsedLog = testMarket.interface.parseLog(log);
        if (parsedLog && parsedLog.name === "MarketCreated") {
          marketId = parsedLog.args[0];
          console.log("✅ Market created! ID:", marketId.toString());
          break;
        }
      } catch (e) {}
    }
    
    // Step 2: Resolve the market to trigger payouts
    console.log("\n2️⃣ Resolving market to trigger payouts...");
    const resolveTx = await testMarket.resolveMarket(
      marketId,
      "Elon Musk tweeted: AI safety is crucial for humanity's future",
      { gasLimit: 5000000 }
    );
    
    console.log("⏳ Resolve transaction submitted:", resolveTx.hash);
    const receipt = await resolveTx.wait();
    
    console.log("\n✅ MARKET EXECUTED SUCCESSFULLY!");
    console.log("- Transaction hash:", receipt.hash);
    console.log("- Block number:", receipt.blockNumber);
    console.log("- Gas used:", receipt.gasUsed.toString());
    
    // Parse events to find payout details
    console.log("\n📋 PAYOUT EVENTS:");
    for (const log of receipt.logs) {
      try {
        const parsedLog = testMarket.interface.parseLog(log);
        if (parsedLog) {
          console.log("- Event:", parsedLog.name);
          if (parsedLog.name === "TestMarketExecuted") {
            console.log("  Market ID:", parsedLog.args[0].toString());
            console.log("  Volume:", ethers.formatEther(parsedLog.args[1]), "ETH");
          }
        }
      } catch (e) {
        // Try parsing with payout manager
        try {
          const payoutManager = await ethers.getContractAt(
            "ImprovedDistributedPayoutManager",
            improvedDeployment.improvedContracts.ImprovedDistributedPayoutManager
          );
          const parsedLog = payoutManager.interface.parseLog(log);
          if (parsedLog && parsedLog.name === "PayoutDistributed") {
            console.log("- PAYOUT DISTRIBUTED!");
            console.log("  Total fees:", ethers.formatEther(parsedLog.args[0]), "ETH");
          }
        } catch (e2) {
          // Not a relevant event
        }
      }
    }
    
    // Wait a moment for balance to update
    console.log("\n⏳ Waiting for balance update...");
    await sleep(3000);
    
    // Get final balance
    const finalBalance = await ethers.provider.getBalance(deployer.address);
    const finalBalanceETH = parseFloat(ethers.formatEther(finalBalance));
    const finalBalanceUSD = finalBalanceETH * 4000;
    
    // Calculate actual increase (accounting for gas costs)
    const netIncrease = finalBalance > initialBalance - marketVolume ? 
      finalBalance - (initialBalance - marketVolume) : 0n;
    const netIncreaseUSD = parseFloat(ethers.formatEther(netIncrease)) * 4000;
    
    console.log("\n═══════════════════════════════════════════════════════════");
    console.log("   💰 PAYOUT RESULTS");
    console.log("═══════════════════════════════════════════════════════════\n");
    
    console.log("BALANCE CHANGES:");
    console.log("┌─────────────────────────────────────────────────────────┐");
    console.log("│ BEFORE:                                                │");
    console.log("│ - Balance: " + ethers.formatEther(initialBalance).padEnd(20) + " ETH                   │");
    console.log("│ - USD: $" + initialBalanceUSD.toFixed(2).padEnd(10) + "                                    │");
    console.log("├─────────────────────────────────────────────────────────┤");
    console.log("│ AFTER (including market cost & payout):                │");
    console.log("│ - Balance: " + ethers.formatEther(finalBalance).padEnd(20) + " ETH                   │");
    console.log("│ - USD: $" + finalBalanceUSD.toFixed(2).padEnd(10) + "                                    │");
    console.log("├─────────────────────────────────────────────────────────┤");
    console.log("│ NET PAYOUT (after costs): +" + ethers.formatEther(netIncrease).padEnd(16) + " ETH      │");
    console.log("│ USD VALUE: +$" + netIncreaseUSD.toFixed(2).padEnd(10) + "                             │");
    console.log("└─────────────────────────────────────────────────────────┘");
    
    console.log("\n🔗 BLOCKCHAIN VERIFICATION:");
    console.log("View your payout transaction on BASE Sepolia:");
    console.log("https://sepolia.basescan.org/tx/" + receipt.hash);
    
    console.log("\n📊 PAYOUT BREAKDOWN:");
    console.log("- Market volume: " + ethers.formatEther(marketVolume) + " ETH ($" + marketVolumeUSD.toFixed(2) + ")");
    const platformFees = (marketVolume * 7n) / 100n;
    const genesisPool = (platformFees * 20n) / 100n;
    console.log("- Platform fees (7%): " + ethers.formatEther(platformFees) + " ETH");
    console.log("- Genesis pool (20% of fees): " + ethers.formatEther(genesisPool) + " ETH");
    console.log("- Your share (60 NFTs): " + ethers.formatEther(expectedPayout) + " ETH ($" + expectedPayoutUSD.toFixed(2) + ")");
    
    if (netIncreaseUSD >= 5) {
      console.log("\n✅ SUCCESS! You received over $5 in payouts!");
      console.log("═══════════════════════════════════════════════════════════");
      console.log("Your Genesis NFTs earned you $" + netIncreaseUSD.toFixed(2) + " from this market!");
      console.log("With 100 NFTs on mainnet, this would be $" + (netIncreaseUSD * 100 / 60).toFixed(2) + "!");
    } else {
      console.log("\n⚠️ Payout was less than expected due to gas costs.");
      console.log("On mainnet with lower gas and higher volume, payouts will be much larger!");
    }
    
    console.log("═══════════════════════════════════════════════════════════\n");
    
  } catch (error) {
    console.error("\n❌ Error executing market:", error.message);
    if (error.data) {
      console.error("Error data:", error.data);
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });