const { ethers } = require("hardhat");

async function main() {
  const provider = ethers.provider;
  const [signer] = await ethers.getSigners();
  
  console.log("Signer:", signer.address);
  const balance = await provider.getBalance(signer.address);
  console.log("Balance:", ethers.formatEther(balance), "ETH\n");
  
  // Check if contract has code at address
  const previousAddr = "0x667121e8f22570F2c521454D93D6A87e44488d93";
  const code = await provider.getCode(previousAddr);
  console.log("Code at previous address:", code.length > 2 ? "YES (length: " + code.length + ")" : "NO CODE");
  
  if (code.length <= 2) {
    console.log("\nPrevious deployment failed. Redeploying...\n");
    
    // Deploy with higher gas limit and explicit wait
    const PredictionMarket = await ethers.getContractFactory("PredictionMarket");
    
    console.log("Deploying PredictionMarket...");
    const deployTx = await PredictionMarket.deploy({
      gasLimit: 5000000,
      gasPrice: ethers.parseUnits("2", "gwei")  // 2 gwei
    });
    
    console.log("Deploy TX hash:", deployTx.deploymentTransaction().hash);
    console.log("Waiting for deployment...");
    
    await deployTx.waitForDeployment();
    const newAddress = await deployTx.getAddress();
    
    console.log("\n=================================");
    console.log("NEW PredictionMarket address:", newAddress);
    console.log("=================================\n");
    
    // Wait a bit then verify code
    await new Promise(r => setTimeout(r, 3000));
    const newCode = await provider.getCode(newAddress);
    console.log("Code at new address:", newCode.length > 2 ? "YES (length: " + newCode.length + ")" : "NO CODE");
    
    if (newCode.length > 2) {
      // Verify contract functions
      const owner = await deployTx.owner();
      const marketCount = await deployTx.marketCount();
      console.log("\nContract verified:");
      console.log("  Owner:", owner);
      console.log("  Market Count:", marketCount.toString());
    }
    
    return newAddress;
  } else {
    console.log("\nContract exists at previous address.");
    return previousAddr;
  }
}

main()
  .then((addr) => {
    console.log("\nFinal contract address:", addr);
    process.exit(0);
  })
  .catch((error) => {
    console.error("Error:", error);
    process.exit(1);
  });
