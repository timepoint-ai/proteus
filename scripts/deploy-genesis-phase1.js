const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("🚀 Starting Phase 1: Genesis NFT Deployment");
    console.log("============================================\n");

    // Get deployer
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Account balance:", ethers.formatEther(balance), "ETH\n");

    // Check network
    const network = await ethers.provider.getNetwork();
    console.log("Network:", network.name);
    console.log("Chain ID:", network.chainId.toString());
    
    if (network.chainId !== 84532n && network.chainId !== 8453n) {
        console.error("⚠️  Warning: Not on BASE Sepolia (84532) or BASE Mainnet (8453)");
        console.log("Current chain ID:", network.chainId.toString());
    }
    console.log();

    // Deploy GenesisNFT
    console.log("📜 Deploying GenesisNFT contract...");
    const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
    const genesisNFT = await GenesisNFT.deploy();
    await genesisNFT.waitForDeployment();
    const genesisAddress = await genesisNFT.getAddress();
    console.log("✅ GenesisNFT deployed to:", genesisAddress);
    
    // Get minting deadline
    const mintingDeadline = await genesisNFT.mintingDeadline();
    const deadlineDate = new Date(Number(mintingDeadline) * 1000);
    console.log("⏰ Minting deadline:", deadlineDate.toISOString());
    console.log();

    // Deploy or update DistributedPayoutManager
    console.log("📜 Deploying DistributedPayoutManager with Genesis support...");
    
    // Get existing contract addresses from deployment file if they exist
    let predictionMarketAddress, builderPoolAddress, bittensorPoolAddress;
    
    const deploymentFile = network.chainId === 84532n 
        ? "./deployments/base-sepolia.json"
        : "./deployments/base-mainnet.json";
    
    if (fs.existsSync(deploymentFile)) {
        const deployments = JSON.parse(fs.readFileSync(deploymentFile, 'utf8'));
        predictionMarketAddress = deployments.PredictionMarket || deployments.EnhancedPredictionMarket;
        builderPoolAddress = deployments.BuilderRewardPool;
        bittensorPoolAddress = deployments.BittensorRewardPool;
    }
    
    // If addresses don't exist, deploy mock versions for testing
    if (!predictionMarketAddress || !builderPoolAddress || !bittensorPoolAddress) {
        console.log("⚠️  Missing contract addresses, deploying mock contracts for testing...");
        
        // Deploy mock contracts
        const MockContract = await ethers.getContractFactory("MockRewardPool");
        
        if (!builderPoolAddress) {
            const builderPool = await MockContract.deploy();
            await builderPool.waitForDeployment();
            builderPoolAddress = await builderPool.getAddress();
            console.log("Mock BuilderRewardPool deployed to:", builderPoolAddress);
        }
        
        if (!bittensorPoolAddress) {
            const bittensorPool = await MockContract.deploy();
            await bittensorPool.waitForDeployment();
            bittensorPoolAddress = await bittensorPool.getAddress();
            console.log("Mock BittensorRewardPool deployed to:", bittensorPoolAddress);
        }
        
        // For prediction market, use the existing one or deploy a mock
        if (!predictionMarketAddress) {
            predictionMarketAddress = "0x6B67Cb0DaAf78f63BD11195Df0FD9FFe4361b93C"; // EnhancedPredictionMarket on BASE Sepolia
        }
    }
    
    const DistributedPayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
    const payoutManager = await DistributedPayoutManager.deploy(
        predictionMarketAddress,
        builderPoolAddress,
        bittensorPoolAddress,
        genesisAddress
    );
    await payoutManager.waitForDeployment();
    const payoutManagerAddress = await payoutManager.getAddress();
    console.log("✅ DistributedPayoutManager deployed to:", payoutManagerAddress);
    console.log();

    // Verify fee distribution percentages
    console.log("💰 Fee Distribution Configuration:");
    console.log("===================================");
    const genesisShare = await payoutManager.GENESIS_SHARE();
    const oracleShare = await payoutManager.ORACLE_SHARE();
    const nodeShare = await payoutManager.NODE_SHARE();
    const creatorShare = await payoutManager.CREATOR_SHARE();
    const builderShare = await payoutManager.BUILDER_POOL_SHARE();
    const bittensorShare = await payoutManager.BITTENSOR_POOL_SHARE();
    const totalFee = await payoutManager.TOTAL_FEE();
    
    console.log(`Genesis NFT Holders: ${genesisShare}/700 (${(Number(genesisShare) / 100).toFixed(1)}%)`);
    console.log(`Oracle Validators:   ${oracleShare}/700 (${(Number(oracleShare) / 100).toFixed(1)}%)`);
    console.log(`Node Operators:      ${nodeShare}/700 (${(Number(nodeShare) / 100).toFixed(1)}%)`);
    console.log(`Market Creators:     ${creatorShare}/700 (${(Number(creatorShare) / 100).toFixed(1)}%)`);
    console.log(`Builder Pool:        ${builderShare}/700 (${(Number(builderShare) / 100).toFixed(1)}%)`);
    console.log(`Bittensor Pool:      ${bittensorShare}/700 (${(Number(bittensorShare) / 100).toFixed(1)}%)`);
    console.log(`-----------------------------------`);
    console.log(`Total Platform Fee:  ${totalFee}/10000 (${(Number(totalFee) / 100).toFixed(1)}%)`);
    console.log();

    // Mint Genesis NFTs according to distribution strategy
    console.log("🎨 Minting Genesis NFTs...");
    console.log("==========================");
    
    const distributions = [
        { name: "Cold Storage", address: deployer.address, amount: 20 },
        { name: "Multi-sig Safe", address: deployer.address, amount: 20 },
        { name: "Hardware Wallet", address: deployer.address, amount: 20 },
        { name: "Hot Wallet", address: deployer.address, amount: 20 },
        { name: "Strategic Reserve", address: deployer.address, amount: 20 }
    ];
    
    for (const dist of distributions) {
        console.log(`Minting ${dist.amount} NFTs for ${dist.name}...`);
        const tx = await genesisNFT.mint(dist.address, dist.amount);
        await tx.wait();
        console.log(`✅ Minted to ${dist.address}`);
    }
    
    const totalMinted = await genesisNFT.totalMinted();
    console.log(`\n📊 Total Genesis NFTs minted: ${totalMinted}/100`);
    console.log();

    // Save deployment addresses
    console.log("💾 Saving deployment addresses...");
    const deployment = {
        network: network.name,
        chainId: network.chainId.toString(),
        deployedAt: new Date().toISOString(),
        contracts: {
            GenesisNFT: genesisAddress,
            DistributedPayoutManager: payoutManagerAddress,
            PredictionMarket: predictionMarketAddress,
            BuilderRewardPool: builderPoolAddress,
            BittensorRewardPool: bittensorPoolAddress
        },
        genesisNFT: {
            totalSupply: totalMinted.toString(),
            mintingDeadline: deadlineDate.toISOString(),
            distributions: distributions
        }
    };
    
    const outputFile = `./deployments/genesis-phase1-${network.chainId}.json`;
    fs.writeFileSync(outputFile, JSON.stringify(deployment, null, 2));
    console.log(`✅ Deployment data saved to ${outputFile}`);
    console.log();

    // Verify contracts on Basescan (if API key is available)
    if (process.env.BASESCAN_API_KEY) {
        console.log("🔍 Verifying contracts on Basescan...");
        
        try {
            await hre.run("verify:verify", {
                address: genesisAddress,
                constructorArguments: []
            });
            console.log("✅ GenesisNFT verified");
        } catch (error) {
            console.log("⚠️  GenesisNFT verification failed:", error.message);
        }
        
        try {
            await hre.run("verify:verify", {
                address: payoutManagerAddress,
                constructorArguments: [
                    predictionMarketAddress,
                    builderPoolAddress,
                    bittensorPoolAddress,
                    genesisAddress
                ]
            });
            console.log("✅ DistributedPayoutManager verified");
        } catch (error) {
            console.log("⚠️  DistributedPayoutManager verification failed:", error.message);
        }
    } else {
        console.log("ℹ️  Skipping verification (no BASESCAN_API_KEY)");
    }
    console.log();

    // Summary
    console.log("🎉 Phase 1 Deployment Complete!");
    console.log("================================");
    console.log("GenesisNFT:", genesisAddress);
    console.log("DistributedPayoutManager:", payoutManagerAddress);
    console.log("\nNext Steps:");
    console.log("1. Verify the contracts manually if needed");
    console.log("2. Distribute Genesis NFTs to different wallets");
    console.log("3. Finalize minting after 24 hours or when all 100 are minted");
    console.log("4. Test the payout distribution with a real market");
    console.log("\n✨ Genesis NFT holders will receive 0.002% of platform volume each!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });