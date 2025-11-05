const hre = require("hardhat");
const { ethers } = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("========================================");
  console.log("🚀 DEPLOYING GENESIS NFT TO BASE MAINNET");
  console.log("========================================\n");

  // Safety check - ensure we're on BASE mainnet
  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 8453n) {
    throw new Error(`❌ Not connected to BASE mainnet! Connected to chainId: ${network.chainId}`);
  }
  console.log("✅ Connected to BASE Mainnet (chainId: 8453)\n");

  // Get deployer account
  let deployer;
  try {
    const accounts = await ethers.getSigners();
    deployer = accounts[0];
    console.log("Deployer address:", deployer.address);

    // Check balance
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Deployer balance:", ethers.formatEther(balance), "ETH");

    if (balance < ethers.parseEther("0.5")) {
      console.log("\n⚠️  WARNING: Deployer has less than 0.5 ETH!");
      console.log("Recommended minimum: 0.5 ETH for Genesis NFT deployment");
      console.log("Please fund this address with BASE ETH first.");
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Error getting deployer account:", error.message);
    console.log("\nPlease ensure DEPLOYER_PRIVATE_KEY is set correctly in .env");
    process.exit(1);
  }

  // 10 second safety delay
  console.log("\n⚠️  FINAL WARNING: Deploying to MAINNET");
  console.log("Press Ctrl+C to cancel...");
  await new Promise(resolve => setTimeout(resolve, 10000));

  console.log("\n1️⃣  Deploying GenesisNFT...");
  const GenesisNFT = await ethers.getContractFactory("GenesisNFT");

  // Get gas price and estimate
  const feeData = await ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice;
  console.log("Gas price:", ethers.formatUnits(gasPrice, "gwei"), "gwei");

  const genesisNFT = await GenesisNFT.deploy({
    gasPrice: gasPrice
  });
  await genesisNFT.waitForDeployment();
  const genesisAddress = await genesisNFT.getAddress();
  console.log("✅ GenesisNFT deployed to:", genesisAddress);

  // Get deployment info
  const maxSupply = await genesisNFT.MAX_SUPPLY();
  const mintPrice = await genesisNFT.mintPrice();
  const totalMinted = await genesisNFT.totalMinted();
  const isMintingActive = await genesisNFT.isMintingActive();

  console.log("\n📊 Deployment Summary:");
  console.log("=====================================");
  console.log("Network: BASE Mainnet (chainId: 8453)");
  console.log("Deployer:", deployer.address);
  console.log("\nContract Address:");
  console.log("- GenesisNFT:", genesisAddress);
  console.log("\nNFT Configuration:");
  console.log("- Max Supply:", maxSupply.toString());
  console.log("- Mint Price:", ethers.formatEther(mintPrice), "ETH");
  console.log("- Total Minted:", totalMinted.toString());
  console.log("- Minting Active:", isMintingActive);
  console.log("=====================================");

  // Save deployment addresses
  const deployment = {
    network: "base-mainnet",
    chainId: 8453,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      GenesisNFT: genesisAddress
    },
    nftConfig: {
      maxSupply: maxSupply.toString(),
      mintPrice: ethers.formatEther(mintPrice),
      totalMinted: totalMinted.toString(),
      isMintingActive: isMintingActive
    }
  };

  // Create deployments directory if it doesn't exist
  if (!fs.existsSync('deployments')) {
    fs.mkdirSync('deployments', { recursive: true });
  }

  fs.writeFileSync(
    'deployments/base-mainnet-genesis.json',
    JSON.stringify(deployment, null, 2)
  );
  console.log("\n✅ Deployment info saved to deployments/base-mainnet-genesis.json");

  // Verify contract on Basescan
  if (process.env.BASESCAN_API_KEY) {
    console.log("\n2️⃣  Verifying GenesisNFT on Basescan...");
    console.log("Waiting 30 seconds for Basescan to index the contract...");
    await new Promise(resolve => setTimeout(resolve, 30000));

    try {
      await hre.run("verify:verify", {
        address: genesisAddress,
        constructorArguments: [],
        network: "base"
      });
      console.log("✅ GenesisNFT verified on Basescan");
    } catch (error) {
      console.log("⚠️  Verification failed:", error.message);
      console.log("You can verify manually later with:");
      console.log(`npx hardhat verify --network base ${genesisAddress}`);
    }
  } else {
    console.log("\n⚠️  BASESCAN_API_KEY not set - skipping verification");
    console.log("Verify manually with:");
    console.log(`npx hardhat verify --network base ${genesisAddress}`);
  }

  console.log("\n🎉 Genesis NFT Deployment Complete!");
  console.log("\nView on Basescan:");
  console.log(`https://basescan.org/address/${genesisAddress}`);
  console.log("\n📋 Next Steps:");
  console.log("1. Verify the contract on Basescan (if not done automatically)");
  console.log("2. Test mint 1 NFT to confirm functionality");
  console.log("3. Deploy PayoutManager: npx hardhat run scripts/deploy-payout-mainnet.js --network base");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:", error);
    process.exit(1);
  });
