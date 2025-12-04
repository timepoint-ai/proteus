const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying simpler PredictionMarket to BASE Sepolia...");
  
  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);
  
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH");
  
  // Deploy PredictionMarket (the simpler one without ActorRegistry)
  const PredictionMarket = await ethers.getContractFactory("PredictionMarket");
  
  console.log("\nDeploying PredictionMarket...");
  const predictionMarket = await PredictionMarket.deploy({
    gasLimit: 3000000
  });
  
  await predictionMarket.waitForDeployment();
  const address = await predictionMarket.getAddress();
  
  console.log("\n=================================");
  console.log("PredictionMarket deployed to:", address);
  console.log("=================================");
  
  // Verify deployment
  const owner = await predictionMarket.owner();
  const marketCount = await predictionMarket.marketCount();
  console.log("\nContract State:");
  console.log("  Owner:", owner);
  console.log("  Market Count:", marketCount.toString());
  console.log("  Platform Fee:", await predictionMarket.PLATFORM_FEE() + "%");
  
  return address;
}

main()
  .then((address) => {
    console.log("\nDeployment successful!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
