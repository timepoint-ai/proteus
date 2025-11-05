const hre = require("hardhat");
const { ethers } = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("=======================================================");
  console.log("🚀 DEPLOYING PAYOUT MANAGER TO BASE MAINNET");
  console.log("=======================================================\n");

  // Safety check - ensure we're on BASE mainnet
  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 8453n) {
    throw new Error(`❌ Not connected to BASE mainnet! Connected to chainId: ${network.chainId}`);
  }
  console.log("✅ Connected to BASE Mainnet (chainId: 8453)\n");

  // Load Genesis NFT deployment
  let genesisAddress;
  try {
    const genesisDeployment = JSON.parse(
      fs.readFileSync('deployments/base-mainnet-genesis.json', 'utf8')
    );
    genesisAddress = genesisDeployment.contracts.GenesisNFT;
    console.log("✅ Loaded Genesis NFT address:", genesisAddress);
  } catch (error) {
    console.error("❌ Error loading Genesis NFT deployment");
    console.log("Please deploy Genesis NFT first: npx hardhat run scripts/deploy-genesis-mainnet.js --network base");
    process.exit(1);
  }

  // Get deployer account
  let deployer;
  try {
    const accounts = await ethers.getSigners();
    deployer = accounts[0];
    console.log("Deployer address:", deployer.address);

    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Deployer balance:", ethers.formatEther(balance), "ETH");

    if (balance < ethers.parseEther("0.1")) {
      console.log("\n⚠️  WARNING: Deployer has less than 0.1 ETH!");
      console.log("Recommended minimum: 0.1 ETH for PayoutManager deployment");
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Error getting deployer account:", error.message);
    process.exit(1);
  }

  // 10 second safety delay
  console.log("\n⚠️  Deploying to MAINNET");
  console.log("Press Ctrl+C to cancel...");
  await new Promise(resolve => setTimeout(resolve, 10000));

  console.log("\n1️⃣  Deploying ImprovedDistributedPayoutManager...");

  // Get the EnhancedPredictionMarket address (will be deployed in next step, use placeholder for now)
  // NOTE: This will need to be updated after platform deployment
  const tempMarketAddress = ethers.ZeroAddress; // Placeholder - will be set after platform deployment

  // Builder and Bittensor pool addresses (use zero address for Phase 1)
  const builderPoolAddress = ethers.ZeroAddress;
  const bittensorPoolAddress = ethers.ZeroAddress;

  const ImprovedDistributedPayoutManager = await ethers.getContractFactory("ImprovedDistributedPayoutManager");

  // Get gas price
  const feeData = await ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice;
  console.log("Gas price:", ethers.formatUnits(gasPrice, "gwei"), "gwei");

  const payoutManager = await ImprovedDistributedPayoutManager.deploy(
    tempMarketAddress,
    builderPoolAddress,
    bittensorPoolAddress,
    genesisAddress,
    {
      gasPrice: gasPrice
    }
  );

  await payoutManager.waitForDeployment();
  const payoutAddress = await payoutManager.getAddress();
  console.log("✅ ImprovedDistributedPayoutManager deployed to:", payoutAddress);

  // Get configuration
  const genesisNFTFromContract = await payoutManager.genesisNFT();
  const genesisCutBps = await payoutManager.GENESIS_CUT_BPS();

  console.log("\n📊 Deployment Summary:");
  console.log("=====================================");
  console.log("Network: BASE Mainnet (chainId: 8453)");
  console.log("Deployer:", deployer.address);
  console.log("\nContract Addresses:");
  console.log("- PayoutManager:", payoutAddress);
  console.log("- Genesis NFT:", genesisNFTFromContract);
  console.log("\nConfiguration:");
  console.log("- Genesis Cut:", (Number(genesisCutBps) / 100).toFixed(2) + "%");
  console.log("- Builder Pool:", builderPoolAddress);
  console.log("- Bittensor Pool:", bittensorPoolAddress);
  console.log("=====================================");

  // Save deployment
  const deployment = JSON.parse(
    fs.readFileSync('deployments/base-mainnet-genesis.json', 'utf8')
  );

  deployment.contracts.ImprovedDistributedPayoutManager = payoutAddress;
  deployment.payoutConfig = {
    genesisNFT: genesisNFTFromContract,
    genesisCut: (Number(genesisCutBps) / 100).toFixed(2) + "%",
    builderPool: builderPoolAddress,
    bittensorPool: bittensorPoolAddress
  };
  deployment.lastUpdated = new Date().toISOString();

  fs.writeFileSync(
    'deployments/base-mainnet-genesis.json',
    JSON.stringify(deployment, null, 2)
  );
  console.log("\n✅ Deployment info saved");

  // Verify contract on Basescan
  if (process.env.BASESCAN_API_KEY) {
    console.log("\n2️⃣  Verifying PayoutManager on Basescan...");
    console.log("Waiting 30 seconds for Basescan to index...");
    await new Promise(resolve => setTimeout(resolve, 30000));

    try {
      await hre.run("verify:verify", {
        address: payoutAddress,
        constructorArguments: [
          tempMarketAddress,
          builderPoolAddress,
          bittensorPoolAddress,
          genesisAddress
        ],
        network: "base"
      });
      console.log("✅ PayoutManager verified on Basescan");
    } catch (error) {
      console.log("⚠️  Verification failed:", error.message);
      console.log("Verify manually with:");
      console.log(`npx hardhat verify --network base ${payoutAddress} ${tempMarketAddress} ${builderPoolAddress} ${bittensorPoolAddress} ${genesisAddress}`);
    }
  }

  console.log("\n🎉 PayoutManager Deployment Complete!");
  console.log("\nView on Basescan:");
  console.log(`https://basescan.org/address/${payoutAddress}`);
  console.log("\n📋 Next Steps:");
  console.log("1. Verify the contract on Basescan (if not done automatically)");
  console.log("2. Deploy platform contracts: npx hardhat run scripts/deploy-platform-mainnet.js --network base");
  console.log("3. Update PayoutManager with correct PredictionMarket address");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:", error);
    process.exit(1);
  });
