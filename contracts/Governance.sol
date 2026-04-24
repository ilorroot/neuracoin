```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

interface INRCToken is IERC20 {
    function totalSupply() external view returns (uint256);
}

contract NuraGovernance is Ownable, ReentrancyGuard {
    // ============ State Variables ============
    
    INRCToken public nrcToken;
    
    uint256 public proposalCount;
    uint256 public votingPeriod = 3 days;
    uint256 public proposalThreshold = 1000e18; // 1000 NRC tokens to create proposal
    
    enum ProposalState {
        Pending,
        Active,
        Canceled,
        Defeated,
        Succeeded,
        Queued,
        Expired,
        Executed
    }
    
    struct Proposal {
        uint256 id;
        address proposer;
        string title;
        string description;
        uint256 startBlock;
        uint256 endBlock;
        uint256 forVotes;
        uint256 againstVotes;
        uint256 abstainVotes;
        bool canceled;
        bool executed;
        mapping(address => Receipt) receipts;
    }
    
    struct Receipt {
        bool hasVoted;
        uint8 support; // 0 = against, 1 = for, 2 = abstain
        uint96 votes;
    }
    
    mapping(uint256 => Proposal) public proposals;
    mapping(address => uint256) public latestProposalIds;
    
    // ============ Events ============
    
    event ProposalCreated(
        uint256 id,
        address indexed proposer,
        string title,
        string description,
        uint256 startBlock,
        uint256 endBlock
    );
    
    event VoteCast(
        address indexed voter,
        uint256 proposalId,
        uint8 support,
        uint96 votes,
        string reason
    );
    
    event ProposalCanceled(uint256 id);
    event ProposalQueued(uint256 id);
    event ProposalExecuted(uint256 id);
    
    // ============ Constructor ============
    
    constructor(address _nrcToken) {
        require(_nrcToken != address(0), "Invalid token address");
        nrcToken = INRCToken(_nrcToken);
    }
    
    // ============ Core Functions ============
    
    function createProposal(
        string calldata title,
        string calldata description
    ) external returns (uint256) {
        require(
            nrcToken.balanceOf(msg.sender) > proposalThreshold,
            "Insufficient balance to propose"
        );
        
        uint256 startBlock = block.number + 1;
        uint256 endBlock = startBlock + ((votingPeriod / 12) + 1); // ~12s per block
        
        uint256 proposalId = proposalCount++;
        Proposal storage newProposal = proposals[proposalId];
        
        newProposal.id = proposalId;
        newProposal.proposer = msg.sender;
        newProposal.title = title;
        newProposal.description = description;
        newProposal.startBlock = startBlock;
        newProposal.endBlock = endBlock;
        
        latestProposalIds[msg.sender] = proposalId;
        
        emit ProposalCreated(proposalId, msg.sender, title, description, startBlock, endBlock);
        
        return proposalId;
    }
    
    function castVote(
        uint256 proposalId,
        uint8 support,
        string calldata reason
    ) external nonReentrant {
        require(proposalId < proposalCount, "Invalid proposal");
        require(support <= 2, "Invalid vote type");
        
        Proposal storage proposal = proposals[proposalId];
        require(block.number <= proposal.endBlock, "Voting closed");
        require(block.number >= proposal.startBlock, "Voting not started");
        require(!proposal.canceled, "Proposal canceled");
        
        Receipt storage receipt = proposal.receipts[msg.sender];
        require(!receipt.hasVoted, "Already voted");
        
        uint96 votes = uint96(nrcToken.balanceOf(msg.sender));
        require(votes > 0, "No voting power");
        
        if (support == 0) {
            proposal.againstVotes += votes;
        } else if (support == 1) {
            proposal.forVotes += votes;
        } else {
            proposal.abstainVotes += votes;
        }
        
        receipt.hasVoted = true;
        receipt.support = support;
        receipt.votes = votes;
        
        emit VoteCast(msg.sender, proposalId, support, votes, reason);
    }
    
    function cancelProposal(uint256 proposalId) external {
        require(proposalId < proposalCount, "Invalid proposal");
        Proposal storage proposal = proposals[proposalId];
        require(msg.sender == proposal.proposer || msg.sender == owner(), "Unauthorized");
        require(!proposal.executed, "Already executed");
        
        proposal.canceled = true;
        emit ProposalCanceled(proposalId);
    }
    
    function queueProposal(uint256 proposalId) external onlyOwner {
        require(proposalId < proposalCount, "Invalid proposal");
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.canceled, "Proposal canceled");
        require(block.number > proposal.endBlock, "Voting in progress");
        require(proposal.forVotes > proposal.againstVotes, "Proposal rejected");
        
        emit ProposalQueued(proposalId);
    }
    
    function executeProposal(uint256 proposalId) external onlyOwner {
        require(proposalId < proposalCount, "Invalid proposal");
        Proposal storage proposal = proposals[proposalId];
        require(!proposal.executed, "Already executed");
        require(proposal.forVotes > proposal.againstVotes, "Cannot execute");
        
        proposal.executed = true;
        emit ProposalExecuted(proposalId);
    }
    
    // ============ View Functions ============
    
    function getProposal(uint256 proposalId)
        external
        view
        returns (
            address proposer,
            string memory title,
            string memory description,
            uint256 startBlock,
            uint256 endBlock,
            uint256 forVotes,
            uint256 againstVotes,
            uint256 abstainVotes,
            bool canceled,
            bool executed
        )
    {
        require(proposalId < proposalCount, "Invalid proposal");
        Proposal storage proposal = proposals[proposalId];
        
        return (
            proposal.proposer,
            proposal.title,
            proposal.description,
            proposal.startBlock,
            proposal.endBlock,
            proposal.forVotes,
            proposal.againstVotes,
            proposal.abstainVotes,
            proposal.canceled,
            proposal.executed
        );
    }
    
    function getProposalState(uint256 proposalId) external view returns (ProposalState) {
        require(proposalId < proposalCount, "Invalid proposal");
        Proposal storage proposal = proposals[proposalId];
        
        if (proposal.canceled) {
            return ProposalState.Canceled;
        } else if (block.number <= proposal.startBlock) {
            return ProposalState.Pending;
        } else if (block.number <= proposal.endBlock) {
            return ProposalState.Active;
        } else if (