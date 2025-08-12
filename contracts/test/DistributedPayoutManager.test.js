const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("DistributedPayoutManager with Genesis NFT", function () {
    let payoutManager;
    let genesisNFT;
    let mockPredictionMarket;
    let mockBuilderPool;
    let mockBittensorPool;
    let owner, addr1, addr2, addr3, addr4, addr5;

    beforeEach(async function () {
        [owner, addr1, addr2, addr3, addr4, addr5] = await ethers.getSigners();

        // Deploy Genesis NFT
        const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
        genesisNFT = await GenesisNFT.deploy();
        await genesisNFT.waitForDeployment();

        // Mint some Genesis NFTs for testing
        await genesisNFT.mint(addr1.address, 20); // addr1 owns 20 NFTs
        await genesisNFT.mint(addr2.address, 30); // addr2 owns 30 NFTs
        await genesisNFT.mint(addr3.address, 50); // addr3 owns 50 NFTs
        // Total: 100 NFTs minted

        // Deploy mock contracts
        const MockPredictionMarket = await ethers.getContractFactory("MockPredictionMarket");
        mockPredictionMarket = await MockPredictionMarket.deploy();
        await mockPredictionMarket.waitForDeployment();

        const MockRewardPool = await ethers.getContractFactory("MockRewardPool");
        mockBuilderPool = await MockRewardPool.deploy();
        await mockBuilderPool.waitForDeployment();
        
        mockBittensorPool = await MockRewardPool.deploy();
        await mockBittensorPool.waitForDeployment();

        // Deploy DistributedPayoutManager
        const DistributedPayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
        payoutManager = await DistributedPayoutManager.deploy(
            await mockPredictionMarket.getAddress(),
            await mockBuilderPool.getAddress(),
            await mockBittensorPool.getAddress(),
            await genesisNFT.getAddress()
        );
        await payoutManager.waitForDeployment();

        // Setup mock market data
        await mockPredictionMarket.setMarket(0, {
            creator: addr4.address,
            actor: addr5.address,
            startTime: Math.floor(Date.now() / 1000) - 3600,
            endTime: Math.floor(Date.now() / 1000) + 3600,
            resolved: true,
            winningSubmissionId: 1,
            totalVolume: ethers.parseEther("100"),
            submissionCount: 3,
            betCount: 10,
            platformFeePercentage: 700, // 7%
            platformFeeCollected: ethers.parseEther("7") // 7% of 100 ETH
        });

        // Send ETH to payout manager for distribution
        await owner.sendTransaction({
            to: await payoutManager.getAddress(),
            value: ethers.parseEther("10")
        });
    });

    describe("Genesis NFT Integration", function () {
        it("Should have Genesis NFT contract set", async function () {
            expect(await payoutManager.genesisNFT()).to.equal(await genesisNFT.getAddress());
        });

        it("Should update Genesis NFT contract address", async function () {
            const newGenesisAddress = addr5.address;
            await payoutManager.updateGenesisNFT(newGenesisAddress);
            expect(await payoutManager.genesisNFT()).to.equal(newGenesisAddress);
        });
    });

    describe("Fee Distribution with Genesis Rewards", function () {
        it("Should distribute fees including Genesis NFT rewards", async function () {
            // Register some nodes and oracles for testing
            await payoutManager.registerNode(addr4.address);
            await payoutManager.registerOracleContribution(0, addr5.address, 100);

            // Get initial balances
            const initialBalance1 = await payoutManager.unclaimedRewards(addr1.address);
            const initialBalance2 = await payoutManager.unclaimedRewards(addr2.address);
            const initialBalance3 = await payoutManager.unclaimedRewards(addr3.address);

            // Distribute fees
            await expect(payoutManager.distributeFees(0))
                .to.emit(payoutManager, "FeesDistributed");

            // Check Genesis holder rewards
            const balance1 = await payoutManager.unclaimedRewards(addr1.address);
            const balance2 = await payoutManager.unclaimedRewards(addr2.address);
            const balance3 = await payoutManager.unclaimedRewards(addr3.address);

            // Genesis holders should receive proportional rewards
            // Total Genesis reward = 7 ETH * 20/700 = 0.2 ETH
            // addr1 (20 NFTs): 0.2 * 20/100 = 0.04 ETH
            // addr2 (30 NFTs): 0.2 * 30/100 = 0.06 ETH
            // addr3 (50 NFTs): 0.2 * 50/100 = 0.10 ETH

            expect(balance1 - initialBalance1).to.be.closeTo(
                ethers.parseEther("0.04"),
                ethers.parseEther("0.001")
            );
            expect(balance2 - initialBalance2).to.be.closeTo(
                ethers.parseEther("0.06"),
                ethers.parseEther("0.001")
            );
            expect(balance3 - initialBalance3).to.be.closeTo(
                ethers.parseEther("0.10"),
                ethers.parseEther("0.001")
            );
        });

        it("Should emit GenesisHolderRewarded events", async function () {
            await payoutManager.registerNode(addr4.address);
            await payoutManager.registerOracleContribution(0, addr5.address, 100);

            const tx = await payoutManager.distributeFees(0);
            const receipt = await tx.wait();

            // Check for GenesisHolderRewarded events
            const events = receipt.logs.filter(log => {
                try {
                    const parsed = payoutManager.interface.parseLog(log);
                    return parsed.name === "GenesisHolderRewarded";
                } catch {
                    return false;
                }
            });

            // Should have 3 events (one for each unique holder)
            expect(events.length).to.equal(3);
        });

        it("Should handle Genesis NFT transfers correctly", async function () {
            // Transfer some NFTs from addr1 to addr4
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr4.address, 1);
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr4.address, 2);
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr4.address, 3);
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr4.address, 4);
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr4.address, 5);

            // Now addr1 has 15 NFTs, addr4 has 5 NFTs

            // Register nodes and oracles
            await payoutManager.registerNode(addr5.address);
            await payoutManager.registerOracleContribution(0, addr5.address, 100);

            // Distribute fees
            await payoutManager.distributeFees(0);

            // Check that addr4 now receives rewards
            const balance4 = await payoutManager.unclaimedRewards(addr4.address);
            expect(balance4).to.be.gt(0);

            // addr4 should receive: 0.2 ETH * 5/100 = 0.01 ETH
            expect(balance4).to.be.closeTo(
                ethers.parseEther("0.01"),
                ethers.parseEther("0.001")
            );
        });
    });

    describe("Fee Percentages", function () {
        it("Should have correct fee distribution percentages", async function () {
            expect(await payoutManager.GENESIS_SHARE()).to.equal(20); // 0.2%
            expect(await payoutManager.ORACLE_SHARE()).to.equal(180); // 1.8%
            expect(await payoutManager.NODE_SHARE()).to.equal(100); // 1%
            expect(await payoutManager.CREATOR_SHARE()).to.equal(100); // 1%
            expect(await payoutManager.BUILDER_POOL_SHARE()).to.equal(200); // 2%
            expect(await payoutManager.BITTENSOR_POOL_SHARE()).to.equal(100); // 1%
            expect(await payoutManager.TOTAL_FEE()).to.equal(700); // 7% total
        });

        it("Should sum to exactly 7%", async function () {
            const genesis = await payoutManager.GENESIS_SHARE();
            const oracle = await payoutManager.ORACLE_SHARE();
            const node = await payoutManager.NODE_SHARE();
            const creator = await payoutManager.CREATOR_SHARE();
            const builder = await payoutManager.BUILDER_POOL_SHARE();
            const bittensor = await payoutManager.BITTENSOR_POOL_SHARE();
            const total = await payoutManager.TOTAL_FEE();

            expect(genesis + oracle + node + creator + builder + bittensor).to.equal(total);
        });
    });

    describe("Claiming Rewards", function () {
        beforeEach(async function () {
            // Setup and distribute fees
            await payoutManager.registerNode(addr4.address);
            await payoutManager.registerOracleContribution(0, addr5.address, 100);
            await payoutManager.distributeFees(0);
        });

        it("Should allow Genesis holders to claim rewards", async function () {
            const unclaimedBefore = await payoutManager.unclaimedRewards(addr1.address);
            expect(unclaimedBefore).to.be.gt(0);

            const balanceBefore = await ethers.provider.getBalance(addr1.address);
            
            await payoutManager.connect(addr1).claimRewards();
            
            const balanceAfter = await ethers.provider.getBalance(addr1.address);
            const unclaimedAfter = await payoutManager.unclaimedRewards(addr1.address);

            expect(unclaimedAfter).to.equal(0);
            expect(balanceAfter).to.be.gt(balanceBefore);
        });

        it("Should emit RewardClaimed event", async function () {
            const unclaimed = await payoutManager.unclaimedRewards(addr1.address);
            
            await expect(payoutManager.connect(addr1).claimRewards())
                .to.emit(payoutManager, "RewardClaimed")
                .withArgs(addr1.address, unclaimed);
        });

        it("Should revert if no rewards to claim", async function () {
            // addr5 has no Genesis NFTs and wasn't set as creator
            await expect(payoutManager.connect(owner).claimRewards())
                .to.be.revertedWith("No rewards to claim");
        });
    });

    describe("Edge Cases", function () {
        it("Should handle no Genesis NFTs minted", async function () {
            // Deploy new payout manager with empty Genesis NFT
            const EmptyGenesisNFT = await ethers.getContractFactory("GenesisNFT");
            const emptyGenesis = await EmptyGenesisNFT.deploy();
            await emptyGenesis.waitForDeployment();

            const EmptyPayoutManager = await ethers.getContractFactory("DistributedPayoutManager");
            const emptyPayout = await EmptyPayoutManager.deploy(
                await mockPredictionMarket.getAddress(),
                await mockBuilderPool.getAddress(),
                await mockBittensorPool.getAddress(),
                await emptyGenesis.getAddress()
            );

            await emptyPayout.registerNode(addr4.address);
            await emptyPayout.registerOracleContribution(0, addr5.address, 100);

            // Should not revert even with no Genesis NFTs
            await expect(emptyPayout.distributeFees(0))
                .to.not.be.reverted;
        });

        it("Should handle Genesis NFT address not set", async function () {
            // Update Genesis NFT to zero address
            await payoutManager.updateGenesisNFT(ethers.ZeroAddress);

            await payoutManager.registerNode(addr4.address);
            await payoutManager.registerOracleContribution(0, addr5.address, 100);

            // Should not revert
            await expect(payoutManager.distributeFees(0))
                .to.not.be.reverted;
        });
    });
});

