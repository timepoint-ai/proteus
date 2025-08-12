const { ethers } = require("hardhat");
const fs = require("fs");

async function main() {
  console.log("🔧 Completing Genesis NFT Deployment on BASE Sepolia...\n");
  
  // Get deployer
  const [deployer] = await ethers.getSigners();
  console.log("Deployer:", deployer.address);
  
  // Check balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH\n");
  
  // Already deployed contracts from your output
  const genesisAddress = "0x1A5D4475881B93e876251303757E60E524286A24";
  const mockMarketAddress = "0x16a21A4B3CbC8A81ae1b26FaE843e5F62579F515";
  
  console.log("✅ Already deployed:");
  console.log("- GenesisNFT:", genesisAddress);
  console.log("- MockPredictionMarket:", mockMarketAddress);
  
  // Deploy only the missing DistributedPayoutManager with higher gas
  console.log("\n📦 Deploying DistributedPayoutManager with increased gas...");
  
  // Get current gas price and add 50% buffer
  const feeData = await ethers.provider.getFeeData();
  const gasPrice = (feeData.gasPrice * 150n) / 100n; // 50% buffer
  console.log("Gas price:", ethers.formatUnits(gasPrice, "gwei"), "gwei");
  
  const DistributedPayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
  const builderPoolAddress = ethers.ZeroAddress;
  const bittensorPoolAddress = ethers.ZeroAddress;
  
  try {
    const payoutManager = await DistributedPayoutManager.deploy(
      mockMarketAddress,
      builderPoolAddress,
      bittensorPoolAddress,
      genesisAddress,
      { gasPrice: gasPrice }
    );
    
    await payoutManager.waitForDeployment();
    const payoutAddress = await payoutManager.getAddress();
    console.log("✅ DistributedPayoutManager deployed to:", payoutAddress);
    
    // Save complete deployment
    const deployment = {
      network: "base-sepolia",
      chainId: 84532,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      contracts: {
        GenesisNFT: genesisAddress,
        DistributedPayoutManager: payoutAddress,
        MockPredictionMarket: mockMarketAddress
      }
    };
    
    fs.writeFileSync(
      'deployments/genesis-phase1-testnet.json',
      JSON.stringify(deployment, null, 2)
    );
    
    console.log("\n✅ Deployment completed and saved!");
    console.log("\n📊 Summary:");
    console.log("=====================================");
    console.log("GenesisNFT:", genesisAddress);
    console.log("PayoutManager:", payoutAddress);
    console.log("MockMarket:", mockMarketAddress);
    console.log("=====================================");
    console.log("\n✨ You can now run: npx hardhat run scripts/mint-test-nfts.js --network baseSepolia");
    
  } catch (error) {
    console.error("\n❌ Deployment failed:", error.message);
    
    // If it fails, save partial deployment
    const partialDeployment = {
      network: "base-sepolia",
      chainId: 84532,
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      contracts: {
        GenesisNFT: genesisAddress,
        MockPredictionMarket: mockMarketAddress
      },
      status: "partial - missing DistributedPayoutManager"
    };
    
    fs.writeFileSync(
      'deployments/genesis-phase1-partial.json',
      JSON.stringify(partialDeployment, null, 2)
    );
    
    console.log("\nPartial deployment saved. Try running this script again with more ETH.");
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });