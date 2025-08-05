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
    await advancedMarkets.waitForDeployment();
    
    const advancedMarketsAddress = await advancedMarkets.getAddress();
    console.log("✓ AdvancedMarkets deployed to:", advancedMarketsAddress);
    
    // Update deployments
    deployments.AdvancedMarkets = {
        address: advancedMarketsAddress,
        deployedAt: new Date().toISOString(),
        phase: 13
    };
    
    console.log("\n2. Deploying SecurityAudit (Phase 14)...");
    const SecurityAudit = await ethers.getContractFactory("SecurityAudit");
    const securityAudit = await SecurityAudit.deploy();
    await securityAudit.waitForDeployment();
    
    const securityAuditAddress = await securityAudit.getAddress();
    console.log("✓ SecurityAudit deployed to:", securityAuditAddress);
    
    // Update deployments
    deployments.SecurityAudit = {
        address: securityAuditAddress,
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
    console.log("AdvancedMarkets:", advancedMarketsAddress);
    console.log("SecurityAudit:", securityAuditAddress);
    
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
    const receipt1 = await advancedMarkets.deploymentTransaction().wait();
    const receipt2 = await securityAudit.deploymentTransaction().wait();
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