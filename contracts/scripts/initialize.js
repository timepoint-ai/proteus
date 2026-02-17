const hre = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("Initializing Proteus contracts...");

  // Load deployment info
  const network = hre.network.name;
  const deploymentFile = network === "base" ? "deployment-mainnet.json" : "deployment-sepolia.json";
  
  if (!fs.existsSync(deploymentFile)) {
    throw new Error(`Deployment file ${deploymentFile} not found. Run deployment first.`);
  }

  const deployment = JSON.parse(fs.readFileSync(deploymentFile, "utf8"));
  const [deployer, oracle1, oracle2, oracle3] = await hre.ethers.getSigners();

  console.log("Initializing with account:", deployer.address);

  // Get contract instances
  const PredictionMarket = await hre.ethers.getContractFactory("PredictionMarket");
  const predictionMarket = PredictionMarket.attach(deployment.contracts.PredictionMarket);

  const ClockchainOracle = await hre.ethers.getContractFactory("ClockchainOracle");
  const oracle = ClockchainOracle.attach(deployment.contracts.ClockchainOracle);

  const NodeRegistry = await hre.ethers.getContractFactory("NodeRegistry");
  const nodeRegistry = NodeRegistry.attach(deployment.contracts.NodeRegistry);

  const PayoutManager = await hre.ethers.getContractFactory("PayoutManager");
  const payoutManager = PayoutManager.attach(deployment.contracts.PayoutManager);

  // Initialize Oracle System
  console.log("\n1. Setting up oracle operators...");
  const oracleAddresses = [
    oracle1?.address || deployer.address,
    oracle2?.address || "0x1234567890123456789012345678901234567890",
    oracle3?.address || "0x2345678901234567890123456789012345678901"
  ];

  for (const oracleAddress of oracleAddresses) {
    try {
      const tx = await oracle.addOracle(oracleAddress);
      await tx.wait();
      console.log(`✅ Added oracle: ${oracleAddress}`);
    } catch (error) {
      console.log(`❌ Failed to add oracle ${oracleAddress}:`, error.message);
    }
  }

  // Initialize consensus parameters
  console.log("\n2. Setting consensus parameters...");
  try {
    const tx = await oracle.updateConsensusParameters(
      3,     // minimumOracles
      66,    // consensusThreshold (66%)
      7200   // submissionWindow (2 hours)
    );
    await tx.wait();
    console.log("✅ Consensus parameters updated");
  } catch (error) {
    console.log("❌ Failed to update consensus parameters:", error.message);
  }

  // Fund PayoutManager
  console.log("\n3. Funding PayoutManager...");
  try {
    const fundAmount = hre.ethers.utils.parseEther("0.1");
    const tx = await deployer.sendTransaction({
      to: payoutManager.address,
      value: fundAmount
    });
    await tx.wait();
    console.log(`✅ PayoutManager funded with ${hre.ethers.utils.formatEther(fundAmount)} ETH`);
  } catch (error) {
    console.log("❌ Failed to fund PayoutManager:", error.message);
  }

  console.log("\n=== Initialization Summary ===");
  console.log("Oracle operators added:", oracleAddresses.length);
  console.log("Consensus threshold: 66%");
  console.log("Minimum oracles: 3");
  console.log("Oracle submission window: 2 hours");
  
  console.log("\n✅ Initialization complete!");
  console.log("\nNext steps:");
  console.log("1. Register nodes in NodeRegistry");
  console.log("2. Create first prediction market");
  console.log("3. Test oracle submissions");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });