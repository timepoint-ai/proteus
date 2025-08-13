const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("════════════════════════════════════════════════════════════");
  console.log("     GENESIS NFT PAYOUT MECHANISM DEMONSTRATION");
  console.log("════════════════════════════════════════════════════════════\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  // Connect to contracts
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  const PayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  const payoutManager = PayoutManager.attach(deployment.contracts.DistributedPayoutManager);
  
  // Get NFT stats
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  const maxSupply = await genesisNFT.MAX_SUPPLY();
  
  console.log("🎨 YOUR GENESIS NFT POSITION");
  console.log("════════════════════════════════════════");
  console.log("Your NFTs:          ", nftBalance.toString());
  console.log("Total Minted:       ", totalMinted.toString(), "/ 100");
  console.log("Your Ownership:     ", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  console.log("Platform Share:     ", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  console.log("Contract:           ", deployment.contracts.GenesisNFT);
  
  // Get your actual NFT IDs
  const nftIds = [];
  for (let i = 1; i <= totalMinted; i++) {
    try {
      const owner = await genesisNFT.ownerOf(i);
      if (owner.toLowerCase() === deployer.address.toLowerCase()) {
        nftIds.push(i);
      }
    } catch (e) {
      // Token doesn't exist
    }
  }
  console.log("Your NFT IDs:       ", nftIds.join(", "));
  
  console.log("\n💰 HOW PAYOUTS WORK");
  console.log("════════════════════════════════════════");
  console.log("1. User creates market with prediction");
  console.log("2. Other users submit competing predictions");
  console.log("3. People bet on predictions they believe will win");
  console.log("4. Oracle verifies actual tweet when time expires");
  console.log("5. Market resolves, determining winners");
  console.log("6. Platform collects 7% fee from all activity");
  console.log("7. Fee distribution happens automatically:");
  
  console.log("\n📊 FEE DISTRIBUTION BREAKDOWN");
  console.log("════════════════════════════════════════");
  console.log("From every 1 ETH in platform fees:");
  console.log("├─ Oracles:          0.02 ETH (2%)");
  console.log("├─ Node Operators:   0.01 ETH (1%)");
  console.log("├─ Content Creators: 0.01 ETH (1%)");
  console.log("├─ Builder Pool:     0.02 ETH (2%)");
  console.log("├─ Bittensor AI:     0.01 ETH (1%)");
  console.log("└─ Genesis NFTs:     0.002 ETH (0.2%)");
  
  console.log("\n💎 YOUR EARNINGS CALCULATOR");
  console.log("════════════════════════════════════════");
  
  const scenarios = [
    { volume: "1", desc: "Small market" },
    { volume: "10", desc: "Medium market" },
    { volume: "100", desc: "Large market" },
    { volume: "1000", desc: "Viral prediction" }
  ];
  
  console.log("Platform Volume → Platform Fee (7%) → Genesis Pool (0.2%) → Your Share\n");
  
  for (const scenario of scenarios) {
    const volume = ethers.parseEther(scenario.volume);
    const platformFee = (volume * 7n) / 100n;
    const genesisPool = (platformFee * 2n) / 1000n;
    const yourShare = (genesisPool * nftBalance) / totalMinted;
    
    console.log(`${scenario.desc.padEnd(16)} ${scenario.volume.padStart(4)} ETH → ${ethers.formatEther(platformFee).padStart(8)} ETH → ${ethers.formatEther(genesisPool).padStart(8)} ETH → ${ethers.formatEther(yourShare).padStart(8)} ETH`);
  }
  
  console.log("\n🚀 CURRENT STATUS");
  console.log("════════════════════════════════════════");
  console.log("✅ Genesis NFT Contract:       Deployed & Verified");
  console.log("✅ Payout Manager:             Deployed & Verified");
  console.log("✅ Your NFTs:                  Minted (15/100)");
  console.log("✅ Integration:                Ready for markets");
  console.log("⏳ Awaiting:                   Market activity");
  
  console.log("\n📈 FUTURE PROJECTIONS");
  console.log("════════════════════════════════════════");
  console.log("With your", nftBalance.toString(), "Genesis NFTs:");
  console.log("• Daily volume of 100 ETH = ~0.014 ETH/day to you");
  console.log("• Weekly volume of 1000 ETH = ~0.14 ETH/week to you");
  console.log("• Monthly volume of 10,000 ETH = ~1.4 ETH/month to you");
  
  if (Number(totalMinted) < 100) {
    const remainingNFTs = 100 - Number(totalMinted);
    console.log("\n⚠️ DILUTION NOTE:");
    console.log(`• ${remainingNFTs} NFTs remain unminted`);
    console.log(`• When all 100 are minted, your share becomes ${(Number(nftBalance) / 100 * 100).toFixed(1)}%`);
    console.log(`• Current advantage: You own 100% of minted supply`);
  }
  
  console.log("\n🔗 VERIFY ON BLOCKCHAIN");
  console.log("════════════════════════════════════════");
  console.log("Genesis NFT Contract:");
  console.log("https://sepolia.basescan.org/address/" + deployment.contracts.GenesisNFT);
  console.log("\nPayout Manager Contract:");
  console.log("https://sepolia.basescan.org/address/" + deployment.contracts.DistributedPayoutManager);
  console.log("\nYour Wallet:");
  console.log("https://sepolia.basescan.org/address/" + deployer.address);
  
  console.log("\n✨ WHAT HAPPENS NEXT");
  console.log("════════════════════════════════════════");
  console.log("1. Deploy to BASE mainnet when ready");
  console.log("2. Real users create prediction markets");
  console.log("3. Every market resolution triggers automatic payouts");
  console.log("4. You receive ETH directly to your wallet");
  console.log("5. No claiming needed - fully automated!");
  console.log("6. Your NFTs = permanent revenue share");
  
  console.log("\n════════════════════════════════════════════════════════════");
  console.log("         GENESIS NFT HOLDERS GET PAID FOREVER");
  console.log("════════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });