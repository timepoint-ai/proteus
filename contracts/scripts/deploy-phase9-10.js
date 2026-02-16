const hre = require("hardhat");

async function main() {
  console.log("Starting Proteus Markets Phase 9 & 10 deployment to BASE Sepolia...");

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Phase 9: Deploy ActorRegistry
  console.log("\n=== Phase 9: Deploying ActorRegistry ===");
  
  // First, we need the NodeRegistry address
  const nodeRegistryAddress = process.env.NODE_REGISTRY_ADDRESS || "0xa1234554321B86b1f3f24A9151B8cbaE5C8BDb75";
  console.log("Using NodeRegistry at:", nodeRegistryAddress);

  const ActorRegistry = await hre.ethers.getContractFactory("ActorRegistry");
  const actorRegistry = await ActorRegistry.deploy(nodeRegistryAddress);
  await actorRegistry.deployed();
  console.log("ActorRegistry deployed to:", actorRegistry.address);

  // Phase 10: Deploy EnhancedPredictionMarket
  console.log("\n=== Phase 10: Deploying EnhancedPredictionMarket ===");
  
  const EnhancedPredictionMarket = await hre.ethers.getContractFactory("EnhancedPredictionMarket");
  const enhancedMarket = await EnhancedPredictionMarket.deploy(actorRegistry.address);
  await enhancedMarket.deployed();
  console.log("EnhancedPredictionMarket deployed to:", enhancedMarket.address);

  // Deploy updated ClockchainOracle that works with new contracts (legacy contract name)
  console.log("\n=== Deploying Enhanced ClockchainOracle ===");
  
  const ClockchainOracle = await hre.ethers.getContractFactory("ClockchainOracle");
  const oracle = await ClockchainOracle.deploy(enhancedMarket.address);
  await oracle.deployed();
  console.log("Enhanced ClockchainOracle deployed to:", oracle.address);

  // Deploy updated PayoutManager
  console.log("\n=== Deploying Enhanced PayoutManager ===");
  
  const PayoutManager = await hre.ethers.getContractFactory("PayoutManager");
  const payoutManager = await PayoutManager.deploy(enhancedMarket.address, oracle.address);
  await payoutManager.deployed();
  console.log("Enhanced PayoutManager deployed to:", payoutManager.address);

  // Grant necessary roles
  console.log("\n=== Setting up roles and permissions ===");

  // Grant ADMIN_ROLE to deployer for ActorRegistry
  const ADMIN_ROLE = await actorRegistry.ADMIN_ROLE();
  await actorRegistry.grantRole(ADMIN_ROLE, deployer.address);
  console.log("Granted ADMIN_ROLE to deployer on ActorRegistry");

  // Summary
  console.log("\n=== Deployment Summary ===");
  console.log("ActorRegistry:", actorRegistry.address);
  console.log("EnhancedPredictionMarket:", enhancedMarket.address);
  console.log("Enhanced ClockchainOracle:", oracle.address);
  console.log("Enhanced PayoutManager:", payoutManager.address);
  
  console.log("\n=== Next Steps ===");
  console.log("1. Update .env with new contract addresses");
  console.log("2. Verify contracts on BaseScan");
  console.log("3. Migrate existing actors to ActorRegistry");
  console.log("4. Update backend services to use new contracts");
  console.log("5. Run integration tests");

  // Save deployment info
  const fs = require('fs');
  const deploymentInfo = {
    network: hre.network.name,
    chainId: (await deployer.provider.getNetwork()).chainId,
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      ActorRegistry: actorRegistry.address,
      EnhancedPredictionMarket: enhancedMarket.address,
      EnhancedClockchainOracle: oracle.address,
      EnhancedPayoutManager: payoutManager.address
    }
  };

  fs.writeFileSync(
    `./deployments/phase9-10-${hre.network.name}-${Date.now()}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );
  console.log("\nDeployment info saved to deployments/ directory");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });