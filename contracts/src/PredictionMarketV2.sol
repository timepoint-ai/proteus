// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title PredictionMarketV2
 * @notice Prediction market contract with full resolution mechanism
 * @dev Fixes the critical blocker in V1 which had no resolution or payout logic
 *
 * Key features:
 * - Complete market lifecycle: create -> submit -> resolve -> claim
 * - On-chain Levenshtein distance for winner determination
 * - Pull-based fee collection (prevents griefing)
 * - Minimum 2 submissions required (single submission auto-refunds)
 * - 1-hour betting cutoff before market end
 * - First-submitter wins ties (deterministic, documented)
 */
contract PredictionMarketV2 is Ownable, Pausable, ReentrancyGuard {

    // ============ Structs ============

    struct Market {
        string actorHandle;        // Social media handle being predicted
        uint256 endTime;           // When betting closes
        uint256 totalPool;         // Total ETH in this market
        bool resolved;             // Has winner been determined
        uint256 winningSubmissionId; // ID of winning submission (0 if unresolved)
        address creator;           // Who created this market
    }

    struct Submission {
        uint256 marketId;          // Which market this belongs to
        address submitter;         // Who submitted this prediction
        string predictedText;      // The predicted text
        uint256 amount;            // ETH staked on this prediction
        bool claimed;              // Has payout been claimed
    }

    // ============ State Variables ============

    uint256 public marketCount;
    uint256 public submissionCount;

    mapping(uint256 => Market) public markets;
    mapping(uint256 => Submission) public submissions;
    mapping(uint256 => uint256[]) public marketSubmissions;  // marketId => submissionIds
    mapping(address => uint256[]) public userSubmissions;    // user => submissionIds
    mapping(address => uint256) public pendingFees;          // Pull-based fee collection

    // ============ Constants ============

    uint256 public constant PLATFORM_FEE_BPS = 700;  // 7% fee
    uint256 public constant MIN_BET = 0.001 ether;
    uint256 public constant BETTING_CUTOFF = 1 hours;
    uint256 public constant MIN_SUBMISSIONS = 2;     // Minimum for valid resolution
    uint256 public constant MAX_TEXT_LENGTH = 280;   // Tweet-length limit for gas efficiency

    address public feeRecipient;

    // ============ Events ============

    event MarketCreated(
        uint256 indexed marketId,
        string actorHandle,
        uint256 endTime,
        address creator
    );

    event SubmissionCreated(
        uint256 indexed submissionId,
        uint256 indexed marketId,
        address submitter,
        string predictedText,
        uint256 amount
    );

    event MarketResolved(
        uint256 indexed marketId,
        uint256 winningSubmissionId,
        string actualText,
        uint256 winningDistance
    );

    event PayoutClaimed(
        uint256 indexed submissionId,
        address indexed claimer,
        uint256 amount
    );

    event SingleSubmissionRefunded(
        uint256 indexed marketId,
        uint256 indexed submissionId,
        address submitter,
        uint256 amount
    );

    event FeesWithdrawn(
        address indexed recipient,
        uint256 amount
    );

    // ============ Errors ============

    error MarketNotFound();
    error MarketAlreadyResolved();
    error MarketNotEnded();
    error MarketEnded();
    error BettingCutoffPassed();
    error InsufficientBet();
    error SubmissionNotFound();
    error NotWinningSubmission();
    error AlreadyClaimed();
    error TransferFailed();
    error NoFeesToWithdraw();
    error InvalidDuration();
    error EmptyPrediction();
    error PredictionTooLong();
    error MinimumSubmissionsNotMet();
    error NotSingleSubmission();
    error MarketNotEndedForRefund();

    // ============ Constructor ============

    constructor(address _feeRecipient) Ownable(msg.sender) {
        feeRecipient = _feeRecipient;
    }

    // ============ External Functions ============

    /**
     * @notice Create a new prediction market
     * @param _actorHandle Social media handle being predicted
     * @param _duration How long until market ends (in seconds)
     * @return marketId The ID of the newly created market
     */
    function createMarket(
        string calldata _actorHandle,
        uint256 _duration
    ) external whenNotPaused returns (uint256) {
        if (_duration < 1 hours || _duration > 30 days) revert InvalidDuration();

        uint256 marketId = marketCount++;

        markets[marketId] = Market({
            actorHandle: _actorHandle,
            endTime: block.timestamp + _duration,
            totalPool: 0,
            resolved: false,
            winningSubmissionId: 0,
            creator: msg.sender
        });

        emit MarketCreated(marketId, _actorHandle, block.timestamp + _duration, msg.sender);

        return marketId;
    }

    /**
     * @notice Submit a prediction and stake ETH on it
     * @param _marketId The market to submit to
     * @param _predictedText Your prediction of what the actor will say
     * @return submissionId The ID of the newly created submission
     */
    function createSubmission(
        uint256 _marketId,
        string calldata _predictedText
    ) external payable whenNotPaused nonReentrant returns (uint256) {
        Market storage market = markets[_marketId];

        if (market.endTime == 0) revert MarketNotFound();
        if (market.resolved) revert MarketAlreadyResolved();
        if (block.timestamp >= market.endTime) revert MarketEnded();
        if (block.timestamp >= market.endTime - BETTING_CUTOFF) revert BettingCutoffPassed();
        if (msg.value < MIN_BET) revert InsufficientBet();
        if (bytes(_predictedText).length == 0) revert EmptyPrediction();
        if (bytes(_predictedText).length > MAX_TEXT_LENGTH) revert PredictionTooLong();

        uint256 submissionId = submissionCount++;

        submissions[submissionId] = Submission({
            marketId: _marketId,
            submitter: msg.sender,
            predictedText: _predictedText,
            amount: msg.value,
            claimed: false
        });

        marketSubmissions[_marketId].push(submissionId);
        userSubmissions[msg.sender].push(submissionId);
        market.totalPool += msg.value;

        emit SubmissionCreated(submissionId, _marketId, msg.sender, _predictedText, msg.value);

        return submissionId;
    }

    /**
     * @notice Resolve a market by providing the actual text
     * @dev Only owner can resolve. Winner determined by Levenshtein distance.
     *      First submitter wins ties (deterministic).
     * @param _marketId The market to resolve
     * @param _actualText The actual text the actor said
     */
    function resolveMarket(
        uint256 _marketId,
        string calldata _actualText
    ) external onlyOwner {
        Market storage market = markets[_marketId];

        if (market.endTime == 0) revert MarketNotFound();
        if (market.resolved) revert MarketAlreadyResolved();
        if (block.timestamp < market.endTime) revert MarketNotEnded();

        uint256[] storage subIds = marketSubmissions[_marketId];
        if (subIds.length < MIN_SUBMISSIONS) revert MinimumSubmissionsNotMet();

        // Find submission with minimum Levenshtein distance
        // First submitter wins ties (lower submissionId)
        uint256 winningId = subIds[0];
        uint256 minDistance = levenshteinDistance(
            submissions[subIds[0]].predictedText,
            _actualText
        );

        for (uint256 i = 1; i < subIds.length; i++) {
            uint256 distance = levenshteinDistance(
                submissions[subIds[i]].predictedText,
                _actualText
            );
            // Strict less-than: first submitter wins ties
            if (distance < minDistance) {
                minDistance = distance;
                winningId = subIds[i];
            }
        }

        market.resolved = true;
        market.winningSubmissionId = winningId;

        emit MarketResolved(_marketId, winningId, _actualText, minDistance);
    }

    /**
     * @notice Claim payout for a winning submission
     * @param _submissionId The submission to claim for
     */
    function claimPayout(uint256 _submissionId) external nonReentrant {
        Submission storage submission = submissions[_submissionId];
        Market storage market = markets[submission.marketId];

        if (submission.submitter == address(0)) revert SubmissionNotFound();
        if (!market.resolved) revert MarketNotEnded();
        if (market.winningSubmissionId != _submissionId) revert NotWinningSubmission();
        if (submission.claimed) revert AlreadyClaimed();

        submission.claimed = true;

        uint256 totalPool = market.totalPool;
        uint256 fee = (totalPool * PLATFORM_FEE_BPS) / 10000;
        uint256 payout = totalPool - fee;

        // Accumulate fees for pull-based withdrawal (prevents griefing)
        pendingFees[feeRecipient] += fee;

        // Transfer payout to winner
        (bool success, ) = submission.submitter.call{value: payout}("");
        if (!success) revert TransferFailed();

        emit PayoutClaimed(_submissionId, submission.submitter, payout);
    }

    /**
     * @notice Refund the only submission when market ends with single entry
     * @dev Prevents unfair 7% fee loss when there's no competition
     * @param _marketId The market with single submission
     */
    function refundSingleSubmission(uint256 _marketId) external nonReentrant {
        Market storage market = markets[_marketId];

        if (market.endTime == 0) revert MarketNotFound();
        if (market.resolved) revert MarketAlreadyResolved();
        if (block.timestamp < market.endTime) revert MarketNotEndedForRefund();

        uint256[] storage subIds = marketSubmissions[_marketId];
        if (subIds.length != 1) revert NotSingleSubmission();

        Submission storage submission = submissions[subIds[0]];
        if (submission.claimed) revert AlreadyClaimed();

        submission.claimed = true;
        market.resolved = true;  // Mark as resolved to prevent re-entry

        // Full refund - no fee taken
        (bool success, ) = submission.submitter.call{value: submission.amount}("");
        if (!success) revert TransferFailed();

        emit SingleSubmissionRefunded(_marketId, subIds[0], submission.submitter, submission.amount);
    }

    /**
     * @notice Withdraw accumulated fees (pull-based)
     */
    function withdrawFees() external nonReentrant {
        uint256 amount = pendingFees[msg.sender];
        if (amount == 0) revert NoFeesToWithdraw();

        pendingFees[msg.sender] = 0;

        (bool success, ) = msg.sender.call{value: amount}("");
        if (!success) revert TransferFailed();

        emit FeesWithdrawn(msg.sender, amount);
    }

    // ============ View Functions ============

    /**
     * @notice Get all submission IDs for a market
     * @param _marketId The market ID
     * @return Array of submission IDs
     */
    function getMarketSubmissions(uint256 _marketId) external view returns (uint256[] memory) {
        return marketSubmissions[_marketId];
    }

    /**
     * @notice Get all submission IDs for a user
     * @param _user The user address
     * @return Array of submission IDs
     */
    function getUserSubmissions(address _user) external view returns (uint256[] memory) {
        return userSubmissions[_user];
    }

    /**
     * @notice Get full market details
     * @param _marketId The market ID
     * @return actorHandle The social media handle
     * @return endTime When the market ends
     * @return totalPool Total ETH in the market
     * @return resolved Whether market has been resolved
     * @return winningSubmissionId The winning submission (0 if unresolved)
     * @return creator Who created the market
     * @return submissionIds All submissions for this market
     */
    function getMarketDetails(uint256 _marketId) external view returns (
        string memory actorHandle,
        uint256 endTime,
        uint256 totalPool,
        bool resolved,
        uint256 winningSubmissionId,
        address creator,
        uint256[] memory submissionIds
    ) {
        Market storage market = markets[_marketId];
        return (
            market.actorHandle,
            market.endTime,
            market.totalPool,
            market.resolved,
            market.winningSubmissionId,
            market.creator,
            marketSubmissions[_marketId]
        );
    }

    /**
     * @notice Get full submission details
     * @param _submissionId The submission ID
     * @return marketId The market this belongs to
     * @return submitter Who submitted
     * @return predictedText The prediction
     * @return amount ETH staked
     * @return claimed Whether payout was claimed
     */
    function getSubmissionDetails(uint256 _submissionId) external view returns (
        uint256 marketId,
        address submitter,
        string memory predictedText,
        uint256 amount,
        bool claimed
    ) {
        Submission storage sub = submissions[_submissionId];
        return (
            sub.marketId,
            sub.submitter,
            sub.predictedText,
            sub.amount,
            sub.claimed
        );
    }

    // ============ Admin Functions ============

    /**
     * @notice Update the fee recipient address
     * @param _newRecipient New address to receive fees
     */
    function setFeeRecipient(address _newRecipient) external onlyOwner {
        feeRecipient = _newRecipient;
    }

    /**
     * @notice Pause the contract in emergency
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpause the contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Emergency withdraw for unresolved markets (admin only)
     * @dev Only callable after extended period, returns funds to submitters
     * @param _marketId The market to emergency withdraw from
     */
    function emergencyWithdraw(uint256 _marketId) external onlyOwner nonReentrant {
        Market storage market = markets[_marketId];

        if (market.endTime == 0) revert MarketNotFound();
        if (market.resolved) revert MarketAlreadyResolved();
        // Only allow emergency withdraw 7 days after market end
        if (block.timestamp < market.endTime + 7 days) revert MarketNotEnded();

        market.resolved = true;  // Mark resolved to prevent future operations

        uint256[] storage subIds = marketSubmissions[_marketId];
        for (uint256 i = 0; i < subIds.length; i++) {
            Submission storage sub = submissions[subIds[i]];
            if (!sub.claimed && sub.amount > 0) {
                sub.claimed = true;
                (bool success, ) = sub.submitter.call{value: sub.amount}("");
                // Continue even if transfer fails (user can have fallback)
                if (success) {
                    emit SingleSubmissionRefunded(_marketId, subIds[i], sub.submitter, sub.amount);
                }
            }
        }
    }

    // ============ Pure Functions ============

    /**
     * @notice Calculate Levenshtein distance between two strings
     * @dev On-chain implementation for deterministic winner selection
     *      Gas cost: O(m*n) where m, n are string lengths
     *      Recommended max length: ~100 characters each
     * @param a First string
     * @param b Second string
     * @return The edit distance between the strings
     */
    function levenshteinDistance(
        string memory a,
        string memory b
    ) public pure returns (uint256) {
        bytes memory bytesA = bytes(a);
        bytes memory bytesB = bytes(b);

        uint256 lenA = bytesA.length;
        uint256 lenB = bytesB.length;

        // Handle empty string cases
        if (lenA == 0) return lenB;
        if (lenB == 0) return lenA;

        // Create distance matrix (only need two rows for space optimization)
        uint256[] memory prevRow = new uint256[](lenB + 1);
        uint256[] memory currRow = new uint256[](lenB + 1);

        // Initialize first row
        for (uint256 j = 0; j <= lenB; j++) {
            prevRow[j] = j;
        }

        // Fill in the rest of the matrix
        for (uint256 i = 1; i <= lenA; i++) {
            currRow[0] = i;

            for (uint256 j = 1; j <= lenB; j++) {
                uint256 cost = (bytesA[i - 1] == bytesB[j - 1]) ? 0 : 1;

                // Minimum of: deletion, insertion, substitution
                uint256 deletion = prevRow[j] + 1;
                uint256 insertion = currRow[j - 1] + 1;
                uint256 substitution = prevRow[j - 1] + cost;

                currRow[j] = _min3(deletion, insertion, substitution);
            }

            // Swap rows
            (prevRow, currRow) = (currRow, prevRow);
        }

        return prevRow[lenB];
    }

    /**
     * @notice Helper to find minimum of three values
     */
    function _min3(uint256 a, uint256 b, uint256 c) internal pure returns (uint256) {
        if (a <= b && a <= c) return a;
        if (b <= a && b <= c) return b;
        return c;
    }
}