// Mock contracts for testing
const MockPredictionMarketCode = `
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MockPredictionMarket {
    struct Market {
        address creator;
        address actor;
        uint256 startTime;
        uint256 endTime;
        bool resolved;
        uint256 winningSubmissionId;
        uint256 totalVolume;
        uint256 submissionCount;
        uint256 betCount;
        uint256 platformFeePercentage;
        uint256 platformFeeCollected;
    }
    
    mapping(uint256 => Market) public markets;
    
    function setMarket(uint256 marketId, Market memory market) external {
        markets[marketId] = market;
    }
    
    function getMarketSubmissions(uint256) external pure returns (uint256[] memory) {
        uint256[] memory ids = new uint256[](3);
        ids[0] = 1;
        ids[1] = 2;
        ids[2] = 3;
        return ids;
    }
    
    function submissions(uint256) external pure returns (
        uint256 marketId,
        address creator,
        string memory predictedText,
        uint256 stake,
        uint256 totalBets,
        uint256 levenshteinDistance,
        bool isWinner,
        string memory screenshotIpfsHash,
        bytes32 screenshotBase64Hash
    ) {
        return (0, address(0), "", 0, 0, 0, false, "", bytes32(0));
    }
}

contract MockRewardPool {
    function deposit() external payable {}
}
`;

// Add mock contract compilation
require("fs").writeFileSync(
    "./contracts/src/MockContracts.sol",
    MockPredictionMarketCode
);