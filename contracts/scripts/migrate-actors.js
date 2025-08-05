const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

// Test actors to migrate from the database
const TEST_ACTORS = [
  {
    xUsername: "elonmusk",
    displayName: "Elon Musk",
    bio: "Founder of SpaceX and Tesla",
    profileImageUrl: "https://pbs.twimg.com/profile_images/1683325380441128960/yRsRRjGO_400x400.jpg",
    verified: true,
    followerCount: 150000000,
    isTestAccount: false
  },
  {
    xUsername: "taylorswift13",
    displayName: "Taylor Swift",
    bio: "Singer-songwriter",
    profileImageUrl: "https://pbs.twimg.com/profile_images/1682408456798367744/sFn6mPRm_400x400.jpg",
    verified: true,
    followerCount: 94000000,
    isTestAccount: false
  },
  {
    xUsername: "realDonaldTrump",
    displayName: "Donald J. Trump",
    bio: "45th President of the United States",
    profileImageUrl: "https://pbs.twimg.com/profile_images/874276197357596672/kUuht00m_400x400.jpg",
    verified: true,
    followerCount: 87000000,
    isTestAccount: false
  },
  {
    xUsername: "BillGates",
    displayName: "Bill Gates",
    bio: "Co-founder of Microsoft, philanthropist",
    profileImageUrl: "https://pbs.twimg.com/profile_images/1674517325532782592/t5qGXpQp_400x400.jpg",
    verified: true,
    followerCount: 64000000,
    isTestAccount: false
  },
  {
    xUsername: "Oprah",
    displayName: "Oprah Winfrey",
    bio: "Media mogul, philanthropist",
    profileImageUrl: "https://pbs.twimg.com/profile_images/1245745763805941762/Hxjb2Qvg_400x400.jpg",
    verified: true,
    followerCount: 43000000,
    isTestAccount: false
  },
  {
    xUsername: "test_alice",
    displayName: "Test Alice",
    bio: "Test account for development",
    profileImageUrl: "https://example.com/test_alice.jpg",
    verified: false,
    followerCount: 100,
    isTestAccount: true
  },
  {
    xUsername: "test_bob",
    displayName: "Test Bob", 
    bio: "Test account for development",
    profileImageUrl: "https://example.com/test_bob.jpg",
    verified: false,
    followerCount: 50,
    isTestAccount: true
  },
  {
    xUsername: "test_charlie",
    displayName: "Test Charlie",
    bio: "Test account for development",
    profileImageUrl: "https://example.com/test_charlie.jpg",
    verified: false,
    followerCount: 25,
    isTestAccount: true
  }
];

async function main() {
  console.log("Starting actor migration to ActorRegistry...");

  // Get deployer account
  const [deployer, node1, node2, node3] = await ethers.getSigners();
  console.log("Migrating with account:", deployer.address);

  // Get ActorRegistry contract address
  const actorRegistryAddress = process.env.ACTOR_REGISTRY_ADDRESS;
  if (!actorRegistryAddress) {
    console.error("ACTOR_REGISTRY_ADDRESS not set in .env");
    process.exit(1);
  }

  // Get NodeRegistry contract
  const nodeRegistryAddress = process.env.NODE_REGISTRY_ADDRESS || "0xa1234554321B86b1f3f24A9151B8cbaE5C8BDb75";
  const NodeRegistry = await hre.ethers.getContractFactory("NodeRegistry");
  const nodeRegistry = NodeRegistry.attach(nodeRegistryAddress);

  // Get ActorRegistry contract
  const ActorRegistry = await hre.ethers.getContractFactory("ActorRegistry");
  const actorRegistry = ActorRegistry.attach(actorRegistryAddress);

  // First, ensure we have active nodes
  console.log("\n=== Checking node operators ===");
  
  const nodeOperators = [deployer, node1, node2, node3];
  const nodeEndpoints = ["http://node0.local", "http://node1.local", "http://node2.local", "http://node3.local"];
  
  for (let i = 0; i < nodeOperators.length; i++) {
    const operator = nodeOperators[i];
    const isNode = await nodeRegistry.isNode(operator.address);
    
    if (!isNode) {
      console.log(`Registering node ${i}: ${operator.address}`);
      try {
        const stake = ethers.utils.parseEther("100"); // 100 BASE tokens
        const tx = await nodeRegistry.connect(operator).registerNode(nodeEndpoints[i], { value: stake });
        await tx.wait();
        console.log(`Node ${i} registered successfully`);
      } catch (error) {
        console.log(`Node ${i} already registered or error:`, error.message);
      }
    } else {
      const nodeData = await nodeRegistry.nodes(operator.address);
      console.log(`Node ${i} already registered, active: ${nodeData.active}`);
    }
  }

  // Migrate actors
  console.log("\n=== Migrating actors to blockchain ===");
  
  const migrationResults = [];
  
  for (const actor of TEST_ACTORS) {
    console.log(`\nMigrating actor: @${actor.xUsername}`);
    
    try {
      // Check if actor already exists
      const exists = await actorRegistry.actorExists(actor.xUsername);
      if (exists) {
        console.log(`Actor @${actor.xUsername} already exists on-chain`);
        const actorData = await actorRegistry.getActor(actor.xUsername);
        if (actorData.active) {
          console.log(`Actor is active with ${actorData.approvalCount} approvals`);
          migrationResults.push({
            xUsername: actor.xUsername,
            status: "already_exists",
            active: true
          });
          continue;
        }
      }
      
      // Propose actor (from first node operator)
      console.log(`Proposing actor @${actor.xUsername}...`);
      const proposeTx = await actorRegistry.connect(deployer).proposeActor(
        actor.xUsername,
        actor.displayName,
        actor.bio,
        actor.profileImageUrl,
        actor.verified,
        actor.followerCount,
        actor.isTestAccount
      );
      
      const proposeReceipt = await proposeTx.wait();
      const proposalEvent = proposeReceipt.events.find(e => e.event === "ActorProposed");
      const proposalId = proposalEvent.args.proposalId;
      
      console.log(`Actor proposed with proposal ID: ${proposalId}`);
      
      // Vote from other nodes to reach approval threshold
      console.log(`Getting approvals from other nodes...`);
      
      // Vote from node1 and node2 (we need 3 total, deployer already voted)
      const voters = [node1, node2];
      for (let i = 0; i < voters.length; i++) {
        const voter = voters[i];
        console.log(`Node ${i + 1} voting for actor...`);
        const voteTx = await actorRegistry.connect(voter).voteOnProposal(proposalId, true);
        await voteTx.wait();
      }
      
      // Check if actor is now active
      const actorData = await actorRegistry.getActor(actor.xUsername);
      console.log(`Actor @${actor.xUsername} migrated successfully!`);
      console.log(`  - Active: ${actorData.active}`);
      console.log(`  - Approvals: ${actorData.approvalCount}`);
      
      migrationResults.push({
        xUsername: actor.xUsername,
        status: "migrated",
        active: actorData.active,
        approvalCount: actorData.approvalCount.toNumber()
      });
      
    } catch (error) {
      console.error(`Failed to migrate actor @${actor.xUsername}:`, error.message);
      migrationResults.push({
        xUsername: actor.xUsername,
        status: "failed",
        error: error.message
      });
    }
  }
  
  // Save migration results
  console.log("\n=== Migration Summary ===");
  console.log(`Total actors: ${TEST_ACTORS.length}`);
  console.log(`Successfully migrated: ${migrationResults.filter(r => r.status === "migrated").length}`);
  console.log(`Already existed: ${migrationResults.filter(r => r.status === "already_exists").length}`);
  console.log(`Failed: ${migrationResults.filter(r => r.status === "failed").length}`);
  
  const migrationReport = {
    timestamp: new Date().toISOString(),
    network: hre.network.name,
    actorRegistryAddress: actorRegistryAddress,
    results: migrationResults
  };
  
  const reportPath = `./deployments/actor-migration-${Date.now()}.json`;
  fs.writeFileSync(reportPath, JSON.stringify(migrationReport, null, 2));
  console.log(`\nMigration report saved to: ${reportPath}`);
  
  // List all active actors
  console.log("\n=== Active Actors on Blockchain ===");
  const activeActors = await actorRegistry.getActiveActors();
  for (const username of activeActors) {
    const actor = await actorRegistry.getActor(username);
    console.log(`@${username} - ${actor.displayName} (Verified: ${actor.verified})`);
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });