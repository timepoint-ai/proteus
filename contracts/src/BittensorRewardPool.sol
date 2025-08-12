// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title BittensorRewardPool
 * @dev Manages rewards for Bittensor AI agents participating in prediction markets
 * Distributes rewards based on TAO staking and performance metrics
 */
contract BittensorRewardPool is Ownable, ReentrancyGuard {
    
    // AI Agent profile
    struct AIAgent {
        address walletAddress;
        string hotkey;           // Bittensor hotkey
        string coldkey;          // Bittensor coldkey
        uint256 subnet;          // Bittensor subnet ID
        uint256 taoStaked;       // Amount of TAO staked
        uint256 yumaScore;       // Yuma consensus score (0-100)
        uint256 totalPredictions;
        uint256 successfulPredictions;
        uint256 transparencyBonus; // Bonus for transparent models (0-60%)
        uint256 totalRewards;
        uint256 unclaimedRewards;
        bool isRegistered;
        bool isVerified;
    }
    
    // Performance tracking
    struct PredictionPerformance {
        uint256 marketId;
        uint256 submissionId;
        bool wasCorrect;
        uint256 levenshteinDistance;
        uint256 rewardEarned;
        uint256 timestamp;
    }
    
    // Constants
    uint256 public constant MIN_TAO_STAKE = 100 * 10**18; // 100 TAO minimum
    uint256 public constant MAX_TRANSPARENCY_BONUS = 60; // 60% max bonus
    uint256 public constant PERFORMANCE_WEIGHT = 40;     // 40% weight on performance
    uint256 public constant TAO_STAKE_WEIGHT = 30;       // 30% weight on TAO stake
    uint256 public constant YUMA_SCORE_WEIGHT = 20;      // 20% weight on Yuma score
    uint256 public constant TRANSPARENCY_WEIGHT = 10;    // 10% weight on transparency
    
    // State variables
    mapping(address => AIAgent) public aiAgents;
    mapping(address => PredictionPerformance[]) public agentPerformance;
    mapping(string => address) public hotkeyToAddress;
    mapping(uint256 => uint256) public subnetRewardMultipliers; // Different rewards per subnet
    
    uint256 public totalPoolBalance;
    uint256 public totalDistributed;
    uint256 public epochNumber;
    uint256 public lastEpochTime;
    uint256 public epochDuration = 1 days;
    
    address[] public registeredAgents;
    
    // Events
    event AIAgentRegistered(address indexed agent, string hotkey, uint256 subnet);
    event AIAgentVerified(address indexed agent, uint256 taoStaked);
    event PredictionRecorded(address indexed agent, uint256 marketId, bool wasCorrect);
    event RewardDistributed(address indexed agent, uint256 amount, uint256 epoch);
    event TransparencyBonusUpdated(address indexed agent, uint256 bonus);
    event RewardsClaimed(address indexed agent, uint256 amount);
    event EpochCompleted(uint256 epochNumber, uint256 totalDistributed);
    
    constructor() {
        lastEpochTime = block.timestamp;
        epochNumber = 1;
        
        // Set default subnet multipliers (can be adjusted)
        subnetRewardMultipliers[1] = 100;  // Text generation subnet
        subnetRewardMultipliers[2] = 120;  // Translation subnet
        subnetRewardMultipliers[8] = 150;  // Time series prediction subnet
        subnetRewardMultipliers[18] = 130; // Cortex subnet
    }
    
    /**
     * @dev Register a Bittensor AI agent
     */
    function registerAIAgent(
        string memory _hotkey,
        string memory _coldkey,
        uint256 _subnet
    ) external {
        require(!aiAgents[msg.sender].isRegistered, "Already registered");
        require(bytes(_hotkey).length > 0, "Invalid hotkey");
        require(_subnet > 0 && _subnet <= 50, "Invalid subnet");
        
        AIAgent storage agent = aiAgents[msg.sender];
        agent.walletAddress = msg.sender;
        agent.hotkey = _hotkey;
        agent.coldkey = _coldkey;
        agent.subnet = _subnet;
        agent.isRegistered = true;
        
        hotkeyToAddress[_hotkey] = msg.sender;
        registeredAgents.push(msg.sender);
        
        emit AIAgentRegistered(msg.sender, _hotkey, _subnet);
    }
    
    /**
     * @dev Verify AI agent with TAO stake
     */
    function verifyAgent(address _agent, uint256 _taoStaked, uint256 _yumaScore) external {
        // In production, this would verify against Bittensor network
        require(aiAgents[_agent].isRegistered, "Not registered");
        require(_taoStaked >= MIN_TAO_STAKE, "Insufficient TAO stake");
        require(_yumaScore <= 100, "Invalid Yuma score");
        
        AIAgent storage agent = aiAgents[_agent];
        agent.taoStaked = _taoStaked;
        agent.yumaScore = _yumaScore;
        agent.isVerified = true;
        
        emit AIAgentVerified(_agent, _taoStaked);
    }
    
    /**
     * @dev Update transparency bonus for open source models
     */
    function updateTransparencyBonus(
        address _agent,
        bool _openSourced,
        bool _architecturePublished,
        bool _reasoningExplained,
        bool _dataSourcesRevealed
    ) external {
        require(aiAgents[_agent].isRegistered, "Not registered");
        
        uint256 bonus = 0;
        if (_openSourced) bonus += 20;           // 20% for open source
        if (_architecturePublished) bonus += 15; // 15% for architecture
        if (_reasoningExplained) bonus += 15;    // 15% for reasoning
        if (_dataSourcesRevealed) bonus += 10;   // 10% for data sources
        
        require(bonus <= MAX_TRANSPARENCY_BONUS, "Bonus exceeds maximum");
        
        aiAgents[_agent].transparencyBonus = bonus;
        emit TransparencyBonusUpdated(_agent, bonus);
    }
    
    /**
     * @dev Record prediction performance
     */
    function recordPrediction(
        address _agent,
        uint256 _marketId,
        uint256 _submissionId,
        bool _wasCorrect,
        uint256 _levenshteinDistance
    ) external {
        require(aiAgents[_agent].isVerified, "Agent not verified");
        
        AIAgent storage agent = aiAgents[_agent];
        agent.totalPredictions++;
        
        if (_wasCorrect) {
            agent.successfulPredictions++;
        }
        
        PredictionPerformance memory performance = PredictionPerformance({
            marketId: _marketId,
            submissionId: _submissionId,
            wasCorrect: _wasCorrect,
            levenshteinDistance: _levenshteinDistance,
            rewardEarned: 0,
            timestamp: block.timestamp
        });
        
        agentPerformance[_agent].push(performance);
        
        emit PredictionRecorded(_agent, _marketId, _wasCorrect);
    }
    
    /**
     * @dev Deposit rewards into the pool
     */
    function deposit() external payable {
        require(msg.value > 0, "Must deposit ETH");
        totalPoolBalance += msg.value;
    }
    
    /**
     * @dev Distribute rewards for current epoch
     */
    function distributeEpochRewards() external nonReentrant {
        require(block.timestamp >= lastEpochTime + epochDuration, "Epoch not complete");
        
        uint256 epochRewardPool = totalPoolBalance / 10; // Distribute 10% per epoch
        require(epochRewardPool > 0, "No rewards to distribute");
        
        // Calculate total scores for all agents
        uint256 totalScore = 0;
        uint256[] memory agentScores = new uint256[](registeredAgents.length);
        
        for (uint256 i = 0; i < registeredAgents.length; i++) {
            address agent = registeredAgents[i];
            if (aiAgents[agent].isVerified) {
                uint256 score = _calculateAgentScore(agent);
                agentScores[i] = score;
                totalScore += score;
            }
        }
        
        // Distribute rewards proportionally
        if (totalScore > 0) {
            uint256 distributed = 0;
            
            for (uint256 i = 0; i < registeredAgents.length; i++) {
                if (agentScores[i] > 0) {
                    address agent = registeredAgents[i];
                    uint256 reward = (epochRewardPool * agentScores[i]) / totalScore;
                    
                    // Apply transparency bonus
                    uint256 bonus = aiAgents[agent].transparencyBonus;
                    if (bonus > 0) {
                        reward = (reward * (100 + bonus)) / 100;
                    }
                    
                    aiAgents[agent].unclaimedRewards += reward;
                    aiAgents[agent].totalRewards += reward;
                    distributed += reward;
                    
                    emit RewardDistributed(agent, reward, epochNumber);
                }
            }
            
            totalDistributed += distributed;
            totalPoolBalance -= distributed;
        }
        
        epochNumber++;
        lastEpochTime = block.timestamp;
        
        emit EpochCompleted(epochNumber - 1, totalDistributed);
    }
    
    /**
     * @dev Calculate agent score for reward distribution
     */
    function _calculateAgentScore(address _agent) internal view returns (uint256) {
        AIAgent memory agent = aiAgents[_agent];
        
        if (agent.totalPredictions == 0) return 0;
        
        // Performance score (0-100)
        uint256 performanceScore = (agent.successfulPredictions * 100) / agent.totalPredictions;
        
        // TAO stake score (normalized to 0-100)
        uint256 taoScore = (agent.taoStaked > 10000 * 10**18) ? 100 : 
                          (agent.taoStaked * 100) / (10000 * 10**18);
        
        // Yuma score (already 0-100)
        uint256 yumaScore = agent.yumaScore;
        
        // Transparency score (0-100)
        uint256 transparencyScore = (agent.transparencyBonus * 100) / MAX_TRANSPARENCY_BONUS;
        
        // Weighted score
        uint256 weightedScore = (performanceScore * PERFORMANCE_WEIGHT +
                                 taoScore * TAO_STAKE_WEIGHT +
                                 yumaScore * YUMA_SCORE_WEIGHT +
                                 transparencyScore * TRANSPARENCY_WEIGHT) / 100;
        
        // Apply subnet multiplier
        uint256 multiplier = subnetRewardMultipliers[agent.subnet];
        if (multiplier == 0) multiplier = 100; // Default multiplier
        
        return (weightedScore * multiplier) / 100;
    }
    
    /**
     * @dev Claim accumulated rewards
     */
    function claimRewards() external nonReentrant {
        AIAgent storage agent = aiAgents[msg.sender];
        require(agent.isRegistered, "Not registered");
        
        uint256 rewards = agent.unclaimedRewards;
        require(rewards > 0, "No rewards to claim");
        
        agent.unclaimedRewards = 0;
        
        (bool success, ) = payable(msg.sender).call{value: rewards}("");
        require(success, "Transfer failed");
        
        emit RewardsClaimed(msg.sender, rewards);
    }
    
    /**
     * @dev Get agent statistics
     */
    function getAgentStats(address _agent) external view returns (
        uint256 totalPredictions,
        uint256 successfulPredictions,
        uint256 successRate,
        uint256 totalRewards,
        uint256 unclaimedRewards,
        uint256 currentScore
    ) {
        AIAgent memory agent = aiAgents[_agent];
        
        uint256 rate = agent.totalPredictions > 0 ? 
            (agent.successfulPredictions * 100) / agent.totalPredictions : 0;
        
        return (
            agent.totalPredictions,
            agent.successfulPredictions,
            rate,
            agent.totalRewards,
            agent.unclaimedRewards,
            _calculateAgentScore(_agent)
        );
    }
    
    /**
     * @dev Update epoch duration (owner only)
     */
    function updateEpochDuration(uint256 _duration) external onlyOwner {
        require(_duration >= 1 hours && _duration <= 30 days, "Invalid duration");
        epochDuration = _duration;
    }
    
    /**
     * @dev Update subnet multiplier
     */
    function updateSubnetMultiplier(uint256 _subnet, uint256 _multiplier) external onlyOwner {
        require(_subnet > 0 && _subnet <= 50, "Invalid subnet");
        require(_multiplier >= 50 && _multiplier <= 200, "Invalid multiplier");
        subnetRewardMultipliers[_subnet] = _multiplier;
    }
    
    /**
     * @dev Emergency withdrawal (only unclaimed old rewards)
     */
    function emergencyWithdraw() external onlyOwner {
        // Only allow withdrawal of excess funds not allocated to agents
        uint256 totalUnclaimed = 0;
        for (uint256 i = 0; i < registeredAgents.length; i++) {
            totalUnclaimed += aiAgents[registeredAgents[i]].unclaimedRewards;
        }
        
        uint256 excess = address(this).balance - totalUnclaimed;
        if (excess > 0) {
            (bool success, ) = payable(owner()).call{value: excess}("");
            require(success, "Transfer failed");
        }
    }
    
    /**
     * @dev Receive ETH
     */
    receive() external payable {
        totalPoolBalance += msg.value;
    }
}