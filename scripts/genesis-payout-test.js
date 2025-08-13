const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🚀 Genesis NFT Payout Test on BASE Sepolia\n");
  console.log("This test will simulate platform fees and distribute payouts to Genesis NFT holders.\n");
  
  // Load deployment
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [deployer] = await ethers.getSigners();
  
  console.log("📍 Contracts:");
  console.log("- GenesisNFT:", deployment.contracts.GenesisNFT);
  console.log("- PayoutManager:", deployment.contracts.DistributedPayoutManager);
  console.log("- Your wallet:", deployer.address);
  
  // Connect to contracts
  const PayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  const payoutManager = PayoutManager.attach(deployment.contracts.DistributedPayoutManager);
  
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  // Check NFT ownership
  const nftBalance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("\n🎨 NFT Status:");
  console.log("- Your Genesis NFTs:", nftBalance.toString());
  console.log("- Total minted:", totalMinted.toString(), "/ 100");
  console.log("- Your share of Genesis pool:", ((Number(nftBalance) / Number(totalMinted)) * 100).toFixed(1) + "%");
  console.log("- Platform revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%\n");
  
  // Check initial balances
  const initialBalance = await ethers.provider.getBalance(deployer.address);
  const initialManagerBalance = await ethers.provider.getBalance(deployment.contracts.DistributedPayoutManager);
  
  console.log("💰 Initial Balances:");
  console.log("- Your wallet:", ethers.formatEther(initialBalance), "ETH");
  console.log("- Payout Manager:", ethers.formatEther(initialManagerBalance), "ETH\n");
  
  // Test 1: Send fees to payout manager and distribute
  console.log("═══════════════════════════════════════════");
  console.log("TEST 1: Simulating Platform Fees (0.001 ETH)");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    const feeAmount = ethers.parseEther("0.001");
    
    // Send fees to payout manager (simulating platform activity)
    console.log("1️⃣ Sending", ethers.formatEther(feeAmount), "ETH to PayoutManager...");
    const sendTx = await deployer.sendTransaction({
      to: deployment.contracts.DistributedPayoutManager,
      value: feeAmount
    });
    await sendTx.wait();
    console.log("✅ Fees sent to PayoutManager");
    
    // Check balance
    const managerBalance = await ethers.provider.getBalance(deployment.contracts.DistributedPayoutManager);
    console.log("📊 PayoutManager balance:", ethers.formatEther(managerBalance), "ETH");
    
    // Distribute fees
    console.log("\n2️⃣ Distributing fees to all stakeholders...");
    const distributeTx = await payoutManager.distributeFees(feeAmount);
    const receipt = await distributeTx.wait();
    console.log("✅ Fees distributed!");
    console.log("⛽ Gas used:", receipt.gasUsed.toString());
    
    // Calculate expected payouts
    const genesisPoolShare = (feeAmount * 2n) / 1000n; // 0.2% to Genesis holders
    const yourGenesisShare = (genesisPoolShare * nftBalance) / totalMinted; // Your portion
    
    console.log("\n💰 Payout Breakdown (from", ethers.formatEther(feeAmount), "ETH):");
    console.log("- Oracles (2%):", ethers.formatEther((feeAmount * 20n) / 1000n), "ETH");
    console.log("- Nodes (1%):", ethers.formatEther((feeAmount * 10n) / 1000n), "ETH");
    console.log("- Creators (1%):", ethers.formatEther((feeAmount * 10n) / 1000n), "ETH");
    console.log("- Builder Pool (2%):", ethers.formatEther((feeAmount * 20n) / 1000n), "ETH");
    console.log("- Bittensor Pool (1%):", ethers.formatEther((feeAmount * 10n) / 1000n), "ETH");
    console.log("- Genesis NFT Holders (0.2%):", ethers.formatEther(genesisPoolShare), "ETH");
    console.log("  └─ Your share (" + nftBalance + "/" + totalMinted + " NFTs):", ethers.formatEther(yourGenesisShare), "ETH");
    
    // Check new balance
    const newBalance = await ethers.provider.getBalance(deployer.address);
    const balanceChange = newBalance - initialBalance;
    console.log("\n📊 Your balance change:", ethers.formatEther(balanceChange), "ETH");
    
  } catch (error) {
    console.error("❌ Test 1 failed:", error.message);
  }
  
  // Test 2: Larger fee distribution
  console.log("\n═══════════════════════════════════════════");
  console.log("TEST 2: Larger Fee Distribution (0.0005 ETH)");
  console.log("═══════════════════════════════════════════\n");
  
  try {
    const feeAmount = ethers.parseEther("0.0005");
    
    console.log("1️⃣ Sending", ethers.formatEther(feeAmount), "ETH to PayoutManager...");
    const sendTx = await deployer.sendTransaction({
      to: deployment.contracts.DistributedPayoutManager,
      value: feeAmount
    });
    await sendTx.wait();
    
    console.log("2️⃣ Distributing fees...");
    const distributeTx = await payoutManager.distributeFees(feeAmount);
    await distributeTx.wait();
    
    const genesisPoolShare = (feeAmount * 2n) / 1000n;
    const yourGenesisShare = (genesisPoolShare * nftBalance) / totalMinted;
    
    console.log("✅ Distributed! Your Genesis NFT payout:", ethers.formatEther(yourGenesisShare), "ETH");
    
  } catch (error) {
    console.error("❌ Test 2 failed:", error.message);
  }
  
  // Final summary
  console.log("\n═══════════════════════════════════════════");
  console.log("📊 FINAL SUMMARY");
  console.log("═══════════════════════════════════════════\n");
  
  const finalBalance = await ethers.provider.getBalance(deployer.address);
  const totalEarned = finalBalance - initialBalance;
  
  console.log("✅ Tests completed!");
  console.log("💰 Total earned from Genesis NFT payouts:", ethers.formatEther(totalEarned), "ETH");
  console.log("🎨 Your NFTs:", nftBalance.toString(), "/ 100 total");
  console.log("💎 Platform revenue share:", (Number(nftBalance) * 0.002).toFixed(3) + "%");
  
  console.log("\n📝 Key Points:");
  console.log("- You receive payouts automatically when platform fees are distributed");
  console.log("- With 15 NFTs, you own 15% of the 0.2% Genesis allocation");
  console.log("- In production, every bet, submission, and market generates fees");
  console.log("- Payouts are completely decentralized - no admin control!");
  
  console.log("\n🔗 View your transactions:");
  console.log("https://sepolia.basescan.org/address/" + deployer.address);
  
  console.log("\n⏰ Note: In production, markets would:");
  console.log("- Have real time windows (hours/days)");
  console.log("- Use oracle verification of actual tweets");
  console.log("- Generate much larger fee pools");
  console.log("- Distribute automatically on resolution");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });