const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🔍 Checking Genesis NFT Ownership\n");
  
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  const [signer] = await ethers.getSigners();
  
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const nft = GenesisNFT.attach(deployment.contracts.GenesisNFT);
  
  const balance = await nft.balanceOf(signer.address);
  const total = await nft.totalMinted();
  
  console.log("📍 Contract:", deployment.contracts.GenesisNFT);
  console.log("👤 Your wallet:", signer.address);
  console.log("🎨 Your NFTs:", balance.toString());
  console.log("📊 Total minted:", total.toString() + "/100\n");
  
  if (balance > 0n) {
    console.log("✅ You own", balance.toString(), "Genesis NFTs!");
    console.log("💰 Revenue share:", (Number(balance) * 0.002).toFixed(3) + "%\n");
    
    console.log("Token IDs you own:");
    for (let i = 0; i < Math.min(5, Number(balance)); i++) {
      const tokenId = await nft.tokenOfOwnerByIndex(signer.address, i);
      console.log("  #" + tokenId);
    }
    if (balance > 5n) console.log("  ... and", (Number(balance) - 5), "more");
  }
  
  console.log("\n🔗 View on Basescan:");
  console.log("https://sepolia.basescan.org/token/" + deployment.contracts.GenesisNFT);
}

main().catch(console.error);