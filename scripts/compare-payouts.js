const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("═══════════════════════════════════════════════════════════");
  console.log("   GENESIS NFT PAYOUT COMPARISON: OLD vs IMPROVED");
  console.log("═══════════════════════════════════════════════════════════\n");
  
  const [deployer] = await ethers.getSigners();
  console.log("Your wallet:", deployer.address);
  
  console.log("\n📊 CURRENT PAYOUT STRUCTURE (Too Low!)");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("Platform Fee: 7% of all market volume");
  console.log("\nFee Distribution:");
  console.log("├─ Oracles:       2.0% of volume (28.6% of fees)");
  console.log("├─ Nodes:         1.0% of volume (14.3% of fees)");
  console.log("├─ Creators:      1.0% of volume (14.3% of fees)");
  console.log("├─ Builder Pool:  2.0% of volume (28.6% of fees)");
  console.log("├─ Bittensor AI:  1.0% of volume (14.3% of fees)");
  console.log("└─ Genesis NFTs:  0.2% of volume (2.8% of fees) ❌ TOO LOW!");
  
  console.log("\n💰 IMPROVED PAYOUT STRUCTURE (Fair Rewards!)");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("Platform Fee: 7% of all market volume");
  console.log("\nFee Distribution:");
  console.log("├─ Genesis NFTs:  1.4% of volume (20% of fees) ✅ MUCH BETTER!");
  console.log("├─ Oracles:       1.4% of volume (20% of fees)");
  console.log("├─ Creators:      1.4% of volume (20% of fees)");
  console.log("├─ Builder Pool:  1.4% of volume (20% of fees)");
  console.log("├─ Nodes:         0.7% of volume (10% of fees)");
  console.log("└─ Bittensor AI:  0.7% of volume (10% of fees)");
  
  console.log("\n💎 YOUR EARNINGS COMPARISON (100 Genesis NFTs)");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("Market Volume    │ Old Payout (0.2%) │ New Payout (1.4%) │ Increase");
  console.log("─────────────────┼───────────────────┼───────────────────┼──────────");
  
  const volumes = [
    { amount: "10", label: "10 ETH" },
    { amount: "100", label: "100 ETH" },
    { amount: "1000", label: "1,000 ETH" },
    { amount: "10000", label: "10,000 ETH" },
    { amount: "100000", label: "100,000 ETH" }
  ];
  
  for (const vol of volumes) {
    const volume = ethers.parseEther(vol.amount);
    
    // Old structure: 0.2% of volume
    const oldPayout = (volume * 2n) / 1000n;
    
    // New structure: 1.4% of volume
    const newPayout = (volume * 14n) / 1000n;
    
    // Increase
    const increase = ((Number(newPayout - oldPayout) / Number(oldPayout)) * 100).toFixed(0);
    
    console.log(
      `${vol.label.padEnd(16)} │ ${ethers.formatEther(oldPayout).padEnd(17)} │ ${ethers.formatEther(newPayout).padEnd(17)} │ ${increase}x more!`
    );
  }
  
  console.log("\n📈 MONTHLY PROJECTIONS (30 days)");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("Daily Volume │ Old Monthly Income │ New Monthly Income");
  console.log("─────────────┼────────────────────┼────────────────────");
  
  const dailyVolumes = [
    { amount: "100", label: "100 ETH/day" },
    { amount: "500", label: "500 ETH/day" },
    { amount: "1000", label: "1,000 ETH/day" }
  ];
  
  for (const daily of dailyVolumes) {
    const dailyVol = ethers.parseEther(daily.amount);
    const monthlyVol = dailyVol * 30n;
    
    const oldMonthly = (monthlyVol * 2n) / 1000n;
    const newMonthly = (monthlyVol * 14n) / 1000n;
    
    console.log(
      `${daily.label.padEnd(12)} │ ${ethers.formatEther(oldMonthly).padEnd(18)} │ ${ethers.formatEther(newMonthly)}`
    );
  }
  
  console.log("\n🎯 WHY YOU DESERVE 1.4% OF VOLUME");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("✅ Early Supporter Risk: You backed the project from day one");
  console.log("✅ 100 NFT Commitment: You're getting ALL 100 Genesis NFTs");
  console.log("✅ Platform Growth: Your support helps bootstrap the ecosystem");
  console.log("✅ Fair Distribution: 20% of fees is reasonable for founders");
  console.log("✅ Aligned Incentives: You profit when the platform succeeds");
  
  console.log("\n💰 REVENUE BREAKDOWN AT SCALE");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("If Clockchain reaches $1M daily volume:");
  console.log("• Platform fees (7%):        $70,000/day");
  console.log("• Genesis share (20% of fees): $14,000/day");
  console.log("• YOUR INCOME (100 NFTs):    $14,000/day = $420,000/month!");
  
  console.log("\n🚀 IMPLEMENTATION PLAN");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("1. Deploy ImprovedDistributedPayoutManager to testnet");
  console.log("2. Test with multiple markets to verify 1.4% payouts");
  console.log("3. Deploy to mainnet with improved percentages");
  console.log("4. You mint all 100 Genesis NFTs");
  console.log("5. Earn 1.4% of all platform volume forever!");
  
  console.log("\n✨ SUMMARY");
  console.log("═══════════════════════════════════════════════════════════");
  console.log("Old payout: 0.2% of volume (way too low for 100% ownership)");
  console.log("New payout: 1.4% of volume (fair reward for Genesis holders)");
  console.log("Improvement: 7X MORE INCOME!");
  console.log("\nThis change ensures Genesis NFT holders are properly rewarded");
  console.log("for their early support and commitment to the platform.");
  console.log("═══════════════════════════════════════════════════════════\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });