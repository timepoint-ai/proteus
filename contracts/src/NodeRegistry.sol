// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title NodeRegistry
 * @dev Decentralized node management with staking and reputation
 */
contract NodeRegistry is Ownable, ReentrancyGuard {
    struct Node {
        address operator;
        uint256 stake;
        uint256 reputation;
        bool active;
        uint256 registrationTime;
        uint256 lastActiveTime;
        string endpoint;
        uint256 totalRewards;
        uint256 slashCount;
    }
    
    struct Vote {
        mapping(address => bool) hasVoted;
        mapping(address => bool) support;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 deadline;
        bool executed;
    }
    
    uint256 public constant MINIMUM_STAKE = 100 ether; // 100 BASE tokens
    uint256 public constant VOTING_PERIOD = 86400; // 24 hours
    uint256 public constant QUORUM_PERCENTAGE = 51; // 51% required
    uint256 public constant SLASH_AMOUNT = 10 ether; // 10 BASE penalty
    uint256 public constant INACTIVITY_PERIOD = 604800; // 7 days
    
    uint256 public nodeCount;
    uint256 public activeNodeCount;
    uint256 public totalStaked;
    uint256 public voteCount;
    
    mapping(address => Node) public nodes;
    mapping(address => bool) public isNode;
    mapping(uint256 => Vote) public votes;
    mapping(address => uint256) public pendingWithdrawals;
    
    address[] public nodeList;
    
    event NodeRegistered(address indexed operator, uint256 stake);
    event NodeDeactivated(address indexed operator);
    event NodeSlashed(address indexed operator, uint256 amount);
    event VoteCreated(uint256 indexed voteId, address indexed subject);
    event VoteCast(uint256 indexed voteId, address indexed voter, bool support);
    event VoteExecuted(uint256 indexed voteId, bool approved);
    event RewardDistributed(address indexed node, uint256 amount);
    event StakeWithdrawn(address indexed operator, uint256 amount);
    
    modifier onlyActiveNode() {
        require(isNode[msg.sender] && nodes[msg.sender].active, "Not an active node");
        _;
    }
    
    modifier nodeExists(address _operator) {
        require(isNode[_operator], "Node does not exist");
        _;
    }
    
    constructor() Ownable(msg.sender) {
        // Initialize
    }
    
    /**
     * @dev Register as a node operator
     */
    function registerNode(string memory _endpoint) external payable nonReentrant {
        require(!isNode[msg.sender], "Already registered");
        require(msg.value >= MINIMUM_STAKE, "Insufficient stake");
        require(bytes(_endpoint).length > 0, "Endpoint required");
        
        nodes[msg.sender] = Node({
            operator: msg.sender,
            stake: msg.value,
            reputation: 100,
            active: false, // Requires vote to activate
            registrationTime: block.timestamp,
            lastActiveTime: block.timestamp,
            endpoint: _endpoint,
            totalRewards: 0,
            slashCount: 0
        });
        
        isNode[msg.sender] = true;
        nodeList.push(msg.sender);
        nodeCount++;
        totalStaked += msg.value;
        
        // Create activation vote
        _createNodeVote(msg.sender, true);
        
        emit NodeRegistered(msg.sender, msg.value);
    }
    
    /**
     * @dev Update node endpoint
     */
    function updateEndpoint(string memory _endpoint) external onlyActiveNode {
        nodes[msg.sender].endpoint = _endpoint;
    }
    
    /**
     * @dev Update node activity timestamp
     */
    function heartbeat() external onlyActiveNode {
        nodes[msg.sender].lastActiveTime = block.timestamp;
    }
    
    /**
     * @dev Create a vote for node activation/deactivation
     */
    function _createNodeVote(address _nodeAddress, bool _activation) internal {
        uint256 voteId = voteCount++;
        Vote storage vote = votes[voteId];
        vote.deadline = block.timestamp + VOTING_PERIOD;
        vote.executed = false;
        
        emit VoteCreated(voteId, _nodeAddress);
    }
    
    /**
     * @dev Cast vote on node activation/deactivation
     */
    function castVote(uint256 _voteId, bool _support) external onlyActiveNode {
        Vote storage vote = votes[_voteId];
        require(block.timestamp < vote.deadline, "Voting period ended");
        require(!vote.hasVoted[msg.sender], "Already voted");
        require(!vote.executed, "Vote already executed");
        
        vote.hasVoted[msg.sender] = true;
        vote.support[msg.sender] = _support;
        
        if (_support) {
            vote.votesFor++;
        } else {
            vote.votesAgainst++;
        }
        
        emit VoteCast(_voteId, msg.sender, _support);
        
        // Auto-execute if quorum reached
        uint256 totalVotes = vote.votesFor + vote.votesAgainst;
        if (totalVotes >= (activeNodeCount * QUORUM_PERCENTAGE / 100)) {
            _executeVote(_voteId);
        }
    }
    
    /**
     * @dev Execute vote if conditions met
     */
    function executeVote(uint256 _voteId) external {
        Vote storage vote = votes[_voteId];
        require(block.timestamp >= vote.deadline, "Voting period not ended");
        require(!vote.executed, "Vote already executed");
        
        _executeVote(_voteId);
    }
    
    /**
     * @dev Internal vote execution
     */
    function _executeVote(uint256 _voteId) internal {
        Vote storage vote = votes[_voteId];
        vote.executed = true;
        
        uint256 totalVotes = vote.votesFor + vote.votesAgainst;
        bool approved = vote.votesFor > vote.votesAgainst;
        
        emit VoteExecuted(_voteId, approved);
        
        // Handle vote result (would need additional storage to track vote purposes)
    }
    
    /**
     * @dev Slash inactive or malicious node
     */
    function slashNode(address _operator) external onlyOwner nodeExists(_operator) {
        Node storage node = nodes[_operator];
        require(node.stake >= SLASH_AMOUNT, "Insufficient stake to slash");
        
        node.stake -= SLASH_AMOUNT;
        node.slashCount++;
        node.reputation = node.reputation > 10 ? node.reputation - 10 : 0;
        
        if (node.stake < MINIMUM_STAKE) {
            _deactivateNode(_operator);
        }
        
        emit NodeSlashed(_operator, SLASH_AMOUNT);
    }
    
    /**
     * @dev Deactivate node
     */
    function _deactivateNode(address _operator) internal {
        Node storage node = nodes[_operator];
        node.active = false;
        activeNodeCount--;
        pendingWithdrawals[_operator] += node.stake;
        totalStaked -= node.stake;
        node.stake = 0;
        
        emit NodeDeactivated(_operator);
    }
    
    /**
     * @dev Distribute rewards to nodes
     */
    function distributeRewards() external payable onlyOwner {
        require(activeNodeCount > 0, "No active nodes");
        uint256 rewardPerNode = msg.value / activeNodeCount;
        
        for (uint256 i = 0; i < nodeList.length; i++) {
            address nodeAddress = nodeList[i];
            if (nodes[nodeAddress].active) {
                nodes[nodeAddress].totalRewards += rewardPerNode;
                pendingWithdrawals[nodeAddress] += rewardPerNode;
                emit RewardDistributed(nodeAddress, rewardPerNode);
            }
        }
    }
    
    /**
     * @dev Withdraw pending rewards and stake
     */
    function withdraw() external nonReentrant {
        uint256 amount = pendingWithdrawals[msg.sender];
        require(amount > 0, "Nothing to withdraw");
        
        pendingWithdrawals[msg.sender] = 0;
        payable(msg.sender).transfer(amount);
        
        emit StakeWithdrawn(msg.sender, amount);
    }
    
    /**
     * @dev Check for inactive nodes
     */
    function checkInactiveNodes() external {
        for (uint256 i = 0; i < nodeList.length; i++) {
            address nodeAddress = nodeList[i];
            Node storage node = nodes[nodeAddress];
            
            if (node.active && 
                block.timestamp > node.lastActiveTime + INACTIVITY_PERIOD) {
                _deactivateNode(nodeAddress);
            }
        }
    }
    
    /**
     * @dev Get all active nodes
     */
    function getActiveNodes() external view returns (address[] memory) {
        address[] memory activeNodes = new address[](activeNodeCount);
        uint256 index = 0;
        
        for (uint256 i = 0; i < nodeList.length; i++) {
            if (nodes[nodeList[i]].active) {
                activeNodes[index++] = nodeList[i];
            }
        }
        
        return activeNodes;
    }
    
    /**
     * @dev Get node details
     */
    function getNodeDetails(address _operator) external view returns (
        uint256 stake,
        uint256 reputation,
        bool active,
        string memory endpoint,
        uint256 totalRewards
    ) {
        Node storage node = nodes[_operator];
        return (
            node.stake,
            node.reputation,
            node.active,
            node.endpoint,
            node.totalRewards
        );
    }
}