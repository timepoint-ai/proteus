const { ethers } = require('hardhat');
const fs = require('fs').promises;
const path = require('path');

async function main() {
    console.log("Deploying Phase 13 & 14 Contracts to BASE Sepolia...");
    
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
    
    console.log("\n1. Deploying AdvancedMarkets (Phase 13)...");
    const AdvancedMarkets = await ethers.getContractFactory("AdvancedMarkets");
    const advancedMarkets = await AdvancedMarkets.deploy(
        deployments.EnhancedPredictionMarket.address
    );
    await advancedMarkets.deployed();
    
    console.log("✓ AdvancedMarkets deployed to:", advancedMarkets.address);
    
    // Update deployments
    deployments.AdvancedMarkets = {
        address: advancedMarkets.address,
        deployedAt: new Date().toISOString(),
        phase: 13
    };
    
    console.log("\n2. Deploying SecurityAudit (Phase 14)...");
    const SecurityAudit = await ethers.getContractFactory("SecurityAudit");
    const securityAudit = await SecurityAudit.deploy();
    await securityAudit.deployed();
    
    console.log("✓ SecurityAudit deployed to:", securityAudit.address);
    
    // Update deployments
    deployments.SecurityAudit = {
        address: securityAudit.address,
        deployedAt: new Date().toISOString(),
        phase: 14
    };
    
    // Grant roles in AdvancedMarkets
    console.log("\n3. Configuring roles...");
    const MARKET_CREATOR_ROLE = await advancedMarkets.MARKET_CREATOR_ROLE();
    
    // Grant market creator role to EnhancedPredictionMarket
    await advancedMarkets.grantRole(
        MARKET_CREATOR_ROLE,
        deployments.EnhancedPredictionMarket.address
    );
    console.log("✓ Granted MARKET_CREATOR_ROLE to EnhancedPredictionMarket");
    
    // Save deployments
    await fs.writeFile(deploymentPath, JSON.stringify(deployments, null, 2));
    
    console.log("\n=== Phase 13 & 14 Deployment Complete ===");
    console.log("AdvancedMarkets:", advancedMarkets.address);
    console.log("SecurityAudit:", securityAudit.address);
    
    console.log("\nPhase 13 Features:");
    console.log("- Multi-choice markets");
    console.log("- Conditional markets");
    console.log("- Range prediction markets");
    console.log("- IPFS distributed storage");
    console.log("- User reputation system");
    
    console.log("\nPhase 14 Features:");
    console.log("- Security monitoring");
    console.log("- Emergency controls");
    console.log("- Rate limiting");
    console.log("- Blacklisting");
    console.log("- Transaction limits");
    
    // Estimate total gas used
    const receipt1 = await advancedMarkets.deployTransaction.wait();
    const receipt2 = await securityAudit.deployTransaction.wait();
    const totalGasUsed = receipt1.gasUsed.add(receipt2.gasUsed);
    const gasPrice = receipt1.effectiveGasPrice;
    const deploymentCost = ethers.utils.formatEther(totalGasUsed.mul(gasPrice));
    
    console.log(`\nTotal deployment cost: ${deploymentCost} BASE`);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });