const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("   DEPLOYING IMPROVED GENESIS PAYOUT SYSTEM (1.4% of volume)");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const [deployer] = await ethers.getSigners();
  const genesisDeployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  
  console.log("📍 Configuration:");
  console.log("- Deployer:", deployer.address);
  console.log("- Genesis NFT:", genesisDeployment.contracts.GenesisNFT);
  console.log("- Network: BASE Sepolia\n");
  
  // Deploy Improved Payout Manager
  console.log("🚀 Deploying ImprovedDistributedPayoutManager...");
  console.log("- Genesis gets: 20% of platform fees (1.4% of volume)");
  console.log("- Old version: 2.8% of platform fees (0.2% of volume)");
  console.log("- Improvement: 7X MORE INCOME!\n");
  
  const ImprovedPayoutManager = await ethers.getContractFactory("ImprovedDistributedPayoutManager");
  
  // Use mock addresses for pools that don't exist yet
  const mockBuilderPool = "0x0000000000000000000000000000000000000001";
  const mockBittensorPool = "0x0000000000000000000000000000000000000002";
  const mockPredictionMarket = "0x429f448e93613d842183E7261386CFC817d94Baf"; // Our test market
  
  const improvedPayoutManager = await ImprovedPayoutManager.deploy(
    mockPredictionMarket,
    mockBuilderPool,
    mockBittensorPool,
    genesisDeployment.contracts.GenesisNFT
  );
  
  await improvedPayoutManager.waitForDeployment();
  const improvedAddress = await improvedPayoutManager.getAddress();
  
  console.log("✅ ImprovedDistributedPayoutManager deployed!");
  console.log("📍 Contract address:", improvedAddress);
  
  // Get fee breakdown
  const feeBreakdown = await improvedPayoutManager.getFeeBreakdown();
  
  console.log("\n💰 NEW FEE DISTRIBUTION (% of platform fees):");
  console.log("═══════════════════════════════════════════════");
  console.log("├─ Genesis NFTs:  " + feeBreakdown[0] + "% ✨ (was 2.8%)");
  console.log("├─ Oracles:       " + feeBreakdown[1] + "%");
  console.log("├─ Nodes:         " + feeBreakdown[2] + "%");
  console.log("├─ Creators:      " + feeBreakdown[3] + "%");
  console.log("├─ Builder Pool:  " + feeBreakdown[4] + "%");
  console.log("└─ Bittensor AI:  " + feeBreakdown[5] + "%");
  
  // Calculate example earnings
  console.log("\n💎 EARNINGS CALCULATOR (100 Genesis NFTs):");
  console.log("═══════════════════════════════════════════════");
  
  const testVolumes = [
    ethers.parseEther("100"),
    ethers.parseEther("1000"),
    ethers.parseEther("10000")
  ];
  
  for (const volume of testVolumes) {
    const earnings = await improvedPayoutManager.calculateGenesisEarnings(volume, 100);
    console.log(`${ethers.formatEther(volume)} ETH volume → ${ethers.formatEther(earnings)} ETH earnings`);
  }
  
  // Save deployment
  const improvedDeployment = {
    ...genesisDeployment,
    improvedContracts: {
      ImprovedDistributedPayoutManager: improvedAddress,
      deployedAt: new Date().toISOString(),
      improvements: {
        genesisShare: "20% of fees (1.4% of volume)",
        oldShare: "2.8% of fees (0.2% of volume)",
        multiplier: "7X increase"
      }
    }
  };
  
  fs.writeFileSync(
    "deployments/improved-genesis-testnet.json",
    JSON.stringify(improvedDeployment, null, 2)
  );
  
  console.log("\n✅ DEPLOYMENT COMPLETE!");
  console.log("═══════════════════════════════════════════════");
  console.log("📄 Deployment saved to: deployments/improved-genesis-testnet.json");
  console.log("🔗 View on Basescan:");
  console.log(`https://sepolia.basescan.org/address/${improvedAddress}`);
  
  console.log("\n🎯 NEXT STEPS:");
  console.log("1. Test with real markets to verify 1.4% payouts");
  console.log("2. Deploy to mainnet when ready");
  console.log("3. You mint all 100 Genesis NFTs");
  console.log("4. Earn 1.4% of all platform volume forever!");
  
  console.log("\n✨ Genesis NFT holders now get the rewards they deserve!");
  console.log("═══════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });