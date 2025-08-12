const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🎨 Minting Test NFTs on BASE Sepolia...\n");
  
  // Load deployment info
  const deploymentPath = path.join(__dirname, "..", "deployments", "genesis-phase1-testnet.json");
  
  if (!fs.existsSync(deploymentPath)) {
    console.log("❌ No deployment found! Run: npm run deploy:genesis-testnet");
    process.exit(1);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  console.log("📂 Loaded deployment from:", deployment.network);
  console.log("GenesisNFT:", deployment.contracts.GenesisNFT);
  console.log("PayoutManager:", deployment.contracts.DistributedPayoutManager);
  console.log("\n");
  
  // Get signer
  const [deployer] = await ethers.getSigners();
  console.log("🔐 Minting from:", deployer.address);
  
  // Connect to GenesisNFT contract
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  // Check current status
  const totalMinted = await genesisNFT.totalMinted();
  const isFinalized = await genesisNFT.finalized();
  
  console.log("📊 Current Status:");
  console.log("- Total Minted:", totalMinted.toString(), "/ 100");
  console.log("- Finalized:", isFinalized);
  console.log("\n");
  
  if (isFinalized) {
    console.log("⚠️  Minting has been finalized! No more NFTs can be minted.");
    process.exit(0);
  }
  
  if (totalMinted >= 100n) {
    console.log("⚠️  All 100 NFTs have been minted!");
    process.exit(0);
  }
  
  // Prompt for minting
  console.log("🎯 Test Minting Options:");
  console.log("=====================================");
  console.log("We'll mint test NFTs to different addresses to simulate real usage.\n");
  
  const testAddresses = [
    deployer.address,
    "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", // Test address 1
    "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", // Test address 2
    "0x90F79bf6EB2c4f870365E785982E1f101E93b906", // Test address 3
  ];
  
  const mintAmounts = [5, 3, 2, 5]; // Total: 15 NFTs
  
  console.log("Planned minting:");
  for (let i = 0; i < testAddresses.length; i++) {
    console.log(`- ${mintAmounts[i]} NFTs to ${testAddresses[i]}`);
  }
  console.log("\nTotal to mint: 15 NFTs\n");
  
  // Execute minting
  console.log("🚀 Starting minting process...\n");
  
  for (let i = 0; i < testAddresses.length; i++) {
    try {
      console.log(`Minting ${mintAmounts[i]} NFTs to ${testAddresses[i]}...`);
      const tx = await genesisNFT.mint(testAddresses[i], mintAmounts[i]);
      const receipt = await tx.wait();
      
      console.log(`✅ Minted! Transaction: ${receipt.hash}`);
      console.log(`   Gas used: ${receipt.gasUsed.toString()}`);
      console.log(`   View: https://sepolia.basescan.org/tx/${receipt.hash}\n`);
    } catch (error) {
      console.log(`❌ Failed to mint: ${error.message}\n`);
    }
  }
  
  // Check final status
  const finalMinted = await genesisNFT.totalMinted();
  const finalFinalized = await genesisNFT.finalized();
  
  console.log("📊 Final Status:");
  console.log("=====================================");
  console.log("- Total Minted:", finalMinted.toString(), "/ 100");
  console.log("- Finalized:", finalFinalized);
  console.log("- Remaining Supply:", (100n - finalMinted).toString());
  console.log("\n");
  
  // Generate sample tokenURI for viewing
  if (finalMinted > 0n) {
    console.log("🖼️ Sample NFT Data:");
    try {
      const tokenURI = await genesisNFT.tokenURI(1);
      console.log("Token #1 URI (first 200 chars):");
      console.log(tokenURI.substring(0, 200) + "...\n");
      
      // Decode base64 to show it's valid
      const base64Data = tokenURI.split(",")[1];
      const jsonData = Buffer.from(base64Data, "base64").toString();
      const metadata = JSON.parse(jsonData);
      
      console.log("Token #1 Metadata:");
      console.log("- Name:", metadata.name);
      console.log("- Description:", metadata.description);
      console.log("- Image Type:", metadata.image.substring(0, 30) + "...");
    } catch (error) {
      console.log("Error fetching token data:", error.message);
    }
  }
  
  console.log("\n✅ Test minting complete!");
  console.log("\n🔍 View NFT Collection:");
  console.log(`https://sepolia.basescan.org/address/${deployment.contracts.GenesisNFT}#tokentxns`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });