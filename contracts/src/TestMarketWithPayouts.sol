// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

interface IDistributedPayoutManager {
    function distributeFees(uint256 amount) external;
}

contract TestMarketWithPayouts {
    struct Market {
        address creator;
        uint256 totalVolume;
        uint256 platformFee;
        bool resolved;
        string prediction;
        string actualResult;
    }
    
    mapping(uint256 => Market) public markets;
    uint256 public marketCount;
    
    address public payoutManager;
    uint256 public constant PLATFORM_FEE_PERCENTAGE = 7; // 7% platform fee
    
    event MarketCreated(uint256 indexed marketId, address creator, string prediction);
    event MarketResolved(uint256 indexed marketId, string actualResult, uint256 platformFee);
    event PayoutDistributed(uint256 indexed marketId, uint256 amount);
    
    constructor(address _payoutManager) {
        payoutManager = _payoutManager;
    }
    
    // Create a market and add volume
    function createAndFundMarket(string memory prediction) external payable returns (uint256) {
        require(msg.value > 0, "Must send ETH");
        
        marketCount++;
        uint256 marketId = marketCount;
        
        uint256 platformFee = (msg.value * PLATFORM_FEE_PERCENTAGE) / 100;
        
        markets[marketId] = Market({
            creator: msg.sender,
            totalVolume: msg.value,
            platformFee: platformFee,
            resolved: false,
            prediction: prediction,
            actualResult: ""
        });
        
        emit MarketCreated(marketId, msg.sender, prediction);
        return marketId;
    }
    
    // Add more volume to a market (simulating bets)
    function addVolume(uint256 marketId) external payable {
        require(marketId > 0 && marketId <= marketCount, "Invalid market");
        require(!markets[marketId].resolved, "Market already resolved");
        require(msg.value > 0, "Must send ETH");
        
        Market storage market = markets[marketId];
        market.totalVolume += msg.value;
        
        // Recalculate platform fee
        market.platformFee = (market.totalVolume * PLATFORM_FEE_PERCENTAGE) / 100;
    }
    
    // Resolve market and distribute payouts
    function resolveMarket(uint256 marketId, string memory actualResult) external {
        require(marketId > 0 && marketId <= marketCount, "Invalid market");
        require(!markets[marketId].resolved, "Already resolved");
        
        Market storage market = markets[marketId];
        market.resolved = true;
        market.actualResult = actualResult;
        
        emit MarketResolved(marketId, actualResult, market.platformFee);
        
        // Send platform fee to payout manager and trigger distribution
        if (market.platformFee > 0) {
            // Send fee to payout manager
            (bool sent, ) = payoutManager.call{value: market.platformFee}("");
            require(sent, "Failed to send fees");
            
            // Trigger distribution
            IDistributedPayoutManager(payoutManager).distributeFees(market.platformFee);
            
            emit PayoutDistributed(marketId, market.platformFee);
        }
        
        // Send remaining funds back to creator (simplified for testing)
        uint256 remaining = market.totalVolume - market.platformFee;
        if (remaining > 0) {
            (bool sentToCreator, ) = market.creator.call{value: remaining}("");
            require(sentToCreator, "Failed to send to creator");
        }
    }
    
    // Get market details
    function getMarket(uint256 marketId) external view returns (
        address creator,
        uint256 totalVolume,
        uint256 platformFee,
        bool resolved,
        string memory prediction,
        string memory actualResult
    ) {
        Market memory market = markets[marketId];
        return (
            market.creator,
            market.totalVolume,
            market.platformFee,
            market.resolved,
            market.prediction,
            market.actualResult
        );
    }
    
    // Emergency withdraw (only for testing cleanup)
    function emergencyWithdraw() external {
        require(msg.sender == 0x2b5fBAC3CAAf8937767b458ac6Ed38Cf0DF6b6EF, "Only test owner");
        payable(msg.sender).transfer(address(this).balance);
    }
}