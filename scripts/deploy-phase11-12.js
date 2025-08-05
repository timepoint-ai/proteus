const { ethers } = require('hardhat');
const fs = require('fs').promises;
const path = require('path');

async function main() {
    console.log("Deploying Phase 11 & 12 Contracts to BASE Sepolia...");
    
    const [deployer] = await ethers.getSigners();
    console.log("Deploying with account:", deployer.address);
    
    // Get existing deployments
    const deploymentPath = path.join(__dirname, '../deployments/base-sepolia.json');
    let deployments = {};
    
    try {
        const data = await fs.readFile(deploymentPath, 'utf8');
        deployments = JSON.parse(data);
    } catch (error) {
        console.log("No existing deployments found, creating new file");
    }
    
    // Check required contracts exist
    if (!deployments.EnhancedPredictionMarket?.address) {
        console.error("EnhancedPredictionMarket not deployed. Deploy Phase 10 first.");
        return;
    }
    
    if (!deployments.NodeRegistry?.address) {
        console.error("NodeRegistry not deployed. Deploy Phase 1 first.");
        return;
    }
    
    console.log("\n1. Deploying DecentralizedOracle (Phase 11)...");
    const DecentralizedOracle = await ethers.getContractFactory("DecentralizedOracle");
    const decentralizedOracle = await DecentralizedOracle.deploy(
        deployments.EnhancedPredictionMarket.address,
        deployments.NodeRegistry.address
    );
    await decentralizedOracle.deployed();
    
    console.log("✓ DecentralizedOracle deployed to:", decentralizedOracle.address);
    
    // Update deployments
    deployments.DecentralizedOracle = {
        address: decentralizedOracle.address,
        deployedAt: new Date().toISOString(),
        phase: 11
    };
    
    // Grant oracle role to DecentralizedOracle in EnhancedPredictionMarket
    console.log("\n2. Granting oracle role to DecentralizedOracle...");
    const enhancedMarket = await ethers.getContractAt(
        "EnhancedPredictionMarket",
        deployments.EnhancedPredictionMarket.address
    );
    
    const ORACLE_ROLE = await enhancedMarket.ORACLE_ROLE();
    const tx = await enhancedMarket.grantRole(ORACLE_ROLE, decentralizedOracle.address);
    await tx.wait();
    
    console.log("✓ Oracle role granted to DecentralizedOracle");
    
    // Save deployments
    await fs.writeFile(deploymentPath, JSON.stringify(deployments, null, 2));
    
    console.log("\n=== Phase 11 & 12 Deployment Complete ===");
    console.log("DecentralizedOracle:", decentralizedOracle.address);
    console.log("\nPhase 12 Notes:");
    console.log("- PostgreSQL dependency removed");
    console.log("- Use blockchain_only_data.py for data access");
    console.log("- P2P communication via p2p_communication.py");
    console.log("- IPFS integration for media storage");
    
    // Estimate total gas used
    const receipt = await decentralizedOracle.deployTransaction.wait();
    const gasUsed = receipt.gasUsed;
    const gasPrice = receipt.effectiveGasPrice;
    const deploymentCost = ethers.utils.formatEther(gasUsed.mul(gasPrice));
    
    console.log(`\nDeployment cost: ${deploymentCost} BASE`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });