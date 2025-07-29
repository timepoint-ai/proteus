// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./PredictionMarket.sol";
import "./ClockchainOracle.sol";

/**
 * @title PayoutManager
 * @dev Automated payout system for resolved prediction markets
 */
contract PayoutManager is ReentrancyGuard, Ownable {
    PredictionMarket public predictionMarket;
    ClockchainOracle public oracle;
    
    struct Payout {
        address recipient;
        uint256 amount;
        uint256 marketId;
        uint256 submissionId;
        bool claimed;
        uint256 timestamp;
    }
    
    struct MarketPayoutInfo {
        uint256 totalPool;
        uint256 winnerPool;
        uint256 platformFees;
        uint256 totalPayouts;
        bool processed;
        mapping(address => uint256) userPayouts;
        mapping(address => bool) hasClaimed;
    }
    
    uint256 public payoutCount;
    uint256 public totalDistributed;
    uint256 public platformFeesCollected;
    
    mapping(uint256 => Payout) public payouts;
    mapping(uint256 => MarketPayoutInfo) public marketPayouts;
    mapping(address => uint256[]) public userPayouts;
    mapping(address => uint256) public userTotalWinnings;
    
    event PayoutCalculated(uint256 indexed marketId, uint256 totalPool, uint256 winnerPool);
    event PayoutClaimed(address indexed recipient, uint256 amount, uint256 marketId);
    event PlatformFeeWithdrawn(address indexed recipient, uint256 amount);
    event EmergencyWithdrawal(address indexed recipient, uint256 amount);
    
    modifier marketResolved(uint256 _marketId) {
        (, , , , bool resolved, , , , , , ) = predictionMarket.markets(_marketId);
        require(resolved, "Market not resolved");
        _;
    }
    
    constructor(address _predictionMarket, address _oracle) {
        predictionMarket = PredictionMarket(_predictionMarket);
        oracle = ClockchainOracle(_oracle);
    }
    
    /**
     * @dev Calculate payouts for a resolved market
     */
    function calculatePayouts(uint256 _marketId) external marketResolved(_marketId) {
        MarketPayoutInfo storage payoutInfo = marketPayouts[_marketId];
        require(!payoutInfo.processed, "Payouts already calculated");
        
        (
            ,
            ,
            ,
            ,
            ,
            uint256 winningSubmissionId,
            uint256 totalVolume,
            ,
            ,
            ,
            uint256 platformFeeCollected
        ) = predictionMarket.markets(_marketId);
        
        // Get all submissions for the market
        uint256[] memory submissionIds = predictionMarket.getMarketSubmissions(_marketId);
        
        uint256 totalLoserPool = 0;
        uint256 totalWinnerStake = 0;
        
        // Calculate winner and loser pools
        for (uint256 i = 0; i < submissionIds.length; i++) {
            (
                ,
                ,
                ,
                uint256 stake,
                uint256 totalBets,
                ,
                ,
                ,
            ) = predictionMarket.submissions(submissionIds[i]);
            
            if (submissionIds[i] == winningSubmissionId) {
                totalWinnerStake = totalBets;
            } else {
                totalLoserPool += totalBets;
            }
        }
        
        payoutInfo.totalPool = totalVolume - platformFeeCollected;
        payoutInfo.winnerPool = totalWinnerStake;
        payoutInfo.platformFees = platformFeeCollected;
        payoutInfo.processed = true;
        
        platformFeesCollected += platformFeeCollected;
        
        // Calculate individual payouts for winning bettors
        if (totalWinnerStake > 0) {
            _calculateWinnerPayouts(_marketId, winningSubmissionId, totalLoserPool, totalWinnerStake);
        }
        
        emit PayoutCalculated(_marketId, payoutInfo.totalPool, payoutInfo.winnerPool);
    }
    
    /**
     * @dev Calculate individual winner payouts
     */
    function _calculateWinnerPayouts(
        uint256 _marketId,
        uint256 _winningSubmissionId,
        uint256 _loserPool,
        uint256 _winnerPool
    ) internal {
        MarketPayoutInfo storage payoutInfo = marketPayouts[_marketId];
        
        // Get all bets
        uint256 betCount = predictionMarket.betCount();
        
        for (uint256 i = 0; i < betCount; i++) {
            (
                address bettor,
                uint256 submissionId,
                uint256 amount,
                
            ) = predictionMarket.bets(i);
            
            if (submissionId == _winningSubmissionId) {
                // Calculate proportional share of loser pool
                uint256 winnerShare = amount + (amount * _loserPool / _winnerPool);
                
                payoutInfo.userPayouts[bettor] += winnerShare;
                
                // Create payout record
                uint256 payoutId = payoutCount++;
                payouts[payoutId] = Payout({
                    recipient: bettor,
                    amount: winnerShare,
                    marketId: _marketId,
                    submissionId: _winningSubmissionId,
                    claimed: false,
                    timestamp: block.timestamp
                });
                
                userPayouts[bettor].push(payoutId);
                payoutInfo.totalPayouts += winnerShare;
            }
        }
        
        // Also pay the original submission creator
        (
            ,
            address creator,
            ,
            uint256 stake,
            ,
            ,
            ,
            ,
        ) = predictionMarket.submissions(_winningSubmissionId);
        
        uint256 creatorShare = stake + (stake * _loserPool / _winnerPool);
        payoutInfo.userPayouts[creator] += creatorShare;
        
        uint256 creatorPayoutId = payoutCount++;
        payouts[creatorPayoutId] = Payout({
            recipient: creator,
            amount: creatorShare,
            marketId: _marketId,
            submissionId: _winningSubmissionId,
            claimed: false,
            timestamp: block.timestamp
        });
        
        userPayouts[creator].push(creatorPayoutId);
        payoutInfo.totalPayouts += creatorShare;
    }
    
    /**
     * @dev Claim payouts for a specific market
     */
    function claimPayout(uint256 _marketId) external nonReentrant {
        MarketPayoutInfo storage payoutInfo = marketPayouts[_marketId];
        require(payoutInfo.processed, "Payouts not calculated");
        require(!payoutInfo.hasClaimed[msg.sender], "Already claimed");
        require(payoutInfo.userPayouts[msg.sender] > 0, "No payout available");
        
        uint256 amount = payoutInfo.userPayouts[msg.sender];
        payoutInfo.hasClaimed[msg.sender] = true;
        userTotalWinnings[msg.sender] += amount;
        totalDistributed += amount;
        
        payable(msg.sender).transfer(amount);
        
        emit PayoutClaimed(msg.sender, amount, _marketId);
    }
    
    /**
     * @dev Claim all available payouts
     */
    function claimAllPayouts() external nonReentrant {
        uint256[] memory userPayoutIds = userPayouts[msg.sender];
        uint256 totalClaim = 0;
        
        for (uint256 i = 0; i < userPayoutIds.length; i++) {
            Payout storage payout = payouts[userPayoutIds[i]];
            
            if (!payout.claimed && payout.recipient == msg.sender) {
                payout.claimed = true;
                totalClaim += payout.amount;
                emit PayoutClaimed(msg.sender, payout.amount, payout.marketId);
            }
        }
        
        require(totalClaim > 0, "No unclaimed payouts");
        
        userTotalWinnings[msg.sender] += totalClaim;
        totalDistributed += totalClaim;
        
        payable(msg.sender).transfer(totalClaim);
    }
    
    /**
     * @dev Get user's payouts for a market
     */
    function getUserMarketPayout(address _user, uint256 _marketId) external view returns (uint256) {
        return marketPayouts[_marketId].userPayouts[_user];
    }
    
    /**
     * @dev Get user's unclaimed payouts
     */
    function getUserUnclaimedPayouts(address _user) external view returns (uint256) {
        uint256[] memory userPayoutIds = userPayouts[_user];
        uint256 unclaimed = 0;
        
        for (uint256 i = 0; i < userPayoutIds.length; i++) {
            Payout storage payout = payouts[userPayoutIds[i]];
            
            if (!payout.claimed && payout.recipient == _user) {
                unclaimed += payout.amount;
            }
        }
        
        return unclaimed;
    }
    
    /**
     * @dev Withdraw platform fees (owner only)
     */
    function withdrawPlatformFees() external onlyOwner {
        uint256 amount = platformFeesCollected;
        require(amount > 0, "No fees to withdraw");
        
        platformFeesCollected = 0;
        payable(owner()).transfer(amount);
        
        emit PlatformFeeWithdrawn(owner(), amount);
    }
    
    /**
     * @dev Emergency withdrawal (owner only)
     */
    function emergencyWithdraw() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        payable(owner()).transfer(balance);
        
        emit EmergencyWithdrawal(owner(), balance);
    }
    
    /**
     * @dev Receive ETH from PredictionMarket
     */
    receive() external payable {
        // Accept ETH transfers
    }
}