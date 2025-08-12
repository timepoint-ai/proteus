// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract MockPredictionMarket {
    struct Market {
        address creator;
        address actor;
        uint256 startTime;
        uint256 endTime;
        bool resolved;
        uint256 winningSubmissionId;
        uint256 totalVolume;
        uint256 submissionCount;
        uint256 betCount;
        uint256 platformFeePercentage;
        uint256 platformFeeCollected;
    }
    
    mapping(uint256 => Market) public markets;
    
    function setMarket(uint256 marketId, Market memory market) external {
        markets[marketId] = market;
    }
    
    function getMarketSubmissions(uint256) external pure returns (uint256[] memory) {
        uint256[] memory ids = new uint256[](3);
        ids[0] = 1;
        ids[1] = 2;
        ids[2] = 3;
        return ids;
    }
    
    function submissions(uint256) external pure returns (
        uint256 marketId,
        address creator,
        string memory predictedText,
        uint256 stake,
        uint256 totalBets,
        uint256 levenshteinDistance,
        bool isWinner,
        string memory screenshotIpfsHash,
        bytes32 screenshotBase64Hash
    ) {
        return (0, address(0), "", 0, 0, 0, false, "", bytes32(0));
    }
}

contract MockRewardPool {
    function deposit() external payable {}
}