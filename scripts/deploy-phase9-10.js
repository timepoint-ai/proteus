const { ethers } = require('hardhat');
const fs = require('fs').promises;
const path = require('path');

async function main() {
    console.log("Deploying Phase 9 & 10 Contracts to BASE Sepolia...");
    
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
    if (!deployments.NodeRegistry?.address) {
        console.error("NodeRegistry not deployed. Deploy Phase 3 first.");
        return;
    }
    
    let actorRegistryAddress;
    
    // Check if ActorRegistry is already deployed
    if (deployments.ActorRegistry?.address) {
        console.log("\nActorRegistry already deployed at:", deployments.ActorRegistry.address);
        actorRegistryAddress = deployments.ActorRegistry.address;
    } else {
        console.log("\n1. Deploying ActorRegistry (Phase 9)...");
        const ActorRegistry = await ethers.getContractFactory("ActorRegistry");
        const actorRegistry = await ActorRegistry.deploy(
            deployments.NodeRegistry.address
        );
        await actorRegistry.waitForDeployment();
        
        actorRegistryAddress = await actorRegistry.getAddress();
        console.log("✓ ActorRegistry deployed to:", actorRegistryAddress);
        
        // Update deployments
        deployments.ActorRegistry = {
            address: actorRegistryAddress,
            deployedAt: new Date().toISOString(),
            phase: 9
        };
    }
    
    console.log("\n2. Deploying EnhancedPredictionMarket (Phase 10)...");
    const EnhancedPredictionMarket = await ethers.getContractFactory("EnhancedPredictionMarket");
    const enhancedPredictionMarket = await EnhancedPredictionMarket.deploy(
        actorRegistryAddress
    );
    await enhancedPredictionMarket.waitForDeployment();
    
    const enhancedPredictionMarketAddress = await enhancedPredictionMarket.getAddress();
    console.log("✓ EnhancedPredictionMarket deployed to:", enhancedPredictionMarketAddress);
    
    // Update deployments
    deployments.EnhancedPredictionMarket = {
        address: enhancedPredictionMarketAddress,
        deployedAt: new Date().toISOString(),
        phase: 10
    };
    
    // Save deployments
    await fs.writeFile(deploymentPath, JSON.stringify(deployments, null, 2));
    
    console.log("\n=== Phase 9 & 10 Deployment Complete ===");
    console.log("ActorRegistry:", actorRegistryAddress);
    console.log("EnhancedPredictionMarket:", enhancedPredictionMarketAddress);
    
    console.log("\nPhase 9 Features:");
    console.log("- Decentralized actor approval");
    console.log("- Multi-node consensus");
    console.log("- X.com username integration");
    
    console.log("\nPhase 10 Features:");
    console.log("- Fully on-chain market data");
    console.log("- No database dependencies");
    console.log("- Complete blockchain storage");
    
    // Estimate total gas used
    const receipt1 = await actorRegistry.deploymentTransaction().wait();
    const receipt2 = await enhancedPredictionMarket.deploymentTransaction().wait();
    const totalGasUsed = receipt1.gasUsed + receipt2.gasUsed;
    const gasPrice = receipt1.gasPrice;
    const deploymentCost = ethers.formatEther(totalGasUsed * gasPrice);
    
    console.log(`\nTotal deployment cost: ${deploymentCost} BASE`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });