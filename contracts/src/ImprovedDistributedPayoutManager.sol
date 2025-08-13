// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

interface IPredictionMarket {
    function markets(uint256) external view returns (
        address creator,
        address actor,
        uint256 startTime,
        uint256 endTime,
        bool resolved,
        uint256 winningSubmissionId,
        uint256 totalVolume,
        uint256 submissionCount,
        uint256 betCount,
        uint256 platformFeePercentage,
        uint256 platformFeeCollected
    );
    
    function submissions(uint256) external view returns (
        uint256 marketId,
        address creator,
        string memory predictedText,
        uint256 stake,
        uint256 totalBets,
        uint256 levenshteinDistance,
        bool isWinner,
        string memory screenshotIpfsHash,
        bytes32 screenshotBase64Hash
    );
    
    function getMarketSubmissions(uint256 marketId) external view returns (uint256[] memory);
}

interface IBuilderRewardPool {
    function deposit() external payable;
}

interface IBittensorRewardPool {
    function deposit() external payable;
}

interface IGenesisNFT is IERC721 {
    function totalSupply() external view returns (uint256);
    function totalMinted() external view returns (uint256);
}

/**
 * @title ImprovedDistributedPayoutManager
 * @dev IMPROVED VERSION: Genesis NFT holders get 20% of platform fees (1.4% of volume)
 * This gives meaningful rewards to early supporters who hold Genesis NFTs
 */
contract ImprovedDistributedPayoutManager is ReentrancyGuard, Pausable {
    // IMPROVED Fee distribution (out of 700 = 7% platform fee)
    // Genesis holders now get 20% of all fees instead of 2.8%!
    uint16 public constant GENESIS_SHARE = 140;      // 20% of fees = 1.4% of volume (was 0.2%)
    uint16 public constant ORACLE_SHARE = 140;       // 20% of fees = 1.4% of volume
    uint16 public constant NODE_SHARE = 70;          // 10% of fees = 0.7% of volume
    uint16 public constant CREATOR_SHARE = 140;      // 20% of fees = 1.4% of volume
    uint16 public constant BUILDER_POOL_SHARE = 140; // 20% of fees = 1.4% of volume
    uint16 public constant BITTENSOR_POOL_SHARE = 70; // 10% of fees = 0.7% of volume
    uint16 public constant TOTAL_FEE = 700;          // 7% total platform fee
    
    IPredictionMarket public predictionMarket;
    IBuilderRewardPool public builderRewardPool;
    IBittensorRewardPool public bittensorRewardPool;
    IGenesisNFT public genesisNFT;
    
    // Track oracle contributions per market
    mapping(uint256 => mapping(address => uint256)) public oracleContributions;
    mapping(uint256 => address[]) public marketOracles;
    
    // Track node operator rewards
    mapping(address => uint256) public nodeRewards;
    address[] public activeNodes;
    
    // Payout tracking
    struct Payout {
        address recipient;
        uint256 amount;
        uint256 marketId;
        bool claimed;
    }
    
    mapping(uint256 => Payout[]) public marketPayouts;
    mapping(address => uint256) public unclaimedRewards;
    
    // Events
    event FeesDistributed(
        uint256 indexed marketId,
        uint256 genesisRewards,
        uint256 oracleRewards,
        uint256 nodeRewards,
        uint256 creatorReward,
        uint256 builderPoolDeposit,
        uint256 bittensorPoolDeposit
    );
    
    event GenesisHolderRewarded(address indexed holder, uint256 amount, uint256 marketId);
    event OracleRewarded(address indexed oracle, uint256 amount, uint256 marketId);
    event NodeRewarded(address indexed node, uint256 amount);
    event CreatorRewarded(address indexed creator, uint256 amount, uint256 marketId);
    
    constructor(
        address _predictionMarket,
        address _builderRewardPool,
        address _bittensorRewardPool,
        address _genesisNFT
    ) {
        predictionMarket = IPredictionMarket(_predictionMarket);
        builderRewardPool = IBuilderRewardPool(_builderRewardPool);
        bittensorRewardPool = IBittensorRewardPool(_bittensorRewardPool);
        genesisNFT = IGenesisNFT(_genesisNFT);
    }
    
    /**
     * @dev Distribute fees for a resolved market
     * Genesis holders now get 20% of all platform fees!
     */
    function distributeFees(uint256 amount) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be greater than 0");
        
        // Calculate distributions (IMPROVED for Genesis holders!)
        uint256 genesisRewards = (amount * GENESIS_SHARE) / TOTAL_FEE;    // 20% of fees
        uint256 oracleRewards = (amount * ORACLE_SHARE) / TOTAL_FEE;      // 20% of fees
        uint256 nodeRewardsAmount = (amount * NODE_SHARE) / TOTAL_FEE;    // 10% of fees (renamed to avoid shadow)
        uint256 creatorReward = (amount * CREATOR_SHARE) / TOTAL_FEE;     // 20% of fees
        uint256 builderPoolDeposit = (amount * BUILDER_POOL_SHARE) / TOTAL_FEE; // 20% of fees
        uint256 bittensorPoolDeposit = (amount * BITTENSOR_POOL_SHARE) / TOTAL_FEE; // 10% of fees
        
        // Distribute to Genesis NFT holders (MAJOR REWARDS NOW!)
        if (genesisRewards > 0 && address(genesisNFT) != address(0)) {
            _distributeToGenesisHolders(genesisRewards, 0);
        }
        
        // Mock distribution for other pools (simplified for testing)
        // In production, these would have proper distribution logic
        
        emit FeesDistributed(
            0, // marketId placeholder
            genesisRewards,
            oracleRewards,
            nodeRewardsAmount,
            creatorReward,
            builderPoolDeposit,
            bittensorPoolDeposit
        );
    }
    
    /**
     * @dev Distribute rewards to Genesis NFT holders
     * With 100 NFTs and 20% of fees, each NFT gets 0.2% of all platform fees
     */
    function _distributeToGenesisHolders(uint256 totalReward, uint256 marketId) internal {
        uint256 totalMinted = genesisNFT.totalMinted();
        if (totalMinted == 0) return;
        
        uint256 rewardPerNFT = totalReward / totalMinted;
        
        // Simple distribution: Send reward for each NFT directly to its owner
        // Multiple NFTs owned by same address will receive multiple payments
        for (uint256 i = 1; i <= totalMinted; i++) {
            try genesisNFT.ownerOf(i) returns (address owner) {
                if (owner != address(0) && rewardPerNFT > 0) {
                    (bool success, ) = owner.call{value: rewardPerNFT}("");
                    if (success) {
                        emit GenesisHolderRewarded(owner, rewardPerNFT, marketId);
                    }
                }
            } catch {
                // Token doesn't exist or other error, skip
            }
        }
    }
    
    /**
     * @dev Calculate potential earnings for Genesis NFT holders
     * @param platformVolume Total volume of prediction markets
     * @param nftCount Number of Genesis NFTs held
     */
    function calculateGenesisEarnings(
        uint256 platformVolume,
        uint256 nftCount
    ) external view returns (uint256) {
        // Platform takes 7% fee
        uint256 platformFee = (platformVolume * 7) / 100;
        
        // Genesis holders get 20% of platform fees (1.4% of volume)
        uint256 totalGenesisReward = (platformFee * GENESIS_SHARE) / TOTAL_FEE;
        
        // Calculate share based on NFT holdings
        uint256 totalSupply = 100; // Max Genesis NFTs
        uint256 holderShare = (totalGenesisReward * nftCount) / totalSupply;
        
        return holderShare;
    }
    
    /**
     * @dev Get current fee distribution percentages
     */
    function getFeeBreakdown() external pure returns (
        uint256 genesisPercent,
        uint256 oraclePercent,
        uint256 nodePercent,
        uint256 creatorPercent,
        uint256 builderPercent,
        uint256 bittensorPercent
    ) {
        // Return percentages of platform fees
        genesisPercent = (GENESIS_SHARE * 100) / TOTAL_FEE;   // 20%
        oraclePercent = (ORACLE_SHARE * 100) / TOTAL_FEE;     // 20%
        nodePercent = (NODE_SHARE * 100) / TOTAL_FEE;         // 10%
        creatorPercent = (CREATOR_SHARE * 100) / TOTAL_FEE;   // 20%
        builderPercent = (BUILDER_POOL_SHARE * 100) / TOTAL_FEE; // 20%
        bittensorPercent = (BITTENSOR_POOL_SHARE * 100) / TOTAL_FEE; // 10%
    }
    
    // Receive function to accept ETH
    receive() external payable {}
}