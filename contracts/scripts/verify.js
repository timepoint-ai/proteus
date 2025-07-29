const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("Starting contract verification on Basescan...");

  // Load deployment info
  const network = hre.network.name;
  const deploymentFile = network === "base" ? "deployment-mainnet.json" : "deployment-sepolia.json";
  
  if (!fs.existsSync(deploymentFile)) {
    throw new Error(`Deployment file ${deploymentFile} not found. Run deployment first.`);
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  console.log(`Verifying contracts deployed on ${deployment.network}...`);

  // Verify PredictionMarket
  console.log("\n1. Verifying PredictionMarket...");
  try {
    await hre.run("verify:verify", {
      address: deployment.contracts.PredictionMarket,
      constructorArguments: [],
    });
    console.log("✅ PredictionMarket verified");
  } catch (error) {
    console.log("❌ PredictionMarket verification failed:", error.message);
  }

  // Verify ClockchainOracle
  console.log("\n2. Verifying ClockchainOracle...");
  try {
    await hre.run("verify:verify", {
      address: deployment.contracts.ClockchainOracle,
      constructorArguments: [deployment.contracts.PredictionMarket],
    });
    console.log("✅ ClockchainOracle verified");
  } catch (error) {
    console.log("❌ ClockchainOracle verification failed:", error.message);
  }

  // Verify NodeRegistry
  console.log("\n3. Verifying NodeRegistry...");
  try {
    await hre.run("verify:verify", {
      address: deployment.contracts.NodeRegistry,
      constructorArguments: [],
    });
    console.log("✅ NodeRegistry verified");
  } catch (error) {
    console.log("❌ NodeRegistry verification failed:", error.message);
  }

  // Verify PayoutManager
  console.log("\n4. Verifying PayoutManager...");
  try {
    await hre.run("verify:verify", {
      address: deployment.contracts.PayoutManager,
      constructorArguments: [
        deployment.contracts.PredictionMarket,
        deployment.contracts.ClockchainOracle
      ],
    });
    console.log("✅ PayoutManager verified");
  } catch (error) {
    console.log("❌ PayoutManager verification failed:", error.message);
  }

  console.log("\nVerification complete!");
  console.log("\nView contracts on Basescan:");
  const baseUrl = network === "base" 
    ? "https://basescan.org/address/" 
    : "https://sepolia.basescan.org/address/";
  
  Object.entries(deployment.contracts).forEach(([name, address]) => {
    console.log(`${name}: ${baseUrl}${address}`);
  });
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });