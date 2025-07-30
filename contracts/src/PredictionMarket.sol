// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title PredictionMarket
 * @dev Core prediction market contract for Clockchain on BASE
 */
contract PredictionMarket is ReentrancyGuard, Ownable {

    struct Market {
        string question;
        address creator;
        uint256 startTime;
        uint256 endTime;
        bool resolved;
        uint256 winningSubmissionId;
        uint256 totalVolume;
        string actorTwitterHandle;
        string targetTweetId;
        bool xcomOnly;
        uint256 platformFeeCollected;
    }

    struct Submission {
        uint256 marketId;
        address creator;
        string predictedText;
        uint256 stake;
        uint256 totalBets;
        uint256 levenshteinDistance;
        bool isWinner;
        string screenshotIpfsHash;
        bytes32 screenshotBase64Hash;
    }

    struct Bet {
        address bettor;
        uint256 submissionId;
        uint256 amount;
        uint256 timestamp;
    }

    uint256 public constant PLATFORM_FEE = 7; // 7%
    uint256 public marketCount;
    uint256 public submissionCount;
    uint256 public betCount;

    mapping(uint256 => Market) public markets;
    mapping(uint256 => Submission) public submissions;
    mapping(uint256 => Bet) public bets;
    mapping(uint256 => uint256[]) public marketSubmissions;
    mapping(address => uint256[]) public userSubmissions;
    mapping(address => uint256[]) public userBets;

    event MarketCreated(uint256 indexed marketId, address indexed creator, string question, uint256 endTime);
    event SubmissionCreated(uint256 indexed submissionId, uint256 indexed marketId, address indexed creator, string predictedText);
    event BetPlaced(uint256 indexed betId, uint256 indexed submissionId, address indexed bettor, uint256 amount);
    event MarketResolved(uint256 indexed marketId, uint256 winningSubmissionId);
    event PayoutDistributed(address indexed recipient, uint256 amount);

    modifier marketExists(uint256 _marketId) {
        require(_marketId < marketCount, "Market does not exist");
        _;
    }

    modifier marketActive(uint256 _marketId) {
        require(block.timestamp < markets[_marketId].endTime, "Market has ended");
        require(!markets[_marketId].resolved, "Market already resolved");
        _;
    }

    modifier marketEnded(uint256 _marketId) {
        require(block.timestamp >= markets[_marketId].endTime, "Market still active");
        _;
    }

    constructor() Ownable(msg.sender) {
        marketCount = 0;
        submissionCount = 0;
        betCount = 0;
    }

    /**
     * @dev Create a new prediction market
     */
    function createMarket(
        string memory _question,
        uint256 _duration,
        string memory _actorTwitterHandle,
        bool _xcomOnly
    ) external payable returns (uint256) {
        require(_duration >= 300, "Market duration must be at least 5 minutes");
        require(_duration <= 7776000, "Market duration cannot exceed 90 days");
        require(bytes(_question).length > 0, "Question cannot be empty");
        require(msg.value >= 0.01 ether, "Minimum market creation fee required");

        uint256 marketId = marketCount++;
        markets[marketId] = Market({
            question: _question,
            creator: msg.sender,
            startTime: block.timestamp,
            endTime: block.timestamp + _duration,
            resolved: false,
            winningSubmissionId: 0,
            totalVolume: msg.value,
            actorTwitterHandle: _actorTwitterHandle,
            targetTweetId: "",
            xcomOnly: _xcomOnly,
            platformFeeCollected: 0
        });

        emit MarketCreated(marketId, msg.sender, _question, block.timestamp + _duration);
        return marketId;
    }

    /**
     * @dev Create a submission for a market
     */
    function createSubmission(
        uint256 _marketId,
        string memory _predictedText,
        string memory _screenshotIpfsHash
    ) external payable marketExists(_marketId) marketActive(_marketId) returns (uint256) {
        require(msg.value >= 0.001 ether, "Minimum submission stake required");
        require(bytes(_predictedText).length > 0, "Predicted text cannot be empty");

        uint256 submissionId = submissionCount++;
        uint256 fee = (msg.value * PLATFORM_FEE) / 100;
        uint256 stake = msg.value - fee;

        submissions[submissionId] = Submission({
            marketId: _marketId,
            creator: msg.sender,
            predictedText: _predictedText,
            stake: stake,
            totalBets: stake,
            levenshteinDistance: type(uint256).max,
            isWinner: false,
            screenshotIpfsHash: _screenshotIpfsHash,
            screenshotBase64Hash: keccak256(bytes(_screenshotIpfsHash))
        });

        markets[_marketId].totalVolume = markets[_marketId].totalVolume + msg.value;
        markets[_marketId].platformFeeCollected = markets[_marketId].platformFeeCollected + fee;

        marketSubmissions[_marketId].push(submissionId);
        userSubmissions[msg.sender].push(submissionId);

        emit SubmissionCreated(submissionId, _marketId, msg.sender, _predictedText);
        return submissionId;
    }

    /**
     * @dev Place a bet on a submission
     */
    function placeBet(uint256 _submissionId) external payable nonReentrant returns (uint256) {
        require(_submissionId < submissionCount, "Submission does not exist");
        require(msg.value >= 0.0001 ether, "Minimum bet amount required");
        
        Submission storage submission = submissions[_submissionId];
        Market storage market = markets[submission.marketId];
        
        require(!market.resolved, "Market already resolved");
        require(block.timestamp < market.endTime, "Market has ended");

        uint256 betId = betCount++;
        uint256 fee = (msg.value * PLATFORM_FEE) / 100;
        uint256 betAmount = msg.value - fee;

        bets[betId] = Bet({
            bettor: msg.sender,
            submissionId: _submissionId,
            amount: betAmount,
            timestamp: block.timestamp
        });

        submission.totalBets = submission.totalBets + betAmount;
        market.totalVolume = market.totalVolume + msg.value;
        market.platformFeeCollected = market.platformFeeCollected + fee;

        userBets[msg.sender].push(betId);

        emit BetPlaced(betId, _submissionId, msg.sender, betAmount);
        return betId;
    }

    /**
     * @dev Get submissions for a market
     */
    function getMarketSubmissions(uint256 _marketId) external view returns (uint256[] memory) {
        return marketSubmissions[_marketId];
    }

    /**
     * @dev Get user's submissions
     */
    function getUserSubmissions(address _user) external view returns (uint256[] memory) {
        return userSubmissions[_user];
    }

    /**
     * @dev Get user's bets
     */
    function getUserBets(address _user) external view returns (uint256[] memory) {
        return userBets[_user];
    }

    /**
     * @dev Emergency withdrawal function (only owner)
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    /**
     * @dev Receive function to accept ETH
     */
    receive() external payable {}
}