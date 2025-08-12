const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🎨 Minting Genesis NFTs on BASE Sepolia...\n");
  
  // Load deployment
  const deploymentPath = path.join(__dirname, "..", "deployments", "genesis-phase1-testnet.json");
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  
  console.log("📍 GenesisNFT:", deployment.contracts.GenesisNFT);
  
  // Get signer
  const [deployer] = await ethers.getSigners();
  console.log("👤 Your wallet:", deployer.address);
  
  // Connect to contract
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  // Check status
  const totalMinted = await genesisNFT.totalMinted();
  const remainingSupply = await genesisNFT.remainingSupply();
  
  console.log("\n📊 Current Status:");
  console.log("- Already minted:", totalMinted.toString(), "/ 100");
  console.log("- Remaining:", remainingSupply.toString());
  
  if (remainingSupply === 0n) {
    console.log("\n✅ All 100 NFTs have been minted!");
    return;
  }
  
  // Mint more NFTs
  const amountToMint = 10n; // Mint 10 more
  console.log("\n🚀 Minting", amountToMint.toString(), "more NFTs to your wallet...");
  
  try {
    const tx = await genesisNFT.mint(deployer.address, amountToMint);
    const receipt = await tx.wait();
    
    console.log("\n✅ SUCCESS! Minted", amountToMint.toString(), "NFTs");
    console.log("📝 Transaction:", receipt.hash);
    console.log("⛽ Gas used:", ethers.formatEther(receipt.gasUsed * receipt.gasPrice), "ETH");
    
    // Check new totals
    const newTotal = await genesisNFT.totalMinted();
    const newRemaining = await genesisNFT.remainingSupply();
    
    console.log("\n📊 Updated Status:");
    console.log("- Total minted:", newTotal.toString(), "/ 100");
    console.log("- Remaining:", newRemaining.toString());
    
    // Show NFT metadata
    console.log("\n🖼️ Your NFT Collection:");
    console.log("View on Basescan:");
    console.log(`https://sepolia.basescan.org/address/${deployment.contracts.GenesisNFT}#tokentxns`);
    
    // Get one tokenURI as sample
    try {
      const tokenURI = await genesisNFT.tokenURI(1);
      const base64Data = tokenURI.split(",")[1];
      const jsonData = Buffer.from(base64Data, "base64").toString();
      const metadata = JSON.parse(jsonData);
      
      console.log("\n🎨 NFT #1 Details:");
      console.log("- Name:", metadata.name);
      console.log("- Reward:", "0.002% of platform revenue forever");
      console.log("- On-chain SVG art");
    } catch (e) {
      // Ignore tokenURI errors
    }
    
  } catch (error) {
    console.error("\n❌ Minting failed:", error.message);
    console.log("\nPossible issues:");
    console.log("1. Not enough ETH for gas");
    console.log("2. Max per wallet limit reached");
    console.log("3. Network congestion");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });