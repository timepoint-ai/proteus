const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("PredictionMarketV2", function () {
  let market;
  let owner, feeRecipient, user1, user2, user3;

  const MIN_BET = ethers.parseEther("0.001");
  const PLATFORM_FEE_BPS = 700n; // 7%
  const ONE_HOUR = 3600;
  const ONE_DAY = 86400;
  const BETTING_CUTOFF = ONE_HOUR;

  beforeEach(async function () {
    [owner, feeRecipient, user1, user2, user3] = await ethers.getSigners();

    const PredictionMarketV2 = await ethers.getContractFactory("PredictionMarketV2");
    market = await PredictionMarketV2.deploy(feeRecipient.address);
    await market.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the correct owner", async function () {
      expect(await market.owner()).to.equal(owner.address);
    });

    it("Should set the correct fee recipient", async function () {
      expect(await market.feeRecipient()).to.equal(feeRecipient.address);
    });

    it("Should initialize with zero markets and submissions", async function () {
      expect(await market.marketCount()).to.equal(0);
      expect(await market.submissionCount()).to.equal(0);
    });
  });

  describe("Market Creation", function () {
    it("Should create a market with valid duration", async function () {
      const duration = ONE_DAY;
      const tx = await market.createMarket("@elonmusk", duration);
      const receipt = await tx.wait();

      expect(await market.marketCount()).to.equal(1);

      const [actorHandle, endTime, totalPool, resolved, winningSubmissionId, creator] =
        await market.getMarketDetails(0);

      expect(actorHandle).to.equal("@elonmusk");
      expect(totalPool).to.equal(0);
      expect(resolved).to.equal(false);
      expect(winningSubmissionId).to.equal(0);
      expect(creator).to.equal(owner.address);
    });

    it("Should emit MarketCreated event", async function () {
      const tx = await market.createMarket("@elonmusk", ONE_DAY);
      const receipt = await tx.wait();
      const block = await ethers.provider.getBlock(receipt.blockNumber);

      await expect(tx)
        .to.emit(market, "MarketCreated")
        .withArgs(0, "@elonmusk", block.timestamp + ONE_DAY, owner.address);
    });

    it("Should reject duration less than 1 hour", async function () {
      await expect(market.createMarket("@elonmusk", ONE_HOUR - 1))
        .to.be.revertedWithCustomError(market, "InvalidDuration");
    });

    it("Should reject duration more than 30 days", async function () {
      await expect(market.createMarket("@elonmusk", 31 * ONE_DAY))
        .to.be.revertedWithCustomError(market, "InvalidDuration");
    });
  });

  describe("Submission Creation", function () {
    beforeEach(async function () {
      await market.createMarket("@elonmusk", ONE_DAY);
    });

    it("Should create a submission with valid bet", async function () {
      await market.connect(user1).createSubmission(0, "Going to Mars!", { value: MIN_BET });

      expect(await market.submissionCount()).to.equal(1);

      const [marketId, submitter, predictedText, amount, claimed] =
        await market.getSubmissionDetails(0);

      expect(marketId).to.equal(0);
      expect(submitter).to.equal(user1.address);
      expect(predictedText).to.equal("Going to Mars!");
      expect(amount).to.equal(MIN_BET);
      expect(claimed).to.equal(false);
    });

    it("Should emit SubmissionCreated event", async function () {
      await expect(market.connect(user1).createSubmission(0, "Test prediction", { value: MIN_BET }))
        .to.emit(market, "SubmissionCreated")
        .withArgs(0, 0, user1.address, "Test prediction", MIN_BET);
    });

    it("Should update market total pool", async function () {
      const betAmount = ethers.parseEther("1.0");
      await market.connect(user1).createSubmission(0, "Prediction", { value: betAmount });

      const [, , totalPool] = await market.getMarketDetails(0);
      expect(totalPool).to.equal(betAmount);
    });

    it("Should track user submissions", async function () {
      await market.connect(user1).createSubmission(0, "Prediction 1", { value: MIN_BET });
      await market.connect(user1).createSubmission(0, "Prediction 2", { value: MIN_BET });

      const userSubs = await market.getUserSubmissions(user1.address);
      expect(userSubs.length).to.equal(2);
      expect(userSubs[0]).to.equal(0);
      expect(userSubs[1]).to.equal(1);
    });

    it("Should reject bet below minimum", async function () {
      await expect(
        market.connect(user1).createSubmission(0, "Test", { value: MIN_BET - 1n })
      ).to.be.revertedWithCustomError(market, "InsufficientBet");
    });

    it("Should reject empty prediction text", async function () {
      await expect(
        market.connect(user1).createSubmission(0, "", { value: MIN_BET })
      ).to.be.revertedWithCustomError(market, "EmptyPrediction");
    });

    it("Should reject prediction text exceeding max length", async function () {
      const tooLong = "a".repeat(281); // MAX_TEXT_LENGTH is 280
      await expect(
        market.connect(user1).createSubmission(0, tooLong, { value: MIN_BET })
      ).to.be.revertedWithCustomError(market, "PredictionTooLong");
    });

    it("Should accept prediction at max length", async function () {
      const maxLength = "a".repeat(280);
      await expect(
        market.connect(user1).createSubmission(0, maxLength, { value: MIN_BET })
      ).to.emit(market, "SubmissionCreated");
    });

    it("Should reject submission for non-existent market", async function () {
      await expect(
        market.connect(user1).createSubmission(999, "Test", { value: MIN_BET })
      ).to.be.revertedWithCustomError(market, "MarketNotFound");
    });

    it("Should reject submission after market ends", async function () {
      await time.increase(ONE_DAY + 1);
      await expect(
        market.connect(user1).createSubmission(0, "Test", { value: MIN_BET })
      ).to.be.revertedWithCustomError(market, "MarketEnded");
    });

    it("Should reject submission within betting cutoff period", async function () {
      await time.increase(ONE_DAY - BETTING_CUTOFF + 1);
      await expect(
        market.connect(user1).createSubmission(0, "Test", { value: MIN_BET })
      ).to.be.revertedWithCustomError(market, "BettingCutoffPassed");
    });
  });

  describe("Market Resolution", function () {
    beforeEach(async function () {
      await market.createMarket("@elonmusk", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Going to Mars soon", { value: ethers.parseEther("1.0") });
      await market.connect(user2).createSubmission(0, "Tesla stock to the moon", { value: ethers.parseEther("0.5") });
    });

    it("Should resolve market and determine winner", async function () {
      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "Going to Mars!");

      const [, , , resolved, winningSubmissionId] = await market.getMarketDetails(0);
      expect(resolved).to.equal(true);
      expect(winningSubmissionId).to.equal(0); // First submission should win
    });

    it("Should emit MarketResolved event", async function () {
      await time.increase(ONE_DAY + 1);
      // "Going to Mars soon" vs "Going to Mars!" has small Levenshtein distance
      await expect(market.resolveMarket(0, "Going to Mars!"))
        .to.emit(market, "MarketResolved");
    });

    it("Should reject resolution before market ends", async function () {
      await expect(market.resolveMarket(0, "Test"))
        .to.be.revertedWithCustomError(market, "MarketNotEnded");
    });

    it("Should reject resolution by non-owner", async function () {
      await time.increase(ONE_DAY + 1);
      await expect(market.connect(user1).resolveMarket(0, "Test"))
        .to.be.revertedWithCustomError(market, "OwnableUnauthorizedAccount");
    });

    it("Should reject double resolution", async function () {
      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "Test");
      await expect(market.resolveMarket(0, "Test again"))
        .to.be.revertedWithCustomError(market, "MarketAlreadyResolved");
    });

    it("Should reject resolution with less than 2 submissions", async function () {
      // Create new market with only 1 submission
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(1, "Single prediction", { value: MIN_BET });
      await time.increase(ONE_DAY + 1);

      await expect(market.resolveMarket(1, "Test"))
        .to.be.revertedWithCustomError(market, "MinimumSubmissionsNotMet");
    });
  });

  describe("Payout Claiming", function () {
    const user1Bet = ethers.parseEther("1.0");
    const user2Bet = ethers.parseEther("0.5");

    beforeEach(async function () {
      await market.createMarket("@elonmusk", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Going to Mars", { value: user1Bet });
      await market.connect(user2).createSubmission(0, "Tesla forever", { value: user2Bet });
      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "Going to Mars!");
    });

    it("Should allow winner to claim payout", async function () {
      const totalPool = user1Bet + user2Bet;
      const expectedFee = (totalPool * PLATFORM_FEE_BPS) / 10000n;
      const expectedPayout = totalPool - expectedFee;

      const balanceBefore = await ethers.provider.getBalance(user1.address);
      const tx = await market.connect(user1).claimPayout(0);
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed * receipt.gasPrice;
      const balanceAfter = await ethers.provider.getBalance(user1.address);

      expect(balanceAfter - balanceBefore + gasCost).to.equal(expectedPayout);
    });

    it("Should emit PayoutClaimed event", async function () {
      const totalPool = user1Bet + user2Bet;
      const expectedFee = (totalPool * PLATFORM_FEE_BPS) / 10000n;
      const expectedPayout = totalPool - expectedFee;

      await expect(market.connect(user1).claimPayout(0))
        .to.emit(market, "PayoutClaimed")
        .withArgs(0, user1.address, expectedPayout);
    });

    it("Should accumulate fees for pull-based withdrawal", async function () {
      const totalPool = user1Bet + user2Bet;
      const expectedFee = (totalPool * PLATFORM_FEE_BPS) / 10000n;

      await market.connect(user1).claimPayout(0);

      expect(await market.pendingFees(feeRecipient.address)).to.equal(expectedFee);
    });

    it("Should reject claim by non-winner", async function () {
      await expect(market.connect(user2).claimPayout(1))
        .to.be.revertedWithCustomError(market, "NotWinningSubmission");
    });

    it("Should reject double claim", async function () {
      await market.connect(user1).claimPayout(0);
      await expect(market.connect(user1).claimPayout(0))
        .to.be.revertedWithCustomError(market, "AlreadyClaimed");
    });

    it("Should reject claim before resolution", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(1, "Test", { value: MIN_BET });

      await expect(market.connect(user1).claimPayout(2))
        .to.be.revertedWithCustomError(market, "MarketNotEnded");
    });
  });

  describe("Single Submission Refund", function () {
    it("Should refund single submission without fee", async function () {
      await market.createMarket("@test", ONE_DAY);
      const betAmount = ethers.parseEther("1.0");
      await market.connect(user1).createSubmission(0, "Only prediction", { value: betAmount });

      await time.increase(ONE_DAY + 1);

      const balanceBefore = await ethers.provider.getBalance(user1.address);
      const tx = await market.connect(user1).refundSingleSubmission(0);
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed * receipt.gasPrice;
      const balanceAfter = await ethers.provider.getBalance(user1.address);

      // Full refund - no 7% fee taken
      expect(balanceAfter - balanceBefore + gasCost).to.equal(betAmount);
    });

    it("Should emit SingleSubmissionRefunded event", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Only", { value: MIN_BET });
      await time.increase(ONE_DAY + 1);

      await expect(market.connect(user1).refundSingleSubmission(0))
        .to.emit(market, "SingleSubmissionRefunded")
        .withArgs(0, 0, user1.address, MIN_BET);
    });

    it("Should reject refund when more than one submission", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "First", { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "Second", { value: MIN_BET });
      await time.increase(ONE_DAY + 1);

      await expect(market.refundSingleSubmission(0))
        .to.be.revertedWithCustomError(market, "NotSingleSubmission");
    });

    it("Should reject refund before market ends", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Only", { value: MIN_BET });

      await expect(market.refundSingleSubmission(0))
        .to.be.revertedWithCustomError(market, "MarketNotEndedForRefund");
    });
  });

  describe("Fee Withdrawal", function () {
    it("Should allow fee recipient to withdraw accumulated fees", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "First", { value: ethers.parseEther("1.0") });
      await market.connect(user2).createSubmission(0, "Second", { value: ethers.parseEther("1.0") });
      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "First");
      await market.connect(user1).claimPayout(0);

      const expectedFee = (ethers.parseEther("2.0") * PLATFORM_FEE_BPS) / 10000n;
      const balanceBefore = await ethers.provider.getBalance(feeRecipient.address);
      const tx = await market.connect(feeRecipient).withdrawFees();
      const receipt = await tx.wait();
      const gasCost = receipt.gasUsed * receipt.gasPrice;
      const balanceAfter = await ethers.provider.getBalance(feeRecipient.address);

      expect(balanceAfter - balanceBefore + gasCost).to.equal(expectedFee);
    });

    it("Should emit FeesWithdrawn event", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "First", { value: ethers.parseEther("1.0") });
      await market.connect(user2).createSubmission(0, "Second", { value: ethers.parseEther("1.0") });
      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "First");
      await market.connect(user1).claimPayout(0);

      const expectedFee = (ethers.parseEther("2.0") * PLATFORM_FEE_BPS) / 10000n;

      await expect(market.connect(feeRecipient).withdrawFees())
        .to.emit(market, "FeesWithdrawn")
        .withArgs(feeRecipient.address, expectedFee);
    });

    it("Should reject withdrawal with no pending fees", async function () {
      await expect(market.connect(feeRecipient).withdrawFees())
        .to.be.revertedWithCustomError(market, "NoFeesToWithdraw");
    });
  });

  describe("Levenshtein Distance", function () {
    it("Should return 0 for identical strings", async function () {
      expect(await market.levenshteinDistance("hello", "hello")).to.equal(0);
    });

    it("Should return length for empty string comparison", async function () {
      expect(await market.levenshteinDistance("", "hello")).to.equal(5);
      expect(await market.levenshteinDistance("hello", "")).to.equal(5);
    });

    it("Should calculate simple substitution", async function () {
      expect(await market.levenshteinDistance("cat", "bat")).to.equal(1);
    });

    it("Should calculate insertion", async function () {
      expect(await market.levenshteinDistance("cat", "cats")).to.equal(1);
    });

    it("Should calculate deletion", async function () {
      expect(await market.levenshteinDistance("cats", "cat")).to.equal(1);
    });

    it("Should calculate complex distance", async function () {
      expect(await market.levenshteinDistance("kitten", "sitting")).to.equal(3);
    });

    it("Should be case sensitive", async function () {
      expect(await market.levenshteinDistance("Hello", "hello")).to.equal(1);
    });

    it("Should handle special characters", async function () {
      expect(await market.levenshteinDistance("hello!", "hello?")).to.equal(1);
    });
  });

  describe("Tie Breaking", function () {
    it("Should award first submitter in case of tie", async function () {
      await market.createMarket("@test", ONE_DAY);
      // Both submissions have same Levenshtein distance to "test"
      await market.connect(user1).createSubmission(0, "test", { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "test", { value: MIN_BET }); // Identical

      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "test");

      const [, , , , winningSubmissionId] = await market.getMarketDetails(0);
      expect(winningSubmissionId).to.equal(0); // First submission wins
    });

    it("Should select lower distance winner regardless of order", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "testing123", { value: MIN_BET }); // Higher distance
      await market.connect(user2).createSubmission(0, "test", { value: MIN_BET }); // Lower distance

      await time.increase(ONE_DAY + 1);
      await market.resolveMarket(0, "test!");

      const [, , , , winningSubmissionId] = await market.getMarketDetails(0);
      expect(winningSubmissionId).to.equal(1); // Second submission wins (closer match)
    });
  });

  describe("Admin Functions", function () {
    it("Should allow owner to change fee recipient", async function () {
      await market.setFeeRecipient(user3.address);
      expect(await market.feeRecipient()).to.equal(user3.address);
    });

    it("Should reject non-owner changing fee recipient", async function () {
      await expect(market.connect(user1).setFeeRecipient(user3.address))
        .to.be.revertedWithCustomError(market, "OwnableUnauthorizedAccount");
    });

    it("Should allow owner to pause", async function () {
      await market.pause();
      expect(await market.paused()).to.equal(true);
    });

    it("Should prevent operations when paused", async function () {
      await market.pause();
      await expect(market.createMarket("@test", ONE_DAY))
        .to.be.revertedWithCustomError(market, "EnforcedPause");
    });

    it("Should allow owner to unpause", async function () {
      await market.pause();
      await market.unpause();
      expect(await market.paused()).to.equal(false);
    });
  });

  describe("Emergency Withdraw", function () {
    it("Should refund all submissions after 7 days", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "First", { value: ethers.parseEther("1.0") });
      await market.connect(user2).createSubmission(0, "Second", { value: ethers.parseEther("0.5") });

      // Wait for market end + 7 days
      await time.increase(ONE_DAY + 7 * ONE_DAY + 1);

      const balance1Before = await ethers.provider.getBalance(user1.address);
      const balance2Before = await ethers.provider.getBalance(user2.address);

      await market.emergencyWithdraw(0);

      const balance1After = await ethers.provider.getBalance(user1.address);
      const balance2After = await ethers.provider.getBalance(user2.address);

      expect(balance1After - balance1Before).to.equal(ethers.parseEther("1.0"));
      expect(balance2After - balance2Before).to.equal(ethers.parseEther("0.5"));
    });

    it("Should reject emergency withdraw before 7 days", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Test", { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "Test2", { value: MIN_BET });
      await time.increase(ONE_DAY + 1); // Only market end, not 7 days

      await expect(market.emergencyWithdraw(0))
        .to.be.revertedWithCustomError(market, "MarketNotEnded");
    });

    it("Should reject emergency withdraw by non-owner", async function () {
      await market.createMarket("@test", ONE_DAY);
      await market.connect(user1).createSubmission(0, "Test", { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "Test2", { value: MIN_BET });
      await time.increase(ONE_DAY + 7 * ONE_DAY + 1);

      await expect(market.connect(user1).emergencyWithdraw(0))
        .to.be.revertedWithCustomError(market, "OwnableUnauthorizedAccount");
    });
  });

  describe("View Functions", function () {
    beforeEach(async function () {
      await market.createMarket("@elonmusk", ONE_DAY);
      await market.connect(user1).createSubmission(0, "First", { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "Second", { value: MIN_BET });
    });

    it("Should return market submissions", async function () {
      const subs = await market.getMarketSubmissions(0);
      expect(subs.length).to.equal(2);
      expect(subs[0]).to.equal(0);
      expect(subs[1]).to.equal(1);
    });

    it("Should return user submissions", async function () {
      const subs = await market.getUserSubmissions(user1.address);
      expect(subs.length).to.equal(1);
      expect(subs[0]).to.equal(0);
    });

    it("Should return full market details", async function () {
      const [actorHandle, endTime, totalPool, resolved, winningSubmissionId, creator, submissionIds] =
        await market.getMarketDetails(0);

      expect(actorHandle).to.equal("@elonmusk");
      expect(totalPool).to.equal(MIN_BET * 2n);
      expect(resolved).to.equal(false);
      expect(creator).to.equal(owner.address);
      expect(submissionIds.length).to.equal(2);
    });

    it("Should return full submission details", async function () {
      const [marketId, submitter, predictedText, amount, claimed] =
        await market.getSubmissionDetails(0);

      expect(marketId).to.equal(0);
      expect(submitter).to.equal(user1.address);
      expect(predictedText).to.equal("First");
      expect(amount).to.equal(MIN_BET);
      expect(claimed).to.equal(false);
    });
  });

  describe("Gas Optimization", function () {
    it("Should handle typical tweet-length strings", async function () {
      await market.createMarket("@test", ONE_DAY);

      // Test with tweet-like predictions (~50 chars - realistic for social media)
      const prediction1 = "Going to Mars by 2030, humanity's future!";
      const prediction2 = "Tesla stock will moon this quarter";
      await market.connect(user1).createSubmission(0, prediction1, { value: MIN_BET });
      await market.connect(user2).createSubmission(0, prediction2, { value: MIN_BET });

      await time.increase(ONE_DAY + 1);

      // Resolution with moderate-length strings
      const tx = await market.resolveMarket(0, "Going to Mars by 2025!");
      const receipt = await tx.wait();

      // Log gas used for reference
      console.log(`Gas used for resolution with ~40 char strings: ${receipt.gasUsed}`);

      // Levenshtein is O(m*n), so ~50 char strings should use < 2M gas
      expect(receipt.gasUsed).to.be.lessThan(2000000n);
    });

    it("Should warn about very long strings via gas cost", async function () {
      await market.createMarket("@test", ONE_DAY);

      // Test with longer strings (~100 chars) to show gas increase
      const longPrediction = "This is a longer prediction that demonstrates higher gas usage for Levenshtein distance";
      await market.connect(user1).createSubmission(0, longPrediction, { value: MIN_BET });
      await market.connect(user2).createSubmission(0, "Short prediction", { value: MIN_BET });

      await time.increase(ONE_DAY + 1);

      const tx = await market.resolveMarket(0, longPrediction);
      const receipt = await tx.wait();

      console.log(`Gas used for resolution with ~85 char string: ${receipt.gasUsed}`);
      // Long strings are expensive but still executable - this is documented
      // Production UI should limit to ~50 chars for reasonable gas costs
    });
  });
});
