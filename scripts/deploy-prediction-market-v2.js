const { ethers } = require("hardhat");

/**
 * Deploy PredictionMarketV2 to BASE Sepolia
 *
 * This contract includes:
 * - Full market resolution mechanism
 * - On-chain Levenshtein distance for winner determination
 * - Pull-based fee collection
 * - Single submission refund
 * - Emergency withdraw functionality
 */
async function main() {
  console.log("Deploying PredictionMarketV2 to BASE Sepolia...\n");

  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH");

  if (balance < ethers.parseEther("0.003")) {
    console.error("ERROR: Insufficient balance. Need at least 0.003 ETH for deployment.");
    process.exit(1);
  }

  // Fee recipient - using deployer address for now
  // Can be changed later via setFeeRecipient()
  const feeRecipient = deployer.address;
  console.log("Fee Recipient:", feeRecipient);

  // Deploy PredictionMarketV2
  const PredictionMarketV2 = await ethers.getContractFactory("PredictionMarketV2");

  console.log("\nDeploying PredictionMarketV2...");
  const predictionMarket = await PredictionMarketV2.deploy(feeRecipient, {
    gasLimit: 5000000  // Higher gas limit for larger contract
  });

  await predictionMarket.waitForDeployment();
  const address = await predictionMarket.getAddress();

  console.log("\n=============================================");
  console.log("PredictionMarketV2 deployed to:", address);
  console.log("=============================================");

  // Verify deployment
  const owner = await predictionMarket.owner();
  const marketCount = await predictionMarket.marketCount();
  const submissionCount = await predictionMarket.submissionCount();
  const platformFeeBps = await predictionMarket.PLATFORM_FEE_BPS();
  const minBet = await predictionMarket.MIN_BET();
  const maxTextLength = await predictionMarket.MAX_TEXT_LENGTH();
  const bettingCutoff = await predictionMarket.BETTING_CUTOFF();
  const minSubmissions = await predictionMarket.MIN_SUBMISSIONS();

  console.log("\nContract State:");
  console.log("  Owner:", owner);
  console.log("  Fee Recipient:", await predictionMarket.feeRecipient());
  console.log("  Market Count:", marketCount.toString());
  console.log("  Submission Count:", submissionCount.toString());
  console.log("\nConstants:");
  console.log("  Platform Fee:", (Number(platformFeeBps) / 100).toFixed(2) + "%");
  console.log("  Min Bet:", ethers.formatEther(minBet), "ETH");
  console.log("  Max Text Length:", maxTextLength.toString(), "chars");
  console.log("  Betting Cutoff:", (Number(bettingCutoff) / 3600).toString(), "hours before market end");
  console.log("  Min Submissions:", minSubmissions.toString());

  // Test Levenshtein function
  console.log("\nTesting Levenshtein distance...");
  const dist1 = await predictionMarket.levenshteinDistance("hello", "hello");
  const dist2 = await predictionMarket.levenshteinDistance("cat", "bat");
  const dist3 = await predictionMarket.levenshteinDistance("kitten", "sitting");
  console.log("  'hello' vs 'hello':", dist1.toString(), "(expected: 0)");
  console.log("  'cat' vs 'bat':", dist2.toString(), "(expected: 1)");
  console.log("  'kitten' vs 'sitting':", dist3.toString(), "(expected: 3)");

  console.log("\n=============================================");
  console.log("DEPLOYMENT SUCCESSFUL");
  console.log("=============================================");
  console.log("\nNext steps:");
  console.log("1. Verify contract on Basescan:");
  console.log(`   npx hardhat verify --network baseSepolia ${address} ${feeRecipient}`);
  console.log("\n2. Update deployment-base-sepolia.json with new address");
  console.log("\n3. Update frontend to use PredictionMarketV2");

  return address;
}

main()
  .then((address) => {
    console.log("\nDone!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
