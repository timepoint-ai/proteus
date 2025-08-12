// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title BuilderRewardPool
 * @dev Manages builder rewards distribution following BASE's model
 * Weekly ETH distributions to top contributors
 */
contract BuilderRewardPool is Ownable, ReentrancyGuard {
    
    // Weekly reward tracking
    struct WeeklyReward {
        uint256 totalPool;
        uint256 distributed;
        uint256 weekNumber;
        uint256 startTime;
        uint256 endTime;
        bool finalized;
    }
    
    // Builder contribution tracking
    struct BuilderContribution {
        address builder;
        uint256 marketsCreated;
        uint256 volumeGenerated;
        uint256 accuracyScore;
        uint256 communityVotes;
        uint256 rewardsClaimed;
        bool isEligible;
    }
    
    // Constants
    uint256 public constant WEEK_DURATION = 7 days;
    uint256 public constant TOP_BUILDERS_COUNT = 10;
    uint256 public constant MIN_CONTRIBUTION_THRESHOLD = 0.01 ether;
    
    // State variables
    mapping(uint256 => WeeklyReward) public weeklyRewards;
    mapping(address => BuilderContribution) public builders;
    mapping(uint256 => address[]) public weeklyTopBuilders;
    mapping(uint256 => mapping(address => uint256)) public weeklyBuilderRewards;
    
    uint256 public currentWeek;
    uint256 public totalDistributed;
    uint256 public contractStartTime;
    
    // Events
    event RewardPoolDeposited(uint256 amount, uint256 weekNumber);
    event WeeklyDistribution(uint256 weekNumber, uint256 totalAmount, uint256 buildersRewarded);
    event BuilderRewarded(address indexed builder, uint256 amount, uint256 weekNumber);
    event ContributionRecorded(address indexed builder, uint256 marketsCreated, uint256 volume);
    event BuilderRegistered(address indexed builder);
    
    constructor() {
        contractStartTime = block.timestamp;
        currentWeek = 1;
        weeklyRewards[currentWeek] = WeeklyReward({
            totalPool: 0,
            distributed: 0,
            weekNumber: currentWeek,
            startTime: block.timestamp,
            endTime: block.timestamp + WEEK_DURATION,
            finalized: false
        });
    }
    
    /**
     * @dev Deposit ETH into the reward pool
     */
    function deposit() external payable {
        require(msg.value > 0, "Must deposit ETH");
        
        _updateWeek();
        weeklyRewards[currentWeek].totalPool += msg.value;
        
        emit RewardPoolDeposited(msg.value, currentWeek);
    }
    
    /**
     * @dev Record builder contribution (called by PredictionMarket)
     */
    function recordContribution(
        address _builder,
        uint256 _marketsCreated,
        uint256 _volumeGenerated
    ) external {
        BuilderContribution storage builder = builders[_builder];
        
        if (!builder.isEligible) {
            builder.builder = _builder;
            builder.isEligible = true;
            emit BuilderRegistered(_builder);
        }
        
        builder.marketsCreated += _marketsCreated;
        builder.volumeGenerated += _volumeGenerated;
        
        emit ContributionRecorded(_builder, _marketsCreated, _volumeGenerated);
    }
    
    /**
     * @dev Update accuracy score for a builder
     */
    function updateAccuracyScore(address _builder, uint256 _score) external {
        // In production, restrict to oracle contract
        builders[_builder].accuracyScore = _score;
    }
    
    /**
     * @dev Community voting for builders
     */
    function voteForBuilder(address _builder) external {
        require(builders[_builder].isEligible, "Builder not registered");
        builders[_builder].communityVotes++;
    }
    
    /**
     * @dev Distribute weekly rewards to top builders
     */
    function distributeWeeklyRewards() external nonReentrant {
        _updateWeek();
        
        uint256 previousWeek = currentWeek - 1;
        require(previousWeek > 0, "No previous week");
        require(!weeklyRewards[previousWeek].finalized, "Week already finalized");
        require(weeklyRewards[previousWeek].totalPool > 0, "No rewards to distribute");
        
        WeeklyReward storage weekReward = weeklyRewards[previousWeek];
        
        // Get top builders for the week
        address[] memory topBuilders = _getTopBuilders();
        weeklyTopBuilders[previousWeek] = topBuilders;
        
        // Calculate reward distribution
        uint256 totalPool = weekReward.totalPool;
        uint256 baseReward = totalPool / TOP_BUILDERS_COUNT;
        
        // Distribute with weighted bonuses for top 3
        for (uint256 i = 0; i < topBuilders.length && i < TOP_BUILDERS_COUNT; i++) {
            if (topBuilders[i] == address(0)) break;
            
            uint256 reward = baseReward;
            
            // Bonus for top 3
            if (i == 0) reward = (reward * 150) / 100; // 50% bonus for #1
            else if (i == 1) reward = (reward * 125) / 100; // 25% bonus for #2
            else if (i == 2) reward = (reward * 110) / 100; // 10% bonus for #3
            
            weeklyBuilderRewards[previousWeek][topBuilders[i]] = reward;
            builders[topBuilders[i]].rewardsClaimed += reward;
            weekReward.distributed += reward;
            
            emit BuilderRewarded(topBuilders[i], reward, previousWeek);
        }
        
        weekReward.finalized = true;
        totalDistributed += weekReward.distributed;
        
        emit WeeklyDistribution(previousWeek, weekReward.distributed, topBuilders.length);
    }
    
    /**
     * @dev Get top builders based on composite score
     */
    function _getTopBuilders() internal view returns (address[] memory) {
        // In production, this would use a more sophisticated ranking algorithm
        // For now, simplified version based on volume generated
        
        address[] memory allBuilders = new address[](100); // Temporary array
        uint256 count = 0;
        
        // This is a simplified implementation
        // In production, would need proper enumeration of builders
        
        // Sort and return top builders
        address[] memory topBuilders = new address[](TOP_BUILDERS_COUNT);
        // Sorting logic would go here
        
        return topBuilders;
    }
    
    /**
     * @dev Calculate builder score for ranking
     */
    function calculateBuilderScore(address _builder) public view returns (uint256) {
        BuilderContribution memory builder = builders[_builder];
        
        // Weighted scoring:
        // 40% volume generated
        // 30% markets created
        // 20% accuracy score
        // 10% community votes
        
        uint256 volumeScore = builder.volumeGenerated / 1 ether;
        uint256 marketScore = builder.marketsCreated * 100;
        uint256 accuracyScore = builder.accuracyScore;
        uint256 voteScore = builder.communityVotes * 10;
        
        return (volumeScore * 40 + marketScore * 30 + accuracyScore * 20 + voteScore * 10) / 100;
    }
    
    /**
     * @dev Claim rewards for a specific week
     */
    function claimReward(uint256 _weekNumber) external nonReentrant {
        require(weeklyRewards[_weekNumber].finalized, "Week not finalized");
        
        uint256 reward = weeklyBuilderRewards[_weekNumber][msg.sender];
        require(reward > 0, "No rewards for this week");
        
        weeklyBuilderRewards[_weekNumber][msg.sender] = 0;
        
        (bool success, ) = payable(msg.sender).call{value: reward}("");
        require(success, "Transfer failed");
    }
    
    /**
     * @dev Update current week if needed
     */
    function _updateWeek() internal {
        uint256 weeksPassed = (block.timestamp - contractStartTime) / WEEK_DURATION + 1;
        
        if (weeksPassed > currentWeek) {
            // Finalize current week
            weeklyRewards[currentWeek].endTime = block.timestamp;
            
            // Start new week
            currentWeek = weeksPassed;
            weeklyRewards[currentWeek] = WeeklyReward({
                totalPool: 0,
                distributed: 0,
                weekNumber: currentWeek,
                startTime: block.timestamp,
                endTime: block.timestamp + WEEK_DURATION,
                finalized: false
            });
        }
    }
    
    /**
     * @dev Get current week info
     */
    function getCurrentWeekInfo() external view returns (
        uint256 weekNumber,
        uint256 totalPool,
        uint256 startTime,
        uint256 endTime
    ) {
        WeeklyReward memory week = weeklyRewards[currentWeek];
        return (week.weekNumber, week.totalPool, week.startTime, week.endTime);
    }
    
    /**
     * @dev Emergency withdrawal (only for unclaimed old rewards)
     */
    function emergencyWithdraw() external onlyOwner {
        // Only withdraw rewards older than 90 days
        uint256 cutoffWeek = currentWeek > 12 ? currentWeek - 12 : 0;
        uint256 amount = 0;
        
        for (uint256 i = 1; i <= cutoffWeek; i++) {
            if (weeklyRewards[i].finalized) {
                amount += (weeklyRewards[i].totalPool - weeklyRewards[i].distributed);
            }
        }
        
        if (amount > 0) {
            (bool success, ) = payable(owner()).call{value: amount}("");
            require(success, "Transfer failed");
        }
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {
        // Direct ETH transfers go to the pool
        weeklyRewards[currentWeek].totalPool += msg.value;
    }
}