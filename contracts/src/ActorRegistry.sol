// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./NodeRegistry.sol";

/**
 * @title ActorRegistry
 * @dev On-chain registry for X.com actors with decentralized approval mechanism
 * Phase 9 Implementation: Move all actor data to blockchain
 */
contract ActorRegistry is AccessControl, ReentrancyGuard {
    bytes32 public constant PROPOSER_ROLE = keccak256("PROPOSER_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    NodeRegistry public nodeRegistry;
    
    struct Actor {
        string xUsername;          // e.g., "elonmusk"
        string displayName;        // e.g., "Elon Musk"
        string bio;               // Profile description
        string profileImageUrl;   // Profile image URL
        bool verified;            // Blue checkmark status
        uint256 followerCount;    // Follower count
        address[] approvers;      // Node operators who approved
        uint256 approvalCount;    // Number of approvals
        bool active;              // Active status
        uint256 registrationTime; // When actor was registered
        uint256 lastSync;         // Last X.com sync timestamp
        address proposer;         // Who proposed this actor
        bool isTestAccount;       // Test account flag
    }
    
    struct ProposalVote {
        mapping(address => bool) hasVoted;
        mapping(address => bool) support;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 deadline;
        bool executed;
        string proposalType; // "ADD" or "REMOVE"
    }
    
    uint256 public constant APPROVAL_THRESHOLD = 3;    // Need 3 node approvals
    uint256 public constant VOTING_PERIOD = 86400;     // 24 hours
    uint256 public constant SYNC_COOLDOWN = 3600;      // 1 hour between syncs
    
    mapping(string => Actor) public actors;            // xUsername => Actor
    mapping(string => bool) public actorExists;        // Quick existence check
    mapping(bytes32 => ProposalVote) public proposals; // proposalId => ProposalVote
    mapping(string => bytes32) public activeProposal;  // xUsername => active proposalId
    
    string[] public actorList;                         // List of all actor usernames
    uint256 public actorCount;
    uint256 public proposalCount;
    
    event ActorProposed(string indexed xUsername, address indexed proposer, bytes32 proposalId);
    event ActorApproved(string indexed xUsername, address indexed approver);
    event ActorActivated(string indexed xUsername, uint256 approvalCount);
    event ActorDeactivated(string indexed xUsername, address indexed proposer);
    event ActorUpdated(string indexed xUsername, address indexed updater);
    event ProposalVoteCast(bytes32 indexed proposalId, address indexed voter, bool support);
    event ProposalExecuted(bytes32 indexed proposalId, bool approved);
    
    modifier onlyActiveNode() {
        require(nodeRegistry.isNode(msg.sender), "Not a registered node");
        (, , , bool active, , , , , ) = nodeRegistry.nodes(msg.sender);
        require(active, "Node is not active");
        _;
    }
    
    modifier actorActive(string memory _xUsername) {
        require(actorExists[_xUsername], "Actor does not exist");
        require(actors[_xUsername].active, "Actor is not active");
        _;
    }
    
    constructor(address _nodeRegistry) {
        nodeRegistry = NodeRegistry(_nodeRegistry);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
    }
    
    /**
     * @dev Propose a new actor for the registry
     */
    function proposeActor(
        string memory _xUsername,
        string memory _displayName,
        string memory _bio,
        string memory _profileImageUrl,
        bool _verified,
        uint256 _followerCount,
        bool _isTestAccount
    ) external onlyActiveNode returns (bytes32) {
        require(!actorExists[_xUsername], "Actor already exists");
        require(bytes(_xUsername).length > 0, "Username cannot be empty");
        require(activeProposal[_xUsername] == bytes32(0), "Active proposal exists");
        
        // Create proposal ID
        bytes32 proposalId = keccak256(abi.encodePacked(_xUsername, block.timestamp, msg.sender));
        
        // Initialize proposal
        ProposalVote storage proposal = proposals[proposalId];
        proposal.deadline = block.timestamp + VOTING_PERIOD;
        proposal.proposalType = "ADD";
        
        // Create actor entry (inactive until approved)
        Actor storage newActor = actors[_xUsername];
        newActor.xUsername = _xUsername;
        newActor.displayName = _displayName;
        newActor.bio = _bio;
        newActor.profileImageUrl = _profileImageUrl;
        newActor.verified = _verified;
        newActor.followerCount = _followerCount;
        newActor.registrationTime = block.timestamp;
        newActor.lastSync = block.timestamp;
        newActor.proposer = msg.sender;
        newActor.isTestAccount = _isTestAccount;
        newActor.active = false;
        
        // Auto-approve from proposer
        newActor.approvers.push(msg.sender);
        newActor.approvalCount = 1;
        proposal.hasVoted[msg.sender] = true;
        proposal.support[msg.sender] = true;
        proposal.votesFor = 1;
        
        actorExists[_xUsername] = true;
        activeProposal[_xUsername] = proposalId;
        
        emit ActorProposed(_xUsername, msg.sender, proposalId);
        emit ActorApproved(_xUsername, msg.sender);
        
        // Check if threshold met
        if (newActor.approvalCount >= APPROVAL_THRESHOLD) {
            _activateActor(_xUsername, proposalId);
        }
        
        return proposalId;
    }
    
    /**
     * @dev Vote on an actor proposal
     */
    function voteOnProposal(bytes32 _proposalId, bool _support) external onlyActiveNode {
        ProposalVote storage proposal = proposals[_proposalId];
        require(block.timestamp < proposal.deadline, "Voting period ended");
        require(!proposal.executed, "Proposal already executed");
        require(!proposal.hasVoted[msg.sender], "Already voted");
        
        proposal.hasVoted[msg.sender] = true;
        proposal.support[msg.sender] = _support;
        
        if (_support) {
            proposal.votesFor++;
            // For ADD proposals, track approvers
            if (keccak256(bytes(proposal.proposalType)) == keccak256(bytes("ADD"))) {
                // Find the actor this proposal is for
                for (uint i = 0; i < actorList.length; i++) {
                    if (activeProposal[actorList[i]] == _proposalId) {
                        Actor storage actor = actors[actorList[i]];
                        actor.approvers.push(msg.sender);
                        actor.approvalCount++;
                        emit ActorApproved(actorList[i], msg.sender);
                        
                        // Check if threshold met
                        if (actor.approvalCount >= APPROVAL_THRESHOLD && !actor.active) {
                            _activateActor(actorList[i], _proposalId);
                        }
                        break;
                    }
                }
            }
        } else {
            proposal.votesAgainst++;
        }
        
        emit ProposalVoteCast(_proposalId, msg.sender, _support);
    }
    
    /**
     * @dev Update actor information (requires node operator)
     */
    function updateActor(
        string memory _xUsername,
        string memory _displayName,
        string memory _bio,
        string memory _profileImageUrl,
        bool _verified,
        uint256 _followerCount
    ) external onlyActiveNode actorActive(_xUsername) {
        require(block.timestamp >= actors[_xUsername].lastSync + SYNC_COOLDOWN, "Sync cooldown active");
        
        Actor storage actor = actors[_xUsername];
        actor.displayName = _displayName;
        actor.bio = _bio;
        actor.profileImageUrl = _profileImageUrl;
        actor.verified = _verified;
        actor.followerCount = _followerCount;
        actor.lastSync = block.timestamp;
        
        emit ActorUpdated(_xUsername, msg.sender);
    }
    
    /**
     * @dev Propose to deactivate an actor
     */
    function proposeDeactivation(string memory _xUsername) external onlyActiveNode actorActive(_xUsername) returns (bytes32) {
        require(activeProposal[_xUsername] == bytes32(0), "Active proposal exists");
        
        bytes32 proposalId = keccak256(abi.encodePacked("REMOVE", _xUsername, block.timestamp, msg.sender));
        
        ProposalVote storage proposal = proposals[proposalId];
        proposal.deadline = block.timestamp + VOTING_PERIOD;
        proposal.proposalType = "REMOVE";
        proposal.hasVoted[msg.sender] = true;
        proposal.support[msg.sender] = true;
        proposal.votesFor = 1;
        
        activeProposal[_xUsername] = proposalId;
        
        emit ActorProposed(_xUsername, msg.sender, proposalId);
        emit ProposalVoteCast(proposalId, msg.sender, true);
        
        return proposalId;
    }
    
    /**
     * @dev Execute a proposal after voting period
     */
    function executeProposal(bytes32 _proposalId) external {
        ProposalVote storage proposal = proposals[_proposalId];
        require(block.timestamp >= proposal.deadline, "Voting period not ended");
        require(!proposal.executed, "Already executed");
        
        proposal.executed = true;
        
        // For REMOVE proposals, need majority
        if (keccak256(bytes(proposal.proposalType)) == keccak256(bytes("REMOVE"))) {
            if (proposal.votesFor > proposal.votesAgainst) {
                // Find and deactivate the actor
                for (uint i = 0; i < actorList.length; i++) {
                    if (activeProposal[actorList[i]] == _proposalId) {
                        _deactivateActor(actorList[i]);
                        activeProposal[actorList[i]] = bytes32(0);
                        break;
                    }
                }
            }
        }
        
        emit ProposalExecuted(_proposalId, proposal.votesFor > proposal.votesAgainst);
    }
    
    /**
     * @dev Internal function to activate an actor
     */
    function _activateActor(string memory _xUsername, bytes32 _proposalId) internal {
        Actor storage actor = actors[_xUsername];
        actor.active = true;
        actorCount++;
        actorList.push(_xUsername);
        
        // Mark proposal as executed
        proposals[_proposalId].executed = true;
        activeProposal[_xUsername] = bytes32(0);
        
        emit ActorActivated(_xUsername, actor.approvalCount);
        emit ProposalExecuted(_proposalId, true);
    }
    
    /**
     * @dev Internal function to deactivate an actor
     */
    function _deactivateActor(string memory _xUsername) internal {
        actors[_xUsername].active = false;
        actorCount--;
        
        emit ActorDeactivated(_xUsername, msg.sender);
    }
    
    /**
     * @dev Get actor details
     */
    function getActor(string memory _xUsername) external view returns (
        string memory displayName,
        string memory bio,
        bool verified,
        uint256 followerCount,
        bool active,
        uint256 approvalCount,
        uint256 registrationTime,
        bool isTestAccount
    ) {
        Actor storage actor = actors[_xUsername];
        return (
            actor.displayName,
            actor.bio,
            actor.verified,
            actor.followerCount,
            actor.active,
            actor.approvalCount,
            actor.registrationTime,
            actor.isTestAccount
        );
    }
    
    /**
     * @dev Get all active actors
     */
    function getActiveActors() external view returns (string[] memory) {
        uint256 activeCount = 0;
        for (uint i = 0; i < actorList.length; i++) {
            if (actors[actorList[i]].active) {
                activeCount++;
            }
        }
        
        string[] memory activeActors = new string[](activeCount);
        uint256 index = 0;
        for (uint i = 0; i < actorList.length; i++) {
            if (actors[actorList[i]].active) {
                activeActors[index] = actorList[i];
                index++;
            }
        }
        
        return activeActors;
    }
    
    /**
     * @dev Check if an actor exists and is active
     */
    function isActorActive(string memory _xUsername) external view returns (bool) {
        return actorExists[_xUsername] && actors[_xUsername].active;
    }
    
    /**
     * @dev Get actor approvers
     */
    function getActorApprovers(string memory _xUsername) external view returns (address[] memory) {
        return actors[_xUsername].approvers;
    }
    
    /**
     * @dev Admin function to grant proposer role
     */
    function grantProposerRole(address account) external onlyRole(ADMIN_ROLE) {
        grantRole(PROPOSER_ROLE, account);
    }
    
    /**
     * @dev Admin function to revoke proposer role
     */
    function revokeProposerRole(address account) external onlyRole(ADMIN_ROLE) {
        revokeRole(PROPOSER_ROLE, account);
    }
}