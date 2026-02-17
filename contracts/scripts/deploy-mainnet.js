const hre = require("hardhat");

async function main() {
  console.log("Starting Proteus deployment to BASE Mainnet...");
  console.log("⚠️  WARNING: This is a mainnet deployment!");
  
  // Safety check
  const network = await hre.ethers.provider.getNetwork();
  if (network.chainId !== 8453) {
    throw new Error("Not connected to BASE mainnet!");
  }

  // Get the deployer account
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", hre.ethers.utils.formatEther(await deployer.getBalance()), "ETH");

  // Confirmation prompt
  console.log("\nPress Ctrl+C to cancel or wait 10 seconds to continue...");
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Deploy PredictionMarket
  console.log("\n1. Deploying PredictionMarket...");
  const PredictionMarket = await hre.ethers.getContractFactory("PredictionMarket");
  const predictionMarket = await PredictionMarket.deploy();
  await predictionMarket.deployed();
  console.log("PredictionMarket deployed to:", predictionMarket.address);

  // Deploy ClockchainOracle (legacy contract name — deployed on-chain as ClockchainOracle)
  console.log("\n2. Deploying ClockchainOracle...");
  const ClockchainOracle = await hre.ethers.getContractFactory("ClockchainOracle");
  const oracle = await ClockchainOracle.deploy(predictionMarket.address);
  await oracle.deployed();
  console.log("ClockchainOracle deployed to:", oracle.address);

  // Deploy NodeRegistry
  console.log("\n3. Deploying NodeRegistry...");
  const NodeRegistry = await hre.ethers.getContractFactory("NodeRegistry");
  const nodeRegistry = await NodeRegistry.deploy();
  await nodeRegistry.deployed();
  console.log("NodeRegistry deployed to:", nodeRegistry.address);

  // Deploy PayoutManager
  console.log("\n4. Deploying PayoutManager...");
  const PayoutManager = await hre.ethers.getContractFactory("PayoutManager");
  const payoutManager = await PayoutManager.deploy(predictionMarket.address, oracle.address);
  await payoutManager.deployed();
  console.log("PayoutManager deployed to:", payoutManager.address);

  // Save deployment addresses
  const deploymentInfo = {
    network: "baseMainnet",
    chainId: 8453,
    deploymentTime: new Date().toISOString(),
    contracts: {
      PredictionMarket: predictionMarket.address,
      ClockchainOracle: oracle.address,
      NodeRegistry: nodeRegistry.address,
      PayoutManager: payoutManager.address
    },
    deployer: deployer.address
  };

  console.log("\n=== Deployment Summary ===");
  console.log(JSON.stringify(deploymentInfo, null, 2));

  // Save to file
  const fs = require("fs");
  fs.writeFileSync(
    "deployment-mainnet.json",
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\nDeployment addresses saved to deployment-mainnet.json");
  console.log("\n⚠️  IMPORTANT: Verify contracts on Basescan immediately!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });