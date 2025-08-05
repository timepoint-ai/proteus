// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title SecurityAudit
 * @notice Phase 14 - Security audit and emergency controls
 */
contract SecurityAudit is AccessControl, Pausable, ReentrancyGuard {
    bytes32 public constant SECURITY_ADMIN_ROLE = keccak256("SECURITY_ADMIN_ROLE");
    bytes32 public constant EMERGENCY_ROLE = keccak256("EMERGENCY_ROLE");
    
    // Security thresholds
    uint256 public maxTransactionValue = 100 ether;
    uint256 public dailyWithdrawLimit = 1000 ether;
    uint256 public suspiciousActivityThreshold = 50; // Number of rapid transactions
    
    // Rate limiting
    mapping(address => uint256) public lastActionTime;
    mapping(address => uint256) public dailyWithdrawn;
    mapping(address => uint256) public transactionCount;
    mapping(address => bool) public blacklisted;
    
    // Emergency state
    bool public emergencyMode = false;
    address public emergencyWithdrawAddress;
    
    // Audit events
    event SecurityAlert(string alertType, address indexed user, uint256 value);
    event EmergencyModeActivated(address indexed activator, string reason);
    event EmergencyModeDeactivated(address indexed deactivator);
    event UserBlacklisted(address indexed user, string reason);
    event UserWhitelisted(address indexed user);
    event SecurityThresholdUpdated(string thresholdType, uint256 oldValue, uint256 newValue);
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SECURITY_ADMIN_ROLE, msg.sender);
        _grantRole(EMERGENCY_ROLE, msg.sender);
        emergencyWithdrawAddress = msg.sender;
    }
    
    /**
     * @notice Check if transaction is within security limits
     */
    function checkTransactionSecurity(
        address user,
        uint256 value
    ) external nonReentrant returns (bool) {
        require(!blacklisted[user], "User is blacklisted");
        require(!paused(), "Contract is paused");
        require(!emergencyMode, "Emergency mode active");
        
        // Check transaction value
        if (value > maxTransactionValue) {
            emit SecurityAlert("HIGH_VALUE_TRANSACTION", user, value);
            return false;
        }
        
        // Check daily limit
        if (block.timestamp / 86400 > lastActionTime[user] / 86400) {
            // Reset daily counter
            dailyWithdrawn[user] = 0;
            transactionCount[user] = 0;
        }
        
        if (dailyWithdrawn[user] + value > dailyWithdrawLimit) {
            emit SecurityAlert("DAILY_LIMIT_EXCEEDED", user, value);
            return false;
        }
        
        // Check for rapid transactions
        transactionCount[user]++;
        if (transactionCount[user] > suspiciousActivityThreshold) {
            emit SecurityAlert("SUSPICIOUS_ACTIVITY", user, transactionCount[user]);
            blacklisted[user] = true;
            return false;
        }
        
        // Update state
        lastActionTime[user] = block.timestamp;
        dailyWithdrawn[user] += value;
        
        return true;
    }
    
    /**
     * @notice Activate emergency mode
     */
    function activateEmergencyMode(string memory reason) 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        emergencyMode = true;
        _pause();
        emit EmergencyModeActivated(msg.sender, reason);
    }
    
    /**
     * @notice Deactivate emergency mode
     */
    function deactivateEmergencyMode() 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        emergencyMode = false;
        _unpause();
        emit EmergencyModeDeactivated(msg.sender);
    }
    
    /**
     * @notice Emergency withdraw function
     */
    function emergencyWithdraw() 
        external 
        onlyRole(EMERGENCY_ROLE) 
    {
        require(emergencyMode, "Not in emergency mode");
        uint256 balance = address(this).balance;
        (bool success, ) = emergencyWithdrawAddress.call{value: balance}("");
        require(success, "Emergency withdraw failed");
    }
    
    /**
     * @notice Blacklist a user
     */
    function blacklistUser(address user, string memory reason) 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        blacklisted[user] = true;
        emit UserBlacklisted(user, reason);
    }
    
    /**
     * @notice Whitelist a user
     */
    function whitelistUser(address user) 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        blacklisted[user] = false;
        transactionCount[user] = 0;
        emit UserWhitelisted(user);
    }
    
    /**
     * @notice Update security thresholds
     */
    function updateMaxTransactionValue(uint256 newValue) 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        uint256 oldValue = maxTransactionValue;
        maxTransactionValue = newValue;
        emit SecurityThresholdUpdated("MAX_TRANSACTION", oldValue, newValue);
    }
    
    function updateDailyWithdrawLimit(uint256 newValue) 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        uint256 oldValue = dailyWithdrawLimit;
        dailyWithdrawLimit = newValue;
        emit SecurityThresholdUpdated("DAILY_LIMIT", oldValue, newValue);
    }
    
    function updateSuspiciousActivityThreshold(uint256 newValue) 
        external 
        onlyRole(SECURITY_ADMIN_ROLE) 
    {
        uint256 oldValue = suspiciousActivityThreshold;
        suspiciousActivityThreshold = newValue;
        emit SecurityThresholdUpdated("SUSPICIOUS_THRESHOLD", oldValue, newValue);
    }
    
    /**
     * @notice Check if user is allowed to transact
     */
    function isUserAllowed(address user) external view returns (bool) {
        return !blacklisted[user] && !paused() && !emergencyMode;
    }
    
    /**
     * @notice Get user security status
     */
    function getUserSecurityStatus(address user) external view returns (
        bool isBlacklisted,
        uint256 dailyWithdrawAmount,
        uint256 transactionCountToday,
        uint256 lastAction
    ) {
        return (
            blacklisted[user],
            dailyWithdrawn[user],
            transactionCount[user],
            lastActionTime[user]
        );
    }
    
    /**
     * @notice Pause contract operations
     */
    function pause() external onlyRole(SECURITY_ADMIN_ROLE) {
        _pause();
    }
    
    /**
     * @notice Unpause contract operations
     */
    function unpause() external onlyRole(SECURITY_ADMIN_ROLE) {
        _unpause();
    }
}