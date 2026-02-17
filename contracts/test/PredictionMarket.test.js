const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Proteus Contracts - Phase 1 Test", function () {
  let predictionMarket, oracle, nodeRegistry, payoutManager;
  let owner, oracle1, oracle2, oracle3, user1, user2;

  beforeEach(async function () {
    [owner, oracle1, oracle2, oracle3, user1, user2] = await ethers.getSigners();

    // Deploy contracts (ethers v6 syntax)
    const PredictionMarket = await ethers.getContractFactory("PredictionMarket");
    predictionMarket = await PredictionMarket.deploy();
    await predictionMarket.waitForDeployment();

    const ClockchainOracle = await ethers.getContractFactory("ClockchainOracle");
    oracle = await ClockchainOracle.deploy(await predictionMarket.getAddress());
    await oracle.waitForDeployment();

    const NodeRegistry = await ethers.getContractFactory("NodeRegistry");
    nodeRegistry = await NodeRegistry.deploy();
    await nodeRegistry.waitForDeployment();

    const PayoutManager = await ethers.getContractFactory("PayoutManager");
    payoutManager = await PayoutManager.deploy(await predictionMarket.getAddress(), await oracle.getAddress());
    await payoutManager.waitForDeployment();

    // Setup oracles
    await oracle.addOracle(oracle1.address);
    await oracle.addOracle(oracle2.address);
    await oracle.addOracle(oracle3.address);
  });

  describe("PredictionMarket", function () {
    it("Should create a market", async function () {
      const question = "Will @elonmusk tweet 'Mars' by tomorrow?";
      const duration = 86400; // 24 hours
      const actorHandle = "@elonmusk";

      const tx = await predictionMarket.connect(user1).createMarket(
        question,
        duration,
        actorHandle,
        true, // X.com only
        { value: ethers.parseEther("0.01") }
      );

      const receipt = await tx.wait();
      // ethers v6: use logs and interface.parseLog
      const event = receipt.logs.map(log => {
        try { return predictionMarket.interface.parseLog(log); } catch { return null; }
      }).find(e => e && e.name === "MarketCreated");

      expect(event.args.marketId).to.equal(0);
      expect(event.args.creator).to.equal(user1.address);
      expect(event.args.question).to.equal(question);
    });

    it("Should create submissions", async function () {
      // Create market first
      await predictionMarket.connect(user1).createMarket(
        "Test question",
        86400,
        "@testactor",
        true,
        { value: ethers.parseEther("0.01") }
      );

      // Create submission
      const predictedText = "Mars colonization is happening";
      const tx = await predictionMarket.connect(user2).createSubmission(
        0, // marketId
        predictedText,
        "ipfs://test-screenshot",
        { value: ethers.parseEther("0.01") }
      );

      const receipt = await tx.wait();
      const event = receipt.logs.map(log => {
        try { return predictionMarket.interface.parseLog(log); } catch { return null; }
      }).find(e => e && e.name === "SubmissionCreated");

      expect(event.args.submissionId).to.equal(0);
      expect(event.args.marketId).to.equal(0);
      expect(event.args.creator).to.equal(user2.address);
    });

    it("Should place bets", async function () {
      // Create market and submission
      await predictionMarket.connect(user1).createMarket(
        "Test question",
        86400,
        "@testactor",
        true,
        { value: ethers.parseEther("0.01") }
      );

      await predictionMarket.connect(user2).createSubmission(
        0,
        "Test prediction",
        "ipfs://test",
        { value: ethers.parseEther("0.01") }
      );

      // Place bet
      const tx = await predictionMarket.connect(user1).placeBet(
        0, // submissionId
        { value: ethers.parseEther("0.001") }
      );

      const receipt = await tx.wait();
      const event = receipt.logs.map(log => {
        try { return predictionMarket.interface.parseLog(log); } catch { return null; }
      }).find(e => e && e.name === "BetPlaced");

      expect(event.args.betId).to.equal(0);
      expect(event.args.submissionId).to.equal(0);
      expect(event.args.bettor).to.equal(user1.address);
    });
  });

  describe("ClockchainOracle", function () {
    it("Should calculate Levenshtein distance correctly", async function () {
      const distance1 = await oracle.calculateLevenshteinDistance("hello", "hello");
      expect(distance1).to.equal(0);

      const distance2 = await oracle.calculateLevenshteinDistance("hello", "hallo");
      expect(distance2).to.equal(1);

      const distance3 = await oracle.calculateLevenshteinDistance("hello", "world");
      expect(distance3).to.equal(4);
    });
  });

  describe("NodeRegistry", function () {
    it("Should register a node", async function () {
      const endpoint = "https://node1.proteus.markets";
      const stakeAmount = ethers.parseEther("100");

      const tx = await nodeRegistry.connect(user1).registerNode(
        endpoint,
        { value: stakeAmount }
      );

      const receipt = await tx.wait();
      const event = receipt.logs.map(log => {
        try { return nodeRegistry.interface.parseLog(log); } catch { return null; }
      }).find(e => e && e.name === "NodeRegistered");

      expect(event.args.operator).to.equal(user1.address);
      expect(event.args.stake).to.equal(stakeAmount);

      // Check node details
      const node = await nodeRegistry.nodes(user1.address);
      expect(node.stake).to.equal(stakeAmount);
      expect(node.endpoint).to.equal(endpoint);
    });
  });

  describe("Integration Test", function () {
    it("Should demonstrate complete workflow", async function () {
      console.log("\n=== Phase 1 Integration Test ===");

      // 1. Register nodes
      console.log("1. Registering nodes...");
      await nodeRegistry.connect(oracle1).registerNode(
        "https://oracle1.proteus.markets",
        { value: ethers.parseEther("100") }
      );
      console.log("✅ Node registered");

      // 2. Create market
      console.log("\n2. Creating prediction market...");
      await predictionMarket.connect(user1).createMarket(
        "Will @vitalikbuterin mention 'zkEVM' today?",
        3600, // 1 hour
        "@vitalikbuterin",
        true,
        { value: ethers.parseEther("0.01") }
      );
      console.log("✅ Market created");

      // 3. Create submissions
      console.log("\n3. Creating submissions...");
      await predictionMarket.connect(user1).createSubmission(
        0,
        "zkEVM is the future",
        "ipfs://screenshot1",
        { value: ethers.parseEther("0.05") }
      );

      await predictionMarket.connect(user2).createSubmission(
        0,
        "zkEVM rollups are scalable",
        "ipfs://screenshot2",
        { value: ethers.parseEther("0.03") }
      );
      console.log("✅ 2 submissions created");

      // 4. Place bets
      console.log("\n4. Placing bets...");
      await predictionMarket.connect(user1).placeBet(
        1, // bet on second submission
        { value: ethers.parseEther("0.02") }
      );
      console.log("✅ Bet placed");

      // 5. Check contract balances (ethers v6 syntax)
      const marketAddress = await predictionMarket.getAddress();
      const marketBalance = await ethers.provider.getBalance(marketAddress);
      console.log("\n5. Contract balances:");
      console.log(`   PredictionMarket: ${ethers.formatEther(marketBalance)} ETH`);

      console.log("\n✅ Phase 1 Complete: All contracts deployed and functional!");
    });
  });
});