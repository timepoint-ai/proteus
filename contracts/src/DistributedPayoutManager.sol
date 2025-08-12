// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

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

/**
 * @title DistributedPayoutManager
 * @dev Manages distributed payouts for the Clockchain prediction market
 * Distributes fees to multiple stakeholders instead of single owner
 */
contract DistributedPayoutManager is ReentrancyGuard, Pausable {
    // Fee distribution percentages (out of 700 = 7%)
    uint16 public constant ORACLE_SHARE = 200;      // 2%
    uint16 public constant NODE_SHARE = 100;        // 1%
    uint16 public constant CREATOR_SHARE = 100;     // 1%
    uint16 public constant BUILDER_POOL_SHARE = 200; // 2%
    uint16 public constant BITTENSOR_POOL_SHARE = 100; // 1%
    uint16 public constant TOTAL_FEE = 700;         // 7% total
    
    IPredictionMarket public predictionMarket;
    IBuilderRewardPool public builderRewardPool;
    IBittensorRewardPool public bittensorRewardPool;
    
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
        uint256 oracleRewards,
        uint256 nodeRewards,
        uint256 creatorReward,
        uint256 builderPoolDeposit,
        uint256 bittensorPoolDeposit
    );
    
    event OracleRewarded(address indexed oracle, uint256 amount, uint256 marketId);
    event NodeRewarded(address indexed node, uint256 amount);
    event CreatorRewarded(address indexed creator, uint256 amount, uint256 marketId);
    event RewardClaimed(address indexed recipient, uint256 amount);
    
    constructor(
        address _predictionMarket,
        address _builderRewardPool,
        address _bittensorRewardPool
    ) {
        predictionMarket = IPredictionMarket(_predictionMarket);
        builderRewardPool = IBuilderRewardPool(_builderRewardPool);
        bittensorRewardPool = IBittensorRewardPool(_bittensorRewardPool);
    }
    
    /**
     * @dev Distribute fees for a resolved market
     * @param _marketId The market ID to distribute fees for
     */
    function distributeFees(uint256 _marketId) external nonReentrant whenNotPaused {
        (
            address creator,
            ,
            ,
            ,
            bool resolved,
            ,
            ,
            ,
            ,
            ,
            uint256 platformFeeCollected
        ) = predictionMarket.markets(_marketId);
        
        require(resolved, "Market not resolved");
        require(platformFeeCollected > 0, "No fees to distribute");
        
        // Calculate distribution amounts
        uint256 oracleReward = (platformFeeCollected * ORACLE_SHARE) / TOTAL_FEE;
        uint256 nodeReward = (platformFeeCollected * NODE_SHARE) / TOTAL_FEE;
        uint256 creatorReward = (platformFeeCollected * CREATOR_SHARE) / TOTAL_FEE;
        uint256 builderReward = (platformFeeCollected * BUILDER_POOL_SHARE) / TOTAL_FEE;
        uint256 bittensorReward = (platformFeeCollected * BITTENSOR_POOL_SHARE) / TOTAL_FEE;
        
        // Distribute to oracles who participated
        _distributeToOracles(_marketId, oracleReward);
        
        // Distribute to active nodes
        _distributeToNodes(nodeReward);
        
        // Reward market creator
        unclaimedRewards[creator] += creatorReward;
        emit CreatorRewarded(creator, creatorReward, _marketId);
        
        // Deposit to Builder Rewards Pool
        if (builderReward > 0 && address(builderRewardPool) != address(0)) {
            builderRewardPool.deposit{value: builderReward}();
        }
        
        // Deposit to Bittensor Reward Pool
        if (bittensorReward > 0 && address(bittensorRewardPool) != address(0)) {
            bittensorRewardPool.deposit{value: bittensorReward}();
        }
        
        emit FeesDistributed(
            _marketId,
            oracleReward,
            nodeReward,
            creatorReward,
            builderReward,
            bittensorReward
        );
    }
    
    /**
     * @dev Distribute rewards to oracles based on their contributions
     */
    function _distributeToOracles(uint256 _marketId, uint256 _totalReward) internal {
        address[] memory oracles = marketOracles[_marketId];
        if (oracles.length == 0 || _totalReward == 0) return;
        
        // Calculate total contributions
        uint256 totalContributions = 0;
        for (uint256 i = 0; i < oracles.length; i++) {
            totalContributions += oracleContributions[_marketId][oracles[i]];
        }
        
        if (totalContributions == 0) {
            // Equal distribution if no contributions tracked
            uint256 perOracleReward = _totalReward / oracles.length;
            for (uint256 i = 0; i < oracles.length; i++) {
                unclaimedRewards[oracles[i]] += perOracleReward;
                emit OracleRewarded(oracles[i], perOracleReward, _marketId);
            }
        } else {
            // Weighted distribution based on contributions
            for (uint256 i = 0; i < oracles.length; i++) {
                uint256 contribution = oracleContributions[_marketId][oracles[i]];
                uint256 reward = (_totalReward * contribution) / totalContributions;
                unclaimedRewards[oracles[i]] += reward;
                emit OracleRewarded(oracles[i], reward, _marketId);
            }
        }
    }
    
    /**
     * @dev Distribute rewards equally among active nodes
     */
    function _distributeToNodes(uint256 _totalReward) internal {
        if (activeNodes.length == 0 || _totalReward == 0) return;
        
        uint256 perNodeReward = _totalReward / activeNodes.length;
        for (uint256 i = 0; i < activeNodes.length; i++) {
            nodeRewards[activeNodes[i]] += perNodeReward;
            unclaimedRewards[activeNodes[i]] += perNodeReward;
            emit NodeRewarded(activeNodes[i], perNodeReward);
        }
    }
    
    /**
     * @dev Register an oracle contribution for a market
     */
    function registerOracleContribution(
        uint256 _marketId,
        address _oracle,
        uint256 _contribution
    ) external {
        // In production, this should be restricted to authorized callers
        oracleContributions[_marketId][_oracle] += _contribution;
        
        // Add oracle to market list if not already present
        bool exists = false;
        for (uint256 i = 0; i < marketOracles[_marketId].length; i++) {
            if (marketOracles[_marketId][i] == _oracle) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            marketOracles[_marketId].push(_oracle);
        }
    }
    
    /**
     * @dev Register a node as active
     */
    function registerNode(address _node) external {
        // In production, this should validate node requirements
        bool exists = false;
        for (uint256 i = 0; i < activeNodes.length; i++) {
            if (activeNodes[i] == _node) {
                exists = true;
                break;
            }
        }
        if (!exists) {
            activeNodes.push(_node);
        }
    }
    
    /**
     * @dev Claim accumulated rewards
     */
    function claimRewards() external nonReentrant {
        uint256 amount = unclaimedRewards[msg.sender];
        require(amount > 0, "No rewards to claim");
        
        unclaimedRewards[msg.sender] = 0;
        
        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "Transfer failed");
        
        emit RewardClaimed(msg.sender, amount);
    }
    
    /**
     * @dev Calculate and distribute winner payouts (same as original)
     */
    function calculateWinnerPayouts(uint256 _marketId) external nonReentrant {
        (
            ,
            ,
            ,
            ,
            bool resolved,
            uint256 winningSubmissionId,
            uint256 totalVolume,
            ,
            ,
            ,
            uint256 platformFeeCollected
        ) = predictionMarket.markets(_marketId);
        
        require(resolved, "Market not resolved");
        
        uint256 totalPool = totalVolume - platformFeeCollected;
        uint256[] memory submissionIds = predictionMarket.getMarketSubmissions(_marketId);
        
        // Calculate winner and loser pools
        uint256 winnerPool = 0;
        uint256 loserPool = 0;
        
        for (uint256 i = 0; i < submissionIds.length; i++) {
            (,,, uint256 stake, uint256 totalBets,,,,) = 
                predictionMarket.submissions(submissionIds[i]);
            
            if (submissionIds[i] == winningSubmissionId) {
                winnerPool = totalBets;
            } else {
                loserPool += totalBets;
            }
        }
        
        // Create payouts for winners
        if (winnerPool > 0) {
            // Winners get their stake back plus proportional share of loser pool
            // Implementation would continue here...
        }
    }
    
    /**
     * @dev Update builder reward pool address
     */
    function updateBuilderRewardPool(address _newPool) external {
        // In production, this should have access controls
        builderRewardPool = IBuilderRewardPool(_newPool);
    }
    
    /**
     * @dev Update Bittensor reward pool address
     */
    function updateBittensorRewardPool(address _newPool) external {
        // In production, this should have access controls
        bittensorRewardPool = IBittensorRewardPool(_newPool);
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {}
}