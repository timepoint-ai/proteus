const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  const [deployer] = await ethers.getSigners();
  const deployment = JSON.parse(fs.readFileSync("deployments/genesis-phase1-testnet.json"));
  
  const genesisNFT = await ethers.getContractAt("GenesisNFT", deployment.contracts.GenesisNFT);
  const balance = await genesisNFT.balanceOf(deployer.address);
  const totalMinted = await genesisNFT.totalMinted();
  
  console.log("Your address:", deployer.address);
  console.log("Your Genesis NFT balance:", balance.toString());
  console.log("Total NFTs minted:", totalMinted.toString());
  
  // Get token IDs
  const tokenIds = [];
  for (let i = 0; i < balance; i++) {
    try {
      const tokenId = await genesisNFT.tokenOfOwnerByIndex(deployer.address, i);
      tokenIds.push(tokenId.toString());
    } catch {
      break;
    }
  }
  console.log("Your token IDs:", tokenIds);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
