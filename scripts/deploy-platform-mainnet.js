const hre = require("hardhat");
const { ethers } = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("=======================================================");
  console.log("🚀 DEPLOYING PLATFORM CONTRACTS TO BASE MAINNET");
  console.log("=======================================================\n");

  // Safety check - ensure we're on BASE mainnet
  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 8453n) {
    throw new Error(`❌ Not connected to BASE mainnet! Connected to chainId: ${network.chainId}`);
  }
  console.log("✅ Connected to BASE Mainnet (chainId: 8453)\n");

  // Load previous deployments
  let genesisAddress, payoutAddress;
  try {
    const deployment = JSON.parse(
      fs.readFileSync('deployments/base-mainnet-genesis.json', 'utf8')
    );
    genesisAddress = deployment.contracts.GenesisNFT;
    payoutAddress = deployment.contracts.ImprovedDistributedPayoutManager;
    console.log("✅ Loaded Genesis NFT:", genesisAddress);
    console.log("✅ Loaded PayoutManager:", payoutAddress);
  } catch (error) {
    console.error("❌ Error loading previous deployments");
    console.log("Please deploy Genesis NFT and PayoutManager first");
    process.exit(1);
  }

  // Get deployer account
  let deployer;
  try {
    const accounts = await ethers.getSigners();
    deployer = accounts[0];
    console.log("Deployer address:", deployer.address);

    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Deployer balance:", ethers.formatEther(balance), "ETH\n");

    if (balance < ethers.parseEther("0.3")) {
      console.log("⚠️  WARNING: Deployer has less than 0.3 ETH!");
      console.log("Recommended minimum: 0.3 ETH for platform deployment");
      process.exit(1);
    }
  } catch (error) {
    console.error("❌ Error getting deployer account:", error.message);
    process.exit(1);
  }

  // 10 second safety delay
  console.log("⚠️  Deploying CORE PLATFORM to MAINNET");
  console.log("Press Ctrl+C to cancel...");
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Get gas price
  const feeData = await ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice;
  console.log("\nGas price:", ethers.formatUnits(gasPrice, "gwei"), "gwei\n");

  // Deploy ActorRegistry
  console.log("1️⃣  Deploying ActorRegistry...");
  const ActorRegistry = await ethers.getContractFactory("ActorRegistry");
  const actorRegistry = await ActorRegistry.deploy({ gasPrice });
  await actorRegistry.waitForDeployment();
  const actorRegistryAddress = await actorRegistry.getAddress();
  console.log("✅ ActorRegistry deployed to:", actorRegistryAddress);

  // Deploy NodeRegistry
  console.log("\n2️⃣  Deploying NodeRegistry...");
  const NodeRegistry = await ethers.getContractFactory("NodeRegistry");
  const nodeRegistry = await NodeRegistry.deploy({ gasPrice });
  await nodeRegistry.waitForDeployment();
  const nodeRegistryAddress = await nodeRegistry.getAddress();
  console.log("✅ NodeRegistry deployed to:", nodeRegistryAddress);

  // Deploy DecentralizedOracle
  console.log("\n3️⃣  Deploying DecentralizedOracle...");
  const DecentralizedOracle = await ethers.getContractFactory("DecentralizedOracle");
  const oracle = await DecentralizedOracle.deploy(nodeRegistryAddress, { gasPrice });
  await oracle.waitForDeployment();
  const oracleAddress = await oracle.getAddress();
  console.log("✅ DecentralizedOracle deployed to:", oracleAddress);

  // Deploy EnhancedPredictionMarket
  console.log("\n4️⃣  Deploying EnhancedPredictionMarket...");
  const EnhancedPredictionMarket = await ethers.getContractFactory("EnhancedPredictionMarket");
  const predictionMarket = await EnhancedPredictionMarket.deploy(
    actorRegistryAddress,
    oracleAddress,
    payoutAddress,
    { gasPrice }
  );
  await predictionMarket.waitForDeployment();
  const marketAddress = await predictionMarket.getAddress();
  console.log("✅ EnhancedPredictionMarket deployed to:", marketAddress);

  console.log("\n📊 Deployment Summary:");
  console.log("=====================================");
  console.log("Network: BASE Mainnet (chainId: 8453)");
  console.log("Deployer:", deployer.address);
  console.log("\nContract Addresses:");
  console.log("- EnhancedPredictionMarket:", marketAddress);
  console.log("- DecentralizedOracle:", oracleAddress);
  console.log("- ActorRegistry:", actorRegistryAddress);
  console.log("- NodeRegistry:", nodeRegistryAddress);
  console.log("\nPreviously Deployed:");
  console.log("- GenesisNFT:", genesisAddress);
  console.log("- PayoutManager:", payoutAddress);
  console.log("=====================================");

  // Save deployment
  const deployment = {
    network: "base-mainnet",
    chainId: 8453,
    deployer: deployer.address,
    deploymentTime: new Date().toISOString(),
    contracts: {
      EnhancedPredictionMarket: marketAddress,
      DecentralizedOracle: oracleAddress,
      ActorRegistry: actorRegistryAddress,
      NodeRegistry: nodeRegistryAddress,
      ImprovedDistributedPayoutManager: payoutAddress,
      GenesisNFT: genesisAddress
    }
  };

  fs.writeFileSync(
    'deployments/base-mainnet.json',
    JSON.stringify(deployment, null, 2)
  );
  console.log("\n✅ Full deployment info saved to deployments/base-mainnet.json");

  // Verify contracts on Basescan
  if (process.env.BASESCAN_API_KEY) {
    console.log("\n5️⃣  Verifying contracts on Basescan...");
    console.log("Waiting 30 seconds for Basescan to index...\n");
    await new Promise(resolve => setTimeout(resolve, 30000));

    const verificationsToRun = [
      {
        name: "ActorRegistry",
        address: actorRegistryAddress,
        args: []
      },
      {
        name: "NodeRegistry",
        address: nodeRegistryAddress,
        args: []
      },
      {
        name: "DecentralizedOracle",
        address: oracleAddress,
        args: [nodeRegistryAddress]
      },
      {
        name: "EnhancedPredictionMarket",
        address: marketAddress,
        args: [actorRegistryAddress, oracleAddress, payoutAddress]
      }
    ];

    for (const verification of verificationsToRun) {
      try {
        console.log(`Verifying ${verification.name}...`);
        await hre.run("verify:verify", {
          address: verification.address,
          constructorArguments: verification.args,
          network: "base"
        });
        console.log(`✅ ${verification.name} verified`);
      } catch (error) {
        console.log(`⚠️  ${verification.name} verification failed:`, error.message);
      }
    }
  } else {
    console.log("\n⚠️  BASESCAN_API_KEY not set - skipping verification");
  }

  console.log("\n🎉 Platform Deployment Complete!");
  console.log("\nView contracts on Basescan:");
  console.log(`- Market: https://basescan.org/address/${marketAddress}`);
  console.log(`- Oracle: https://basescan.org/address/${oracleAddress}`);
  console.log(`- ActorRegistry: https://basescan.org/address/${actorRegistryAddress}`);
  console.log(`- NodeRegistry: https://basescan.org/address/${nodeRegistryAddress}`);

  console.log("\n📋 Next Steps:");
  console.log("1. Verify all contracts on Basescan (if not done automatically)");
  console.log("2. Initialize platform: npx hardhat run scripts/initialize-mainnet.js --network base");
  console.log("3. Register initial actors (top 10 Twitter accounts)");
  console.log("4. Set up oracle nodes (minimum 3)");
  console.log("5. Test market creation with small amount (0.001 ETH)");
  console.log("6. Deploy frontend with contract addresses");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Deployment failed:", error);
    process.exit(1);
  });
