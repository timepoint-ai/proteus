// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./EnhancedPredictionMarket.sol";

/**
 * @title AdvancedMarkets
 * @notice Phase 13 - Advanced market types and features
 */
contract AdvancedMarkets is AccessControl, ReentrancyGuard {
    bytes32 public constant MARKET_CREATOR_ROLE = keccak256("MARKET_CREATOR_ROLE");
    
    EnhancedPredictionMarket public predictionMarket;
    
    // Market types
    enum MarketType {
        STANDARD,        // Original single prediction
        MULTI_CHOICE,    // Multiple choice options
        CONDITIONAL,     // Depends on another market
        RANGE,          // Numeric range prediction
        COMPOSITE       // Combination of multiple predictions
    }
    
    struct AdvancedMarket {
        bytes32 marketId;
        MarketType marketType;
        bytes32[] options;      // For multi-choice
        bytes32 dependsOn;      // For conditional markets
        uint256 minValue;       // For range markets
        uint256 maxValue;       // For range markets
        bytes32[] components;   // For composite markets
        mapping(bytes32 => uint256) optionStakes;
        mapping(address => mapping(bytes32 => uint256)) userOptionBets;
    }
    
    // Advanced market storage
    mapping(bytes32 => AdvancedMarket) public advancedMarkets;
    mapping(address => uint256) public userReputation;
    mapping(bytes32 => bool) public marketExists;
    
    // Events
    event AdvancedMarketCreated(
        bytes32 indexed marketId,
        MarketType marketType,
        address indexed creator,
        uint256 timestamp
    );
    
    event MultiChoiceOptionAdded(
        bytes32 indexed marketId,
        bytes32 optionId,
        string optionText
    );
    
    event ConditionalMarketLinked(
        bytes32 indexed marketId,
        bytes32 indexed dependsOnMarketId
    );
    
    event RangeMarketCreated(
        bytes32 indexed marketId,
        uint256 minValue,
        uint256 maxValue
    );
    
    event ReputationUpdated(
        address indexed user,
        uint256 oldReputation,
        uint256 newReputation
    );
    
    constructor(address _predictionMarket) {
        predictionMarket = EnhancedPredictionMarket(_predictionMarket);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MARKET_CREATOR_ROLE, msg.sender);
    }
    
    /**
     * @notice Create a multi-choice market
     */
    function createMultiChoiceMarket(
        bytes32 marketId,
        string[] memory options,
        uint256 endTime
    ) external onlyRole(MARKET_CREATOR_ROLE) {
        require(!marketExists[marketId], "Market already exists");
        require(options.length >= 2 && options.length <= 10, "Invalid option count");
        
        AdvancedMarket storage market = advancedMarkets[marketId];
        market.marketId = marketId;
        market.marketType = MarketType.MULTI_CHOICE;
        
        // Store options
        for (uint i = 0; i < options.length; i++) {
            bytes32 optionId = keccak256(abi.encodePacked(marketId, i, options[i]));
            market.options.push(optionId);
            emit MultiChoiceOptionAdded(marketId, optionId, options[i]);
        }
        
        marketExists[marketId] = true;
        emit AdvancedMarketCreated(marketId, MarketType.MULTI_CHOICE, msg.sender, block.timestamp);
    }
    
    /**
     * @notice Create a conditional market that depends on another
     */
    function createConditionalMarket(
        bytes32 marketId,
        bytes32 dependsOnMarketId,
        uint256 endTime
    ) external onlyRole(MARKET_CREATOR_ROLE) {
        require(!marketExists[marketId], "Market already exists");
        require(marketExists[dependsOnMarketId], "Dependent market does not exist");
        
        AdvancedMarket storage market = advancedMarkets[marketId];
        market.marketId = marketId;
        market.marketType = MarketType.CONDITIONAL;
        market.dependsOn = dependsOnMarketId;
        
        marketExists[marketId] = true;
        emit ConditionalMarketLinked(marketId, dependsOnMarketId);
        emit AdvancedMarketCreated(marketId, MarketType.CONDITIONAL, msg.sender, block.timestamp);
    }
    
    /**
     * @notice Create a range prediction market
     */
    function createRangeMarket(
        bytes32 marketId,
        uint256 minValue,
        uint256 maxValue,
        uint256 endTime
    ) external onlyRole(MARKET_CREATOR_ROLE) {
        require(!marketExists[marketId], "Market already exists");
        require(maxValue > minValue, "Invalid range");
        
        AdvancedMarket storage market = advancedMarkets[marketId];
        market.marketId = marketId;
        market.marketType = MarketType.RANGE;
        market.minValue = minValue;
        market.maxValue = maxValue;
        
        marketExists[marketId] = true;
        emit RangeMarketCreated(marketId, minValue, maxValue);
        emit AdvancedMarketCreated(marketId, MarketType.RANGE, msg.sender, block.timestamp);
    }
    
    /**
     * @notice Bet on a multi-choice option
     */
    function betOnOption(
        bytes32 marketId,
        bytes32 optionId
    ) external payable nonReentrant {
        require(marketExists[marketId], "Market does not exist");
        AdvancedMarket storage market = advancedMarkets[marketId];
        require(market.marketType == MarketType.MULTI_CHOICE, "Not a multi-choice market");
        
        // Verify option exists
        bool validOption = false;
        for (uint i = 0; i < market.options.length; i++) {
            if (market.options[i] == optionId) {
                validOption = true;
                break;
            }
        }
        require(validOption, "Invalid option");
        
        // Record bet
        market.optionStakes[optionId] += msg.value;
        market.userOptionBets[msg.sender][optionId] += msg.value;
        
        // Update user reputation based on participation
        userReputation[msg.sender] += 1;
        emit ReputationUpdated(msg.sender, userReputation[msg.sender] - 1, userReputation[msg.sender]);
    }
    
    /**
     * @notice Calculate reputation score for a user
     */
    function calculateReputation(address user) external view returns (uint256) {
        // Base reputation from participation
        uint256 reputation = userReputation[user];
        
        // Could add more factors:
        // - Successful predictions
        // - Market creation
        // - Oracle participation
        // - Time-weighted activity
        
        return reputation;
    }
    
    /**
     * @notice Get market details
     */
    function getAdvancedMarket(bytes32 marketId) external view returns (
        MarketType marketType,
        uint256 optionCount,
        bytes32 dependsOn,
        uint256 minValue,
        uint256 maxValue
    ) {
        AdvancedMarket storage market = advancedMarkets[marketId];
        return (
            market.marketType,
            market.options.length,
            market.dependsOn,
            market.minValue,
            market.maxValue
        );
    }
    
    /**
     * @notice Get user's bet on a specific option
     */
    function getUserOptionBet(
        bytes32 marketId,
        address user,
        bytes32 optionId
    ) external view returns (uint256) {
        return advancedMarkets[marketId].userOptionBets[user][optionId];
    }
    
    /**
     * @notice Get total stake for an option
     */
    function getOptionStake(
        bytes32 marketId,
        bytes32 optionId
    ) external view returns (uint256) {
        return advancedMarkets[marketId].optionStakes[optionId];
    }
}