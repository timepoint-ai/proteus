// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./PredictionMarket.sol";

/**
 * @title ClockchainOracle
 * @notice Legacy contract name. Part of the Proteus protocol (formerly Clockchain).
 * @dev Oracle contract for X.com post verification and market resolution
 */
contract ClockchainOracle is AccessControl, ReentrancyGuard {
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    PredictionMarket public predictionMarket;
    
    struct OracleSubmission {
        uint256 marketId;
        address oracle;
        string actualText;
        string tweetId;
        string screenshotBase64;
        uint256 timestamp;
        uint256 votesFor;
        uint256 votesAgainst;
        bool verified;
        mapping(address => bool) hasVoted;
    }
    
    struct MarketResolution {
        uint256 marketId;
        uint256 winningSubmissionId;
        uint256[] levenshteinDistances;
        bool resolved;
        uint256 timestamp;
    }
    
    uint256 public submissionCount;
    uint256 public minimumOracles = 3;
    uint256 public consensusThreshold = 66; // 66% required for consensus
    uint256 public submissionWindow = 7200; // 2 hours after market ends
    
    mapping(uint256 => OracleSubmission) public oracleSubmissions;
    mapping(uint256 => MarketResolution) public marketResolutions;
    mapping(uint256 => uint256[]) public marketOracleSubmissions;
    mapping(address => uint256) public oracleReputation;
    
    event OracleSubmissionCreated(uint256 indexed submissionId, uint256 indexed marketId, address indexed oracle);
    event OracleVoteCast(uint256 indexed submissionId, address indexed voter, bool support);
    event MarketResolved(uint256 indexed marketId, uint256 winningSubmissionId);
    event ScreenshotStored(uint256 indexed submissionId, bytes32 screenshotHash);
    
    modifier onlyOracle() {
        require(hasRole(ORACLE_ROLE, msg.sender), "Caller is not an oracle");
        _;
    }
    
    modifier onlyAdmin() {
        require(hasRole(ADMIN_ROLE, msg.sender), "Caller is not an admin");
        _;
    }
    
    constructor(address payable _predictionMarket) {
        predictionMarket = PredictionMarket(_predictionMarket);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }
    
    /**
     * @dev Submit oracle data for market resolution
     */
    function submitOracleData(
        uint256 _marketId,
        string memory _actualText,
        string memory _tweetId,
        string memory _screenshotBase64
    ) external onlyOracle returns (uint256) {
        (
            string memory question,
            address creator,
            uint256 startTime,
            uint256 endTime,
            bool resolved,
            uint256 winningSubmissionId,
            uint256 totalVolume,
            string memory actorTwitterHandle,
            string memory targetTweetId,
            bool xcomOnly,
            uint256 platformFeeCollected
        ) = predictionMarket.markets(_marketId);
        
        require(block.timestamp >= endTime, "Market has not ended yet");
        require(block.timestamp <= endTime + submissionWindow, "Oracle submission window closed");
        require(!resolved, "Market already resolved");
        require(xcomOnly, "Market requires X.com verification");
        
        uint256 submissionId = submissionCount++;
        OracleSubmission storage submission = oracleSubmissions[submissionId];
        submission.marketId = _marketId;
        submission.oracle = msg.sender;
        submission.actualText = _actualText;
        submission.tweetId = _tweetId;
        submission.screenshotBase64 = _screenshotBase64;
        submission.timestamp = block.timestamp;
        submission.votesFor = 1; // Oracle's own vote
        submission.votesAgainst = 0;
        submission.verified = false;
        submission.hasVoted[msg.sender] = true;
        
        marketOracleSubmissions[_marketId].push(submissionId);
        
        emit OracleSubmissionCreated(submissionId, _marketId, msg.sender);
        emit ScreenshotStored(submissionId, keccak256(bytes(_screenshotBase64)));
        
        return submissionId;
    }
    
    /**
     * @dev Vote on an oracle submission
     */
    function voteOnSubmission(uint256 _submissionId, bool _support) external onlyOracle {
        OracleSubmission storage submission = oracleSubmissions[_submissionId];
        require(!submission.hasVoted[msg.sender], "Already voted");
        require(!submission.verified, "Submission already verified");
        
        submission.hasVoted[msg.sender] = true;
        
        if (_support) {
            submission.votesFor++;
        } else {
            submission.votesAgainst++;
        }
        
        emit OracleVoteCast(_submissionId, msg.sender, _support);
        
        // Check if consensus reached
        uint256 totalVotes = submission.votesFor + submission.votesAgainst;
        if (totalVotes >= minimumOracles && 
            submission.votesFor * 100 / totalVotes >= consensusThreshold) {
            submission.verified = true;
            _resolveMarket(submission.marketId, _submissionId);
        }
    }
    
    /**
     * @dev Calculate Levenshtein distance between two strings
     */
    function calculateLevenshteinDistance(
        string memory _s1,
        string memory _s2
    ) public pure returns (uint256) {
        bytes memory b1 = bytes(_s1);
        bytes memory b2 = bytes(_s2);
        uint256 len1 = b1.length;
        uint256 len2 = b2.length;
        
        if (len1 == 0) return len2;
        if (len2 == 0) return len1;
        
        uint256[] memory previousRow = new uint256[](len2 + 1);
        uint256[] memory currentRow = new uint256[](len2 + 1);
        
        // Initialize first row
        for (uint256 i = 0; i <= len2; i++) {
            previousRow[i] = i;
        }
        
        for (uint256 i = 1; i <= len1; i++) {
            currentRow[0] = i;
            
            for (uint256 j = 1; j <= len2; j++) {
                uint256 cost = (b1[i - 1] == b2[j - 1]) ? 0 : 1;
                
                currentRow[j] = _min(
                    _min(currentRow[j - 1] + 1, previousRow[j] + 1),
                    previousRow[j - 1] + cost
                );
            }
            
            // Swap rows
            (previousRow, currentRow) = (currentRow, previousRow);
        }
        
        return previousRow[len2];
    }
    
    /**
     * @dev Internal function to resolve market
     */
    function _resolveMarket(uint256 _marketId, uint256 _oracleSubmissionId) internal {
        OracleSubmission storage oracleSubmission = oracleSubmissions[_oracleSubmissionId];
        
        uint256[] memory submissionIds = predictionMarket.getMarketSubmissions(_marketId);
        uint256 winningSubmissionId = 0;
        uint256 minDistance = type(uint256).max;
        
        // Calculate distances for all submissions
        for (uint256 i = 0; i < submissionIds.length; i++) {
            (
                uint256 marketId,
                address creator,
                string memory predictedText,
                uint256 stake,
                uint256 totalBets,
                uint256 levenshteinDistance,
                bool isWinner,
                string memory screenshotIpfsHash,
                bytes32 screenshotBase64Hash
            ) = predictionMarket.submissions(submissionIds[i]);
            
            uint256 distance = calculateLevenshteinDistance(predictedText, oracleSubmission.actualText);
            
            if (distance < minDistance) {
                minDistance = distance;
                winningSubmissionId = submissionIds[i];
            }
        }
        
        marketResolutions[_marketId] = MarketResolution({
            marketId: _marketId,
            winningSubmissionId: winningSubmissionId,
            levenshteinDistances: new uint256[](0),
            resolved: true,
            timestamp: block.timestamp
        });
        
        emit MarketResolved(_marketId, winningSubmissionId);
        
        // Update oracle reputation
        oracleReputation[oracleSubmission.oracle] += 10;
    }
    
    /**
     * @dev Get oracle submissions for a market
     */
    function getMarketOracleSubmissions(uint256 _marketId) external view returns (uint256[] memory) {
        return marketOracleSubmissions[_marketId];
    }
    
    /**
     * @dev Add oracle role to address
     */
    function addOracle(address _oracle) external onlyAdmin {
        grantRole(ORACLE_ROLE, _oracle);
        oracleReputation[_oracle] = 100; // Starting reputation
    }
    
    /**
     * @dev Remove oracle role from address
     */
    function removeOracle(address _oracle) external onlyAdmin {
        revokeRole(ORACLE_ROLE, _oracle);
    }
    
    /**
     * @dev Update consensus parameters
     */
    function updateConsensusParameters(
        uint256 _minimumOracles,
        uint256 _consensusThreshold,
        uint256 _submissionWindow
    ) external onlyAdmin {
        minimumOracles = _minimumOracles;
        consensusThreshold = _consensusThreshold;
        submissionWindow = _submissionWindow;
    }
    
    /**
     * @dev Min function
     */
    function _min(uint256 a, uint256 b) internal pure returns (uint256) {
        return a < b ? a : b;
    }
}