const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying Genesis NFT contracts to BASE Sepolia...\n");

  // Get deployer account
  let deployer;
  try {
    const accounts = await ethers.getSigners();
    deployer = accounts[0];
    console.log("Deployer address:", deployer.address);
    
    // Check balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Deployer balance:", ethers.formatEther(balance), "ETH");
    
    if (balance === 0n) {
      console.log("\n⚠️  WARNING: Deployer has no ETH!");
      console.log("Please fund this address with BASE Sepolia ETH:");
      console.log("https://docs.base.org/tools/network-faucets/");
      console.log("Address:", deployer.address);
      process.exit(1);
    }
  } catch (error) {
    console.error("Error getting deployer account:", error.message);
    console.log("\nPlease ensure DEPLOYER_PRIVATE_KEY is set correctly");
    process.exit(1);
  }

  console.log("\n1. Deploying Mock PredictionMarket...");
  const MockPredictionMarket = await ethers.getContractFactory("MockPredictionMarket");
  const mockMarket = await MockPredictionMarket.deploy();
  await mockMarket.waitForDeployment();
  const mockMarketAddress = await mockMarket.getAddress();
  console.log("✅ MockPredictionMarket deployed to:", mockMarketAddress);

  console.log("\n2. Deploying GenesisNFT...");
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
  const genesisNFT = await GenesisNFT.deploy();
  await genesisNFT.waitForDeployment();
  const genesisAddress = await genesisNFT.getAddress();
  console.log("✅ GenesisNFT deployed to:", genesisAddress);

  console.log("\n3. Deploying DistributedPayoutManager...");
  const DistributedPayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  // For now, use zero addresses for builder and bittensor pools (will be deployed later)
  const builderPoolAddress = ethers.ZeroAddress;
  const bittensorPoolAddress = ethers.ZeroAddress;
  
  const payoutManager = await DistributedPayoutManager.deploy(
    mockMarketAddress,
    builderPoolAddress,
    bittensorPoolAddress,
    genesisAddress
  );
  await payoutManager.waitForDeployment();
  const payoutAddress = await payoutManager.getAddress();
  console.log("✅ DistributedPayoutManager deployed to:", payoutAddress);

  // Mint some test NFTs
  console.log("\n4. Minting test NFTs...");
  const mintTx = await genesisNFT.mint(deployer.address, 10);
  await mintTx.wait();
  console.log("✅ Minted 10 NFTs to deployer");

  // Get deployment info
  const totalMinted = await genesisNFT.totalMinted();
  const remainingSupply = await genesisNFT.remainingSupply();
  const isMintingActive = await genesisNFT.isMintingActive();

  console.log("\n📊 Deployment Summary:");
  console.log("=====================================");
  console.log("Network: BASE Sepolia (chainId: 84532)");
  console.log("Deployer:", deployer.address);
  console.log("\nContract Addresses:");
  console.log("- GenesisNFT:", genesisAddress);
  console.log("- DistributedPayoutManager:", payoutAddress);
  console.log("- MockPredictionMarket:", mockMarketAddress);
  console.log("\nNFT Status:");
  console.log("- Total Minted:", totalMinted.toString(), "/ 100");
  console.log("- Remaining Supply:", remainingSupply.toString());
  console.log("- Minting Active:", isMintingActive);
  console.log("=====================================");

  // Save deployment addresses
  const deployment = {
    network: "base-sepolia",
    chainId: 84532,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      GenesisNFT: genesisAddress,
      DistributedPayoutManager: payoutAddress,
      MockPredictionMarket: mockMarketAddress
    },
    nftStatus: {
      totalMinted: totalMinted.toString(),
      remainingSupply: remainingSupply.toString(),
      isMintingActive: isMintingActive
    }
  };

  const fs = require('fs');
  fs.writeFileSync(
    'deployments/genesis-phase1-testnet.json',
    JSON.stringify(deployment, null, 2)
  );
  console.log("\n✅ Deployment info saved to deployments/genesis-phase1-testnet.json");

  // Verify contracts on Basescan (optional)
  if (process.env.BASESCAN_API_KEY) {
    console.log("\n5. Verifying contracts on Basescan...");
    try {
      await hre.run("verify:verify", {
        address: genesisAddress,
        constructorArguments: [],
      });
      console.log("✅ GenesisNFT verified");
    } catch (error) {
      console.log("⚠️  GenesisNFT verification failed:", error.message);
    }

    try {
      await hre.run("verify:verify", {
        address: payoutAddress,
        constructorArguments: [mockMarketAddress, genesisAddress],
      });
      console.log("✅ DistributedPayoutManager verified");
    } catch (error) {
      console.log("⚠️  DistributedPayoutManager verification failed:", error.message);
    }
  }

  console.log("\n🎉 Deployment complete!");
  console.log("\nView on Basescan:");
  console.log(`https://sepolia.basescan.org/address/${genesisAddress}`);
  console.log(`https://sepolia.basescan.org/address/${payoutAddress}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });