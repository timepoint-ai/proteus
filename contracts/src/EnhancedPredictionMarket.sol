// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./ActorRegistry.sol";

/**
 * @title EnhancedPredictionMarket
 * @dev Phase 10 Implementation: Fully on-chain prediction markets
 * All market, submission, and bet data stored on blockchain
 */
contract EnhancedPredictionMarket is ReentrancyGuard, Ownable {
    ActorRegistry public actorRegistry;
    
    struct Market {
        string question;
        string actorUsername;      // X.com username from ActorRegistry
        address creator;
        uint256 startTime;
        uint256 endTime;
        bool resolved;
        uint256 winningSubmissionId;
        uint256 totalVolume;
        uint256 platformFeeCollected;
        uint256 submissionCount;
        uint256 betCount;
        uint256 createdAt;
        uint256 resolvedAt;
        address[] oracleWallets;   // Authorized oracles for this market
        string metadata;           // Additional market metadata (JSON string)
    }
    
    struct Submission {
        uint256 marketId;
        address creator;
        string predictedText;
        uint256 stake;
        uint256 totalBets;
        uint256 betCount;
        uint256 levenshteinDistance;
        bool isWinner;
        uint256 createdAt;
        string submissionType;     // "original", "competitor", "null"
        bytes32 textHash;          // Hash of predicted text for verification
    }
    
    struct Bet {
        address bettor;
        uint256 marketId;
        uint256 submissionId;
        uint256 amount;
        uint256 timestamp;
        uint256 potentialPayout;   // Calculated at bet time
        bool paid;                 // Payout status
        bytes32 transactionHash;   // For duplicate prevention
    }
    
    struct MarketStats {
        uint256 totalSubmissions;
        uint256 totalBets;
        uint256 totalVolume;
        uint256 highestStake;
        address topBettor;
        uint256 topBettorVolume;
        uint256 averageBetSize;
        uint256 lastActivityTime;
    }
    
    uint256 public constant PLATFORM_FEE = 7; // 7%
    uint256 public constant MINIMUM_MARKET_DURATION = 300; // 5 minutes
    uint256 public constant MAXIMUM_MARKET_DURATION = 7776000; // 90 days
    uint256 public constant MINIMUM_BET = 0.001 ether;
    
    uint256 public marketCount;
    uint256 public totalSubmissionCount;
    uint256 public totalBetCount;
    uint256 public totalPlatformVolume;
    uint256 public totalFeesCollected;
    
    // Core mappings
    mapping(uint256 => Market) public markets;
    mapping(uint256 => Submission) public submissions;
    mapping(uint256 => Bet) public bets;
    
    // Relationship mappings
    mapping(uint256 => uint256[]) public marketSubmissions;     // marketId => submissionIds
    mapping(uint256 => uint256[]) public submissionBets;        // submissionId => betIds
    mapping(address => uint256[]) public userMarkets;           // user => marketIds created
    mapping(address => uint256[]) public userSubmissions;       // user => submissionIds
    mapping(address => uint256[]) public userBets;              // user => betIds
    mapping(string => uint256[]) public actorMarkets;           // actorUsername => marketIds
    
    // Stats and tracking
    mapping(uint256 => MarketStats) public marketStats;
    mapping(address => uint256) public userTotalVolume;
    mapping(address => uint256) public userTotalWinnings;
    mapping(address => uint256) public userMarketCount;
    mapping(bytes32 => bool) public usedTransactionHashes;
    
    // Oracle management
    mapping(uint256 => mapping(address => bool)) public isMarketOracle;
    mapping(address => uint256[]) public oracleMarkets;
    
    // Events
    event MarketCreated(
        uint256 indexed marketId, 
        address indexed creator, 
        string actorUsername,
        string question, 
        uint256 endTime
    );
    event SubmissionCreated(
        uint256 indexed submissionId, 
        uint256 indexed marketId, 
        address indexed creator, 
        string predictedText,
        string submissionType
    );
    event BetPlaced(
        uint256 indexed betId, 
        uint256 indexed submissionId, 
        address indexed bettor, 
        uint256 amount
    );
    event MarketResolved(
        uint256 indexed marketId, 
        uint256 winningSubmissionId,
        uint256 totalPayout
    );
    event PayoutDistributed(
        address indexed recipient, 
        uint256 amount,
        uint256 marketId
    );
    event PlatformFeeCollected(uint256 amount, uint256 marketId);
    event MarketStatsUpdated(uint256 indexed marketId);
    
    modifier marketExists(uint256 _marketId) {
        require(_marketId < marketCount, "Market does not exist");
        _;
    }
    
    modifier marketActive(uint256 _marketId) {
        require(block.timestamp >= markets[_marketId].startTime, "Market not started");
        require(block.timestamp < markets[_marketId].endTime, "Market has ended");
        require(!markets[_marketId].resolved, "Market already resolved");
        _;
    }
    
    modifier marketEnded(uint256 _marketId) {
        require(block.timestamp >= markets[_marketId].endTime, "Market still active");
        _;
    }
    
    modifier onlyMarketOracle(uint256 _marketId) {
        require(isMarketOracle[_marketId][msg.sender], "Not authorized oracle");
        _;
    }
    
    constructor(address _actorRegistry) Ownable(msg.sender) {
        actorRegistry = ActorRegistry(_actorRegistry);
        marketCount = 0;
        totalSubmissionCount = 0;
        totalBetCount = 0;
    }
    
    /**
     * @dev Create a new prediction market (fully on-chain)
     */
    function createMarket(
        string memory _question,
        string memory _actorUsername,
        uint256 _duration,
        address[] memory _oracleWallets,
        string memory _metadata
    ) external payable returns (uint256) {
        require(_duration >= MINIMUM_MARKET_DURATION, "Duration too short");
        require(_duration <= MAXIMUM_MARKET_DURATION, "Duration too long");
        require(bytes(_question).length > 0, "Question cannot be empty");
        require(bytes(_actorUsername).length > 0, "Actor username required");
        require(_oracleWallets.length >= 3, "At least 3 oracles required");
        
        // Verify actor exists and is active
        require(actorRegistry.isActorActive(_actorUsername), "Actor not active");
        
        uint256 marketId = marketCount++;
        Market storage newMarket = markets[marketId];
        
        newMarket.question = _question;
        newMarket.actorUsername = _actorUsername;
        newMarket.creator = msg.sender;
        newMarket.startTime = block.timestamp;
        newMarket.endTime = block.timestamp + _duration;
        newMarket.createdAt = block.timestamp;
        newMarket.oracleWallets = _oracleWallets;
        newMarket.metadata = _metadata;
        
        // Initialize oracle mappings
        for (uint i = 0; i < _oracleWallets.length; i++) {
            isMarketOracle[marketId][_oracleWallets[i]] = true;
            oracleMarkets[_oracleWallets[i]].push(marketId);
        }
        
        // Track relationships
        userMarkets[msg.sender].push(marketId);
        actorMarkets[_actorUsername].push(marketId);
        userMarketCount[msg.sender]++;
        
        // Initialize market stats
        marketStats[marketId].lastActivityTime = block.timestamp;
        
        emit MarketCreated(marketId, msg.sender, _actorUsername, _question, newMarket.endTime);
        emit MarketStatsUpdated(marketId);
        
        return marketId;
    }
    
    /**
     * @dev Create a submission for a market (fully on-chain)
     */
    function createSubmission(
        uint256 _marketId,
        string memory _predictedText,
        string memory _submissionType
    ) external payable marketExists(_marketId) marketActive(_marketId) returns (uint256) {
        require(msg.value >= MINIMUM_BET, "Stake too low");
        require(bytes(_predictedText).length > 0 || keccak256(bytes(_submissionType)) == keccak256(bytes("null")), 
                "Predicted text required for non-null submissions");
        
        // Validate submission type
        require(
            keccak256(bytes(_submissionType)) == keccak256(bytes("original")) ||
            keccak256(bytes(_submissionType)) == keccak256(bytes("competitor")) ||
            keccak256(bytes(_submissionType)) == keccak256(bytes("null")),
            "Invalid submission type"
        );
        
        // Check if this is the first submission (original)
        if (markets[_marketId].submissionCount == 0) {
            require(keccak256(bytes(_submissionType)) == keccak256(bytes("original")), 
                    "First submission must be original");
        }
        
        uint256 submissionId = totalSubmissionCount++;
        Submission storage newSubmission = submissions[submissionId];
        
        newSubmission.marketId = _marketId;
        newSubmission.creator = msg.sender;
        newSubmission.predictedText = _predictedText;
        newSubmission.stake = msg.value;
        newSubmission.totalBets = msg.value;
        newSubmission.betCount = 1;
        newSubmission.createdAt = block.timestamp;
        newSubmission.submissionType = _submissionType;
        newSubmission.textHash = keccak256(abi.encodePacked(_predictedText));
        
        // Update market data
        markets[_marketId].submissionCount++;
        markets[_marketId].totalVolume += msg.value;
        marketSubmissions[_marketId].push(submissionId);
        
        // Update user data
        userSubmissions[msg.sender].push(submissionId);
        userTotalVolume[msg.sender] += msg.value;
        
        // Update market stats
        _updateMarketStats(_marketId, msg.value, msg.sender);
        
        // Calculate platform fee
        uint256 platformFee = (msg.value * PLATFORM_FEE) / 100;
        markets[_marketId].platformFeeCollected += platformFee;
        totalFeesCollected += platformFee;
        
        emit SubmissionCreated(submissionId, _marketId, msg.sender, _predictedText, _submissionType);
        emit PlatformFeeCollected(platformFee, _marketId);
        emit MarketStatsUpdated(_marketId);
        
        return submissionId;
    }
    
    /**
     * @dev Place a bet on a submission (fully on-chain)
     */
    function placeBet(
        uint256 _submissionId,
        bytes32 _transactionHash
    ) external payable nonReentrant returns (uint256) {
        require(msg.value >= MINIMUM_BET, "Bet too low");
        require(_submissionId < totalSubmissionCount, "Submission does not exist");
        require(!usedTransactionHashes[_transactionHash], "Transaction already used");
        
        Submission storage submission = submissions[_submissionId];
        uint256 marketId = submission.marketId;
        
        require(block.timestamp >= markets[marketId].startTime, "Market not started");
        require(block.timestamp < markets[marketId].endTime, "Market has ended");
        require(!markets[marketId].resolved, "Market already resolved");
        
        uint256 betId = totalBetCount++;
        Bet storage newBet = bets[betId];
        
        newBet.bettor = msg.sender;
        newBet.marketId = marketId;
        newBet.submissionId = _submissionId;
        newBet.amount = msg.value;
        newBet.timestamp = block.timestamp;
        newBet.transactionHash = _transactionHash;
        
        // Calculate potential payout (simplified for now)
        uint256 totalPool = markets[marketId].totalVolume + msg.value;
        uint256 submissionPool = submission.totalBets + msg.value;
        newBet.potentialPayout = (msg.value * totalPool) / submissionPool;
        
        // Update submission data
        submission.totalBets += msg.value;
        submission.betCount++;
        
        // Update market data
        markets[marketId].totalVolume += msg.value;
        markets[marketId].betCount++;
        
        // Update relationships
        submissionBets[_submissionId].push(betId);
        userBets[msg.sender].push(betId);
        
        // Update user data
        userTotalVolume[msg.sender] += msg.value;
        
        // Mark transaction hash as used
        usedTransactionHashes[_transactionHash] = true;
        
        // Update market stats
        _updateMarketStats(marketId, msg.value, msg.sender);
        
        // Calculate platform fee
        uint256 platformFee = (msg.value * PLATFORM_FEE) / 100;
        markets[marketId].platformFeeCollected += platformFee;
        totalFeesCollected += platformFee;
        totalPlatformVolume += msg.value;
        
        emit BetPlaced(betId, _submissionId, msg.sender, msg.value);
        emit PlatformFeeCollected(platformFee, marketId);
        emit MarketStatsUpdated(marketId);
        
        return betId;
    }
    
    /**
     * @dev Resolve a market (called by oracle system)
     */
    function resolveMarket(
        uint256 _marketId,
        uint256 _winningSubmissionId,
        uint256[] memory _levenshteinDistances
    ) external marketExists(_marketId) marketEnded(_marketId) onlyMarketOracle(_marketId) {
        require(!markets[_marketId].resolved, "Already resolved");
        require(_winningSubmissionId < totalSubmissionCount, "Invalid submission");
        require(submissions[_winningSubmissionId].marketId == _marketId, "Submission not in market");
        
        Market storage market = markets[_marketId];
        market.resolved = true;
        market.winningSubmissionId = _winningSubmissionId;
        market.resolvedAt = block.timestamp;
        
        // Update submission data
        submissions[_winningSubmissionId].isWinner = true;
        
        // Store Levenshtein distances for all submissions
        uint256[] memory submissionIds = marketSubmissions[_marketId];
        require(_levenshteinDistances.length == submissionIds.length, "Distance count mismatch");
        
        for (uint i = 0; i < submissionIds.length; i++) {
            submissions[submissionIds[i]].levenshteinDistance = _levenshteinDistances[i];
        }
        
        // Calculate total payout
        uint256 totalPayout = market.totalVolume - market.platformFeeCollected;
        
        emit MarketResolved(_marketId, _winningSubmissionId, totalPayout);
        emit MarketStatsUpdated(_marketId);
    }
    
    /**
     * @dev Claim winnings for a bet
     */
    function claimWinnings(uint256 _betId) external nonReentrant {
        require(_betId < totalBetCount, "Bet does not exist");
        Bet storage bet = bets[_betId];
        require(bet.bettor == msg.sender, "Not your bet");
        require(!bet.paid, "Already claimed");
        
        uint256 marketId = bet.marketId;
        Market storage market = markets[marketId];
        require(market.resolved, "Market not resolved");
        
        uint256 submissionId = bet.submissionId;
        require(submissions[submissionId].isWinner, "Not a winning bet");
        
        // Calculate payout
        uint256 totalPool = market.totalVolume - market.platformFeeCollected;
        uint256 winnerPool = submissions[market.winningSubmissionId].totalBets;
        uint256 payout = (bet.amount * totalPool) / winnerPool;
        
        // Mark as paid
        bet.paid = true;
        
        // Update user winnings
        userTotalWinnings[msg.sender] += payout;
        
        // Transfer winnings
        (bool success, ) = payable(msg.sender).call{value: payout}("");
        require(success, "Transfer failed");
        
        emit PayoutDistributed(msg.sender, payout, marketId);
    }
    
    /**
     * @dev Internal function to update market statistics
     */
    function _updateMarketStats(uint256 _marketId, uint256 _amount, address _bettor) internal {
        MarketStats storage stats = marketStats[_marketId];
        
        stats.totalVolume = markets[_marketId].totalVolume;
        stats.totalSubmissions = markets[_marketId].submissionCount;
        stats.totalBets = markets[_marketId].betCount;
        stats.lastActivityTime = block.timestamp;
        
        if (_amount > stats.highestStake) {
            stats.highestStake = _amount;
        }
        
        uint256 bettorVolume = 0;
        uint256[] memory userBetIds = userBets[_bettor];
        for (uint i = 0; i < userBetIds.length; i++) {
            if (bets[userBetIds[i]].marketId == _marketId) {
                bettorVolume += bets[userBetIds[i]].amount;
            }
        }
        
        if (bettorVolume > stats.topBettorVolume) {
            stats.topBettor = _bettor;
            stats.topBettorVolume = bettorVolume;
        }
        
        if (stats.totalBets > 0) {
            stats.averageBetSize = stats.totalVolume / stats.totalBets;
        }
    }
    
    /**
     * @dev Get market details with all submissions
     */
    function getMarketDetails(uint256 _marketId) external view returns (
        Market memory market,
        uint256[] memory submissionIds,
        MarketStats memory stats
    ) {
        return (
            markets[_marketId],
            marketSubmissions[_marketId],
            marketStats[_marketId]
        );
    }
    
    /**
     * @dev Get submission details with all bets
     */
    function getSubmissionDetails(uint256 _submissionId) external view returns (
        Submission memory submission,
        uint256[] memory betIds
    ) {
        return (
            submissions[_submissionId],
            submissionBets[_submissionId]
        );
    }
    
    /**
     * @dev Get user's complete activity
     */
    function getUserActivity(address _user) external view returns (
        uint256[] memory marketIds,
        uint256[] memory submissionIds,
        uint256[] memory betIds,
        uint256 totalVolume,
        uint256 totalWinnings
    ) {
        return (
            userMarkets[_user],
            userSubmissions[_user],
            userBets[_user],
            userTotalVolume[_user],
            userTotalWinnings[_user]
        );
    }
    
    /**
     * @dev Get markets for a specific actor
     */
    function getActorMarkets(string memory _actorUsername) external view returns (uint256[] memory) {
        return actorMarkets[_actorUsername];
    }
    
    /**
     * @dev Withdraw platform fees (owner only)
     */
    function withdrawPlatformFees() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No fees to withdraw");
        
        (bool success, ) = payable(owner()).call{value: balance}("");
        require(success, "Withdrawal failed");
    }
    
    /**
     * @dev Emergency pause (owner only)
     */
    function emergencyPause() external onlyOwner {
        // Implementation for emergency pause if needed
        // This would pause all market creation and betting
    }
}