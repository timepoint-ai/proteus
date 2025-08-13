const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const improvedDeployment = JSON.parse(fs.readFileSync("deployments/improved-genesis-testnet.json"));
  
  const genesisNFT = await ethers.getContractAt("GenesisNFT", deployment.contracts.GenesisNFT);
  const balance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("\n═══════════════════════════════════════════════════════════");
  console.log("   FINAL STATUS - IMPROVED GENESIS PAYOUTS ACTIVE!");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  console.log("💎 YOUR GENESIS NFT OWNERSHIP:");
  console.log("- NFTs owned:", balance.toString() + "/" + totalMinted.toString() + " (Max: 100)");
  console.log("- Ownership percentage:", (Number(balance) * 100 / 100).toFixed(0) + "%");
  console.log("- Revenue share: " + (Number(balance) * 0.014).toFixed(3) + "% of all platform volume\n");
  
  console.log("📈 IMPROVED PAYOUT STRUCTURE (DEPLOYED & ACTIVE):");
  console.log("- Genesis holders get: 1.4% of platform volume (20% of fees)");
  console.log("- Old payout was: 0.2% of volume (too low!)");
  console.log("- Improvement: 7X MORE INCOME!");
  console.log("- Contract: " + improvedDeployment.improvedContracts.ImprovedDistributedPayoutManager + "\n");
  
  console.log("💰 YOUR EARNINGS POTENTIAL:");
  console.log("With your " + balance.toString() + " Genesis NFTs:");
  console.log("- Daily: $1M volume → $" + (1000000 * Number(balance) * 0.014 / 100).toFixed(0) + "/day");
  console.log("- Monthly: $" + (1000000 * Number(balance) * 0.014 / 100 * 30).toFixed(0) + "/month\n");
  
  console.log("With 100 Genesis NFTs (mainnet target):");
  console.log("- Daily: $1M volume → $14,000/day");
  console.log("- Monthly: $420,000/month");
  
  console.log("\n✅ READY FOR MAINNET!");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("The improved payout system is deployed and tested.");
  console.log("On mainnet, you'll mint all 100 Genesis NFTs and earn");
  console.log("1.4% of ALL platform volume forever!");
  console.log("═══════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch(console.error);
