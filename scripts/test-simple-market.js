const { ethers } = require("hardhat");

async function main() {
  const predictionMarketAddr = "0x667121e8f22570F2c521454D93D6A87e44488d93";
  
  const [signer] = await ethers.getSigners();
  console.log("Test wallet:", signer.address);
  
  const balance = await ethers.provider.getBalance(signer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH\n");
  
  // Get contract
  const PredictionMarket = await ethers.getContractFactory("PredictionMarket");
  const market = PredictionMarket.attach(predictionMarketAddr);
  
  // Verify contract state
  console.log("=== Verifying Contract ===");
  const owner = await market.owner();
  console.log("Owner:", owner);
  const marketCount = await market.marketCount();
  console.log("Market Count:", marketCount.toString());
  
  // Create a test market
  console.log("\n=== Creating Test Market ===");
  const question = "What will @elonmusk tweet next about X?";
  const duration = 3600; // 1 hour
  const twitterHandle = "elonmusk";
  const xcomOnly = true;
  
  console.log("Question:", question);
  console.log("Duration:", duration, "seconds (1 hour)");
  console.log("Actor:", twitterHandle);
  console.log("Creation fee: 0.005 ETH");
  
  const createTx = await market.createMarket(
    question,
    duration,
    twitterHandle,
    xcomOnly,
    { value: ethers.parseEther("0.005"), gasLimit: 500000 }
  );
  
  console.log("\nTransaction hash:", createTx.hash);
  console.log("Waiting for confirmation...");
  
  const receipt = await createTx.wait();
  console.log("Confirmed in block:", receipt.blockNumber);
  console.log("Gas used:", receipt.gasUsed.toString());
  
  // Get the created market
  const newMarketCount = await market.marketCount();
  const marketId = Number(newMarketCount) - 1;
  console.log("\nMarket ID:", marketId);
  
  // Read market data
  const marketData = await market.markets(marketId);
  console.log("\n=== Market Created ===");
  console.log("Question:", marketData.question);
  console.log("Creator:", marketData.creator);
  console.log("Start Time:", new Date(Number(marketData.startTime) * 1000).toISOString());
  console.log("End Time:", new Date(Number(marketData.endTime) * 1000).toISOString());
  console.log("Total Volume:", ethers.formatEther(marketData.totalVolume), "ETH");
  console.log("Actor:", marketData.actorTwitterHandle);
  console.log("X.com Only:", marketData.xcomOnly);
  console.log("Resolved:", marketData.resolved);
  
  // Check remaining balance
  const newBalance = await ethers.provider.getBalance(signer.address);
  console.log("\nRemaining Balance:", ethers.formatEther(newBalance), "ETH");
  console.log("Cost (including gas):", ethers.formatEther(balance - newBalance), "ETH");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error:", error);
    process.exit(1);
  });
