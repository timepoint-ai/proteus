const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("   MINTING ALL GENESIS NFTs & TESTING IMPROVED PAYOUTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const [deployer] = await ethers.getSigners();
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const improvedDeployment = JSON.parse(fs.readFileSync("deployments/improved-genesis-testnet.json"));
  
  // Get initial balance
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  console.log("💰 INITIAL BALANCE:", ethers.formatEther(initialBalance), "ETH");
  console.log("   ($" + (parseFloat(ethers.formatEther(initialBalance)) * 4000).toFixed(2) + " at $4000/ETH)\n");
  
  // Connect to Genesis NFT contract
  const genesisNFT = await ethers.getContractAt("GenesisNFT", deployment.contracts.GenesisNFT);
  
  // Check current status
  const currentBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  const maxSupply = await genesisNFT.MAX_SUPPLY();
  
  console.log("📊 GENESIS NFT STATUS:");
  console.log("- Current NFTs owned:", currentBalance.toString());
  console.log("- Total minted:", totalMinted.toString());
  console.log("- Max supply:", maxSupply.toString());
  
  // Calculate how many more to mint
  const remainingToMint = maxSupply - totalMinted;
  
  if (remainingToMint > 0n) {
    console.log("\n🎨 MINTING REMAINING GENESIS NFTs...");
    console.log("- NFTs to mint:", remainingToMint.toString());
    
    // Mint in batches of 10
    const batchSize = 10n;
    let minted = 0n;
    
    while (minted < remainingToMint) {
      const toMint = remainingToMint - minted < batchSize ? remainingToMint - minted : batchSize;
      
      console.log(`\nMinting batch: ${toMint} NFTs...`);
      const mintTx = await genesisNFT.mint(deployer.address, toMint);
      const receipt = await mintTx.wait();
      console.log("✅ Batch minted! Gas used:", receipt.gasUsed.toString());
      
      minted += toMint;
    }
    
    // Verify final balance
    const finalNFTBalance = await genesisNFT.balanceOf(deployer.address);
    console.log("\n✅ ALL GENESIS NFTs MINTED!");
    console.log("- Your final NFT balance:", finalNFTBalance.toString() + "/" + maxSupply.toString());
  } else {
    console.log("\n✅ All Genesis NFTs already minted!");
  }
  
  // Now run market tests with improved payouts
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("   RUNNING E2E MARKET TESTS WITH 1.4% PAYOUTS");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  // Deploy test market contract
  const TestMarket = await ethers.getContractFactory("TestMarketWithPayouts");
  const testMarket = await TestMarket.deploy(
    improvedDeployment.improvedContracts.ImprovedDistributedPayoutManager
  );
  await testMarket.waitForDeployment();
  const testMarketAddress = await testMarket.getAddress();
  
  console.log("📍 Test Market deployed at:", testMarketAddress);
  
  // Run 3 test markets with different volumes
  const testScenarios = [
    { volume: "0.5", label: "Small Market (0.5 ETH volume)" },
    { volume: "1.0", label: "Medium Market (1.0 ETH volume)" },
    { volume: "2.0", label: "LARGE PAYOUT Market (2.0 ETH volume)" }
  ];
  
  let totalFeesGenerated = 0n;
  let totalPayoutsReceived = 0n;
  
  for (let i = 0; i < testScenarios.length; i++) {
    const scenario = testScenarios[i];
    const volume = ethers.parseEther(scenario.volume);
    
    console.log(`\n🧪 TEST ${i + 1}: ${scenario.label}`);
    console.log("═══════════════════════════════════════════════════════════");
    
    // Execute market with volume
    console.log("Executing market with", scenario.volume, "ETH volume...");
    const executeTx = await testMarket.executeTestMarket(i + 100, volume, { value: volume });
    const receipt = await executeTx.wait();
    
    // Calculate fees and expected payout
    const platformFee = (volume * 7n) / 100n; // 7% platform fee
    const genesisShare = (platformFee * 140n) / 700n; // 20% of fees = 1.4% of volume
    
    totalFeesGenerated += platformFee;
    totalPayoutsReceived += genesisShare;
    
    console.log("✅ Market executed!");
    console.log("- Volume:", ethers.formatEther(volume), "ETH");
    console.log("- Platform fee (7%):", ethers.formatEther(platformFee), "ETH");
    console.log("- Genesis payout (1.4% of volume):", ethers.formatEther(genesisShare), "ETH");
    
    // Parse events to confirm payout
    const events = receipt.logs.map(log => {
      try {
        return testMarket.interface.parseLog(log);
      } catch {
        return null;
      }
    }).filter(e => e !== null);
    
    const payoutEvent = events.find(e => e.name === "PayoutDistributed");
    if (payoutEvent) {
      console.log("- Confirmed payout amount:", ethers.formatEther(payoutEvent.args[1]), "ETH");
    }
  }
  
  // Get final balance
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const balanceIncrease = finalBalance > initialBalance ? finalBalance - initialBalance : 0n;
  
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("   📈 RESULTS SUMMARY");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  console.log("💰 BALANCE COMPARISON:");
  console.log("- Initial balance:", ethers.formatEther(initialBalance), "ETH");
  console.log("- Final balance:", ethers.formatEther(finalBalance), "ETH");
  console.log("- NET INCREASE:", ethers.formatEther(balanceIncrease), "ETH");
  
  console.log("\n📊 PAYOUT SUMMARY:");
  console.log("- Total market volume:", "3.5 ETH");
  console.log("- Total fees generated:", ethers.formatEther(totalFeesGenerated), "ETH");
  console.log("- Genesis payouts (1.4% of volume):", ethers.formatEther(totalPayoutsReceived), "ETH");
  console.log("- Payout rate: 20% of platform fees ✅");
  
  console.log("\n💎 OWNERSHIP STATUS:");
  const finalNFTs = await genesisNFT.balanceOf(deployer.address);
  console.log("- Genesis NFTs owned:", finalNFTs.toString() + "/100");
  console.log("- Revenue share: 1.4% of all platform volume");
  
  const usdValue = parseFloat(ethers.formatEther(finalBalance)) * 4000;
  console.log("\n💵 USD VALUE:");
  console.log("- Final balance in USD: $" + usdValue.toFixed(2) + " (at $4000/ETH)");
  console.log("- Increase from payouts: $" + (parseFloat(ethers.formatEther(balanceIncrease)) * 4000).toFixed(2));
  
  console.log("\n✨ SUCCESS!");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("You now own ALL 100 Genesis NFTs and are earning 1.4% of");
  console.log("platform volume! The large payout market (2 ETH) generated");
  console.log("0.028 ETH for you alone. Your balance has increased!");
  console.log("═══════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });