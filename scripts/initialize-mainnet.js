const hre = require("hardhat");
const { ethers } = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("=======================================================");
  console.log("🔧 INITIALIZING PLATFORM ON BASE MAINNET");
  console.log("=======================================================\n");

  // Safety check - ensure we're on BASE mainnet
  const network = await ethers.provider.getNetwork();
  if (network.chainId !== 8453n) {
    throw new Error(`❌ Not connected to BASE mainnet! Connected to chainId: ${network.chainId}`);
  }
  console.log("✅ Connected to BASE Mainnet (chainId: 8453)\n");

  // Load deployment
  let deployment;
  try {
    deployment = JSON.parse(
      fs.readFileSync('deployments/base-mainnet.json', 'utf8')
    );
    console.log("✅ Loaded deployment configuration");
  } catch (error) {
    console.error("❌ Error loading deployment");
    console.log("Please deploy platform first: npx hardhat run scripts/deploy-platform-mainnet.js --network base");
    process.exit(1);
  }

  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deployer address:", deployer.address);

  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Deployer balance:", ethers.formatEther(balance), "ETH\n");

  // Get contract instances
  const actorRegistry = await ethers.getContractAt(
    "ActorRegistry",
    deployment.contracts.ActorRegistry
  );
  const nodeRegistry = await ethers.getContractAt(
    "NodeRegistry",
    deployment.contracts.NodeRegistry
  );

  // 10 second safety delay
  console.log("⚠️  Initializing MAINNET platform");
  console.log("Press Ctrl+C to cancel...");
  await new Promise(resolve => setTimeout(resolve, 10000));

  // Get gas price
  const feeData = await ethers.provider.getFeeData();
  const gasPrice = feeData.gasPrice;
  console.log("\nGas price:", ethers.formatUnits(gasPrice, "gwei"), "gwei\n");

  // Register initial actors (top Twitter accounts for prediction markets)
  console.log("1️⃣  Registering initial actors...");
  const initialActors = [
    { handle: "elonmusk", category: "tech" },
    { handle: "realDonaldTrump", category: "politics" },
    { handle: "narendramodi", category: "politics" },
    { handle: "BarackObama", category: "politics" },
    { handle: "JoeBiden", category: "politics" },
    { handle: "BillGates", category: "tech" },
    { handle: "KimKardashian", category: "entertainment" },
    { handle: "taylorswift13", category: "entertainment" },
    { handle: "Cristiano", category: "sports" },
    { handle: "neymarjr", category: "sports" }
  ];

  const registeredActors = [];

  for (const actor of initialActors) {
    try {
      // Check if already registered
      const actorId = await actorRegistry.getActorId(actor.handle);
      if (actorId > 0) {
        console.log(`⏭️  ${actor.handle} already registered (ID: ${actorId})`);
        registeredActors.push({ ...actor, id: actorId.toString() });
        continue;
      }

      // Register new actor
      const tx = await actorRegistry.registerActor(actor.handle, { gasPrice });
      await tx.wait();
      const newActorId = await actorRegistry.getActorId(actor.handle);
      console.log(`✅ Registered ${actor.handle} (ID: ${newActorId})`);
      registeredActors.push({ ...actor, id: newActorId.toString() });
    } catch (error) {
      console.log(`⚠️  Failed to register ${actor.handle}:`, error.message);
    }
  }

  console.log(`\n✅ Registered ${registeredActors.length} actors\n`);

  // Register initial oracle nodes
  console.log("2️⃣  Registering initial oracle nodes...");

  // NOTE: Replace these with actual oracle node addresses before running
  const initialNodes = [
    {
      address: process.env.ORACLE_NODE_1 || ethers.ZeroAddress,
      name: "Oracle Node 1"
    },
    {
      address: process.env.ORACLE_NODE_2 || ethers.ZeroAddress,
      name: "Oracle Node 2"
    },
    {
      address: process.env.ORACLE_NODE_3 || ethers.ZeroAddress,
      name: "Oracle Node 3"
    }
  ];

  const registeredNodes = [];

  for (const node of initialNodes) {
    if (node.address === ethers.ZeroAddress) {
      console.log(`⏭️  Skipping ${node.name} (address not configured in .env)`);
      continue;
    }

    try {
      // Check if already registered
      const isRegistered = await nodeRegistry.isRegisteredNode(node.address);
      if (isRegistered) {
        console.log(`⏭️  ${node.name} (${node.address}) already registered`);
        registeredNodes.push(node);
        continue;
      }

      // Register node
      const tx = await nodeRegistry.registerNode(node.address, { gasPrice });
      await tx.wait();
      console.log(`✅ Registered ${node.name}: ${node.address}`);
      registeredNodes.push(node);
    } catch (error) {
      console.log(`⚠️  Failed to register ${node.name}:`, error.message);
    }
  }

  console.log(`\n✅ Registered ${registeredNodes.length} oracle nodes\n`);

  // Save initialization data
  const initData = {
    network: "base-mainnet",
    chainId: 8453,
    initializedAt: new Date().toISOString(),
    initializedBy: deployer.address,
    actors: registeredActors,
    nodes: registeredNodes.map(n => ({
      name: n.name,
      address: n.address
    }))
  };

  deployment.initialization = initData;

  fs.writeFileSync(
    'deployments/base-mainnet.json',
    JSON.stringify(deployment, null, 2)
  );

  console.log("📊 Initialization Summary:");
  console.log("=====================================");
  console.log("Actors registered:", registeredActors.length);
  console.log("Oracle nodes registered:", registeredNodes.length);
  console.log("=====================================");

  if (registeredNodes.length < 3) {
    console.log("\n⚠️  WARNING: Less than 3 oracle nodes registered!");
    console.log("Set ORACLE_NODE_1, ORACLE_NODE_2, ORACLE_NODE_3 in .env");
    console.log("Then run this script again to register more nodes");
  }

  console.log("\n🎉 Platform Initialization Complete!");
  console.log("\n📋 Next Steps:");
  console.log("1. Test market creation with: npx hardhat run scripts/create-test-market.js --network base");
  console.log("2. Update frontend environment variables:");
  console.log(`   - NEXT_PUBLIC_PREDICTION_MARKET_ADDRESS=${deployment.contracts.EnhancedPredictionMarket}`);
  console.log(`   - NEXT_PUBLIC_GENESIS_NFT_ADDRESS=${deployment.contracts.GenesisNFT}`);
  console.log("3. Deploy frontend to production");
  console.log("4. Run smoke tests");
  console.log("5. Announce Genesis NFT minting");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("\n❌ Initialization failed:", error);
    process.exit(1);
  });
