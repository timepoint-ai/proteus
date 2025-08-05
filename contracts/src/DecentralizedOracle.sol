// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

interface IEnhancedPredictionMarket {
    function getMarket(bytes32 marketId) external view returns (
        address actor,
        uint256 startTime,
        uint256 endTime,
        bool resolved,
        bytes32 winningSubmissionId,
        uint256 totalPool
    );
    
    function resolveMarket(bytes32 marketId, bytes32 winningSubmissionId) external;
}

interface INodeRegistry {
    function isActiveNode(address node) external view returns (bool);
}

contract DecentralizedOracle is ReentrancyGuard {
    using Strings for uint256;
    
    struct OracleData {
        string actualText;
        string screenshotIPFS;
        bytes32 textHash;
        uint256 levenshteinDistance;
        address[] validators;
        mapping(address => bool) hasValidated;
        bool consensusReached;
    }
    
    struct MarketOracleData {
        mapping(bytes32 => OracleData) submissions; // submissionId => OracleData
        bytes32[] submissionIds;
        uint256 totalValidations;
        bool isResolved;
    }
    
    IEnhancedPredictionMarket public predictionMarket;
    INodeRegistry public nodeRegistry;
    
    mapping(bytes32 => MarketOracleData) public marketOracles; // marketId => MarketOracleData
    
    uint256 public constant MIN_VALIDATORS = 3;
    uint256 public constant CONSENSUS_THRESHOLD = 66; // 66%
    
    event OracleDataSubmitted(
        bytes32 indexed marketId,
        bytes32 indexed submissionId,
        address indexed oracle,
        string actualText,
        string screenshotIPFS,
        uint256 levenshteinDistance
    );
    
    event ConsensusReached(
        bytes32 indexed marketId,
        bytes32 indexed submissionId,
        uint256 validatorCount
    );
    
    event MarketAutoResolved(
        bytes32 indexed marketId,
        bytes32 indexed winningSubmissionId,
        uint256 lowestDistance
    );
    
    constructor(address _predictionMarket, address _nodeRegistry) {
        predictionMarket = IEnhancedPredictionMarket(_predictionMarket);
        nodeRegistry = INodeRegistry(_nodeRegistry);
    }
    
    /**
     * @dev Submit oracle data for a specific submission
     * @param marketId The market ID
     * @param submissionId The submission ID
     * @param actualText The actual text from X.com
     * @param screenshotIPFS IPFS hash of the screenshot proof
     * @param predictedText The predicted text for this submission
     */
    function submitOracleData(
        bytes32 marketId,
        bytes32 submissionId,
        string calldata actualText,
        string calldata screenshotIPFS,
        string calldata predictedText
    ) external nonReentrant {
        require(nodeRegistry.isActiveNode(msg.sender), "Not an active oracle node");
        
        // Verify market exists and is expired but not resolved
        (,, uint256 endTime, bool resolved,,) = predictionMarket.getMarket(marketId);
        require(endTime > 0, "Market does not exist");
        require(block.timestamp > endTime, "Market not yet expired");
        require(!resolved, "Market already resolved");
        
        MarketOracleData storage marketData = marketOracles[marketId];
        OracleData storage oracleData = marketData.submissions[submissionId];
        
        // Ensure oracle hasn't already validated this submission
        require(!oracleData.hasValidated[msg.sender], "Oracle already validated this submission");
        
        // Calculate Levenshtein distance on-chain
        uint256 distance = calculateLevenshteinDistance(actualText, predictedText);
        
        // First submission for this submissionId
        if (oracleData.validators.length == 0) {
            oracleData.actualText = actualText;
            oracleData.screenshotIPFS = screenshotIPFS;
            oracleData.textHash = keccak256(abi.encodePacked(actualText));
            oracleData.levenshteinDistance = distance;
            marketData.submissionIds.push(submissionId);
        } else {
            // Verify consistency with previous submissions
            require(
                keccak256(abi.encodePacked(actualText)) == oracleData.textHash,
                "Text hash mismatch with previous submissions"
            );
            require(
                keccak256(abi.encodePacked(screenshotIPFS)) == keccak256(abi.encodePacked(oracleData.screenshotIPFS)),
                "Screenshot IPFS hash mismatch"
            );
        }
        
        // Record validation
        oracleData.validators.push(msg.sender);
        oracleData.hasValidated[msg.sender] = true;
        marketData.totalValidations++;
        
        emit OracleDataSubmitted(
            marketId,
            submissionId,
            msg.sender,
            actualText,
            screenshotIPFS,
            distance
        );
        
        // Check for consensus
        if (oracleData.validators.length >= MIN_VALIDATORS && !oracleData.consensusReached) {
            oracleData.consensusReached = true;
            emit ConsensusReached(marketId, submissionId, oracleData.validators.length);
            
            // Try to auto-resolve if all submissions have consensus
            _tryAutoResolve(marketId);
        }
    }
    
    /**
     * @dev Calculate Levenshtein distance between two strings (simplified version)
     * Note: In production, this would need optimization for gas efficiency
     */
    function calculateLevenshteinDistance(
        string memory a,
        string memory b
    ) public pure returns (uint256) {
        bytes memory bytesA = bytes(a);
        bytes memory bytesB = bytes(b);
        
        uint256 lenA = bytesA.length;
        uint256 lenB = bytesB.length;
        
        // Handle empty strings
        if (lenA == 0) return lenB;
        if (lenB == 0) return lenA;
        
        // For gas efficiency, limit string length
        require(lenA <= 280 && lenB <= 280, "Strings too long for on-chain calculation");
        
        // Create a 2D array for dynamic programming
        uint256[][] memory dp = new uint256[][](lenA + 1);
        for (uint256 i = 0; i <= lenA; i++) {
            dp[i] = new uint256[](lenB + 1);
        }
        
        // Initialize base cases
        for (uint256 i = 0; i <= lenA; i++) {
            dp[i][0] = i;
        }
        for (uint256 j = 0; j <= lenB; j++) {
            dp[0][j] = j;
        }
        
        // Fill the dp table
        for (uint256 i = 1; i <= lenA; i++) {
            for (uint256 j = 1; j <= lenB; j++) {
                uint256 cost = bytesA[i - 1] == bytesB[j - 1] ? 0 : 1;
                
                uint256 deletion = dp[i - 1][j] + 1;
                uint256 insertion = dp[i][j - 1] + 1;
                uint256 substitution = dp[i - 1][j - 1] + cost;
                
                dp[i][j] = _min(_min(deletion, insertion), substitution);
            }
        }
        
        return dp[lenA][lenB];
    }
    
    /**
     * @dev Try to automatically resolve market if conditions are met
     */
    function _tryAutoResolve(bytes32 marketId) private {
        MarketOracleData storage marketData = marketOracles[marketId];
        
        if (marketData.isResolved) return;
        
        // Check if we have enough consensus on submissions
        uint256 lowestDistance = type(uint256).max;
        bytes32 winningSubmissionId;
        bool canResolve = true;
        
        for (uint256 i = 0; i < marketData.submissionIds.length; i++) {
            bytes32 submissionId = marketData.submissionIds[i];
            OracleData storage oracleData = marketData.submissions[submissionId];
            
            // All submissions need consensus
            if (!oracleData.consensusReached) {
                canResolve = false;
                break;
            }
            
            // Track submission with lowest Levenshtein distance
            if (oracleData.levenshteinDistance < lowestDistance) {
                lowestDistance = oracleData.levenshteinDistance;
                winningSubmissionId = submissionId;
            }
        }
        
        // Auto-resolve if all submissions have consensus
        if (canResolve && marketData.submissionIds.length > 0) {
            marketData.isResolved = true;
            predictionMarket.resolveMarket(marketId, winningSubmissionId);
            
            emit MarketAutoResolved(marketId, winningSubmissionId, lowestDistance);
        }
    }
    
    /**
     * @dev Get oracle data for a submission
     */
    function getOracleData(
        bytes32 marketId,
        bytes32 submissionId
    ) external view returns (
        string memory actualText,
        string memory screenshotIPFS,
        uint256 levenshteinDistance,
        uint256 validatorCount,
        bool consensusReached
    ) {
        OracleData storage data = marketOracles[marketId].submissions[submissionId];
        return (
            data.actualText,
            data.screenshotIPFS,
            data.levenshteinDistance,
            data.validators.length,
            data.consensusReached
        );
    }
    
    /**
     * @dev Check if an oracle has validated a submission
     */
    function hasOracleValidated(
        bytes32 marketId,
        bytes32 submissionId,
        address oracle
    ) external view returns (bool) {
        return marketOracles[marketId].submissions[submissionId].hasValidated[oracle];
    }
    
    /**
     * @dev Helper function to find minimum of two numbers
     */
    function _min(uint256 a, uint256 b) private pure returns (uint256) {
        return a < b ? a : b;
    }
}