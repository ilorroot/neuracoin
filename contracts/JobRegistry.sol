// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./NeuraCoin.sol";

/**
 * @title JobRegistry
 * @notice Manages the lifecycle of AI compute jobs on the NeuraCoin protocol.
 *         Handles job submission, provider matching, escrow, settlement, and disputes.
 */
contract JobRegistry is Ownable, ReentrancyGuard {

    // ── Types ─────────────────────────────────────────────────────────────────

    enum JobStatus { Open, Assigned, Completed, Disputed, Cancelled, Resolved }

    enum DisputeResolution { Pending, RequesterWon, ProviderWon }

    struct Job {
        uint256 id;
        address requester;
        address provider;
        uint256 stake;          // NRC locked in escrow
        uint256 reward;         // NRC reward for provider
        bytes32 specHash;       // IPFS hash of job specification
        bytes32 outputHash;     // Provider-submitted output hash
        JobStatus status;
        uint256 createdAt;
        uint256 completedAt;
    }

    struct Dispute {
        uint256 jobId;
        address disputer;
        string reason;
        uint256 createdAt;
        DisputeResolution resolution;
        uint256 resolvedAt;
        address resolver;
    }

    // ── Constants ─────────────────────────────────────────────────────────────

    uint256 public constant PROTOCOL_FEE_BPS = 10;      // 0.1% in basis points
    uint256 public constant MIN_PROVIDER_STAKE = 1_000 * 10 ** 18;  // 1,000 NRC
    uint256 public constant JOB_TIMEOUT = 24 hours;
    uint256 public constant DISPUTE_WINDOW = 7 days;    // Time to flag a job after completion
    uint256 public constant DISPUTE_RESOLUTION_TIME = 3 days;

    // ── State ─────────────────────────────────────────────────────────────────

    NeuraCoin public immutable nrc;
    address public treasury;
    address public disputeResolver;

    uint256 public nextJobId;
    mapping(uint256 => Job) public jobs;
    mapping(uint256 => Dispute) public disputes;
    mapping(address => uint256) public providerStakes;
    mapping(address => bool) public registeredProviders;
    mapping(uint256 => bool) public jobDisputed;
    uint256[] private openJobIds;

    // ── Events ────────────────────────────────────────────────────────────────

    event JobSubmitted(uint256 indexed jobId, address indexed requester, uint256 stake);
    event JobAssigned(uint256 indexed jobId, address indexed provider);
    event JobCompleted(uint256 indexed jobId, bytes32 outputHash);
    event JobCancelled(uint256 indexed jobId);
    event DisputeFlagged(uint256 indexed jobId, address indexed disputer, string reason);
    event DisputeResolved(uint256 indexed jobId, DisputeResolution resolution, address resolver);
    event ProviderRegistered(address indexed provider, uint256 stake);
    event ProviderUnregistered(address indexed provider);

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor(address _nrc, address _treasury, address _disputeResolver) {
        require(_nrc != address(0), "Invalid NRC address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_disputeResolver != address(0), "Invalid dispute resolver address");
        
        nrc = NeuraCoin(_nrc);
        treasury = _treasury;
        disputeResolver = _disputeResolver;
        nextJobId = 1;
    }

    // ── Provider Management ────────────────────────────────────────────────────

    function registerProvider(uint256 stakeAmount) external nonReentrant {
        require(stakeAmount >= MIN_PROVIDER_STAKE, "Stake below minimum");
        require(!registeredProviders[msg.sender], "Already registered");
        
        require(nrc.transferFrom(msg.sender, address(this), stakeAmount), "Stake transfer failed");
        
        registeredProviders[msg.sender] = true;
        providerStakes[msg.sender] = stakeAmount;
        
        emit ProviderRegistered(msg.sender, stakeAmount);
    }

    function unregisterProvider() external nonReentrant {
        require(registeredProviders[msg.sender], "Not registered");
        
        uint256 stake = providerStakes[msg.sender];
        registeredProviders[msg.sender] = false;
        providerStakes[msg.sender] = 0;
        
        require(nrc.transfer(msg.sender, stake), "Stake withdrawal failed");
        
        emit ProviderUnregistered(msg.sender);
    }

    // ── Job Submission & Assignment ────────────────────────────────────────────

    function submitJob(uint256 stakeAmount, bytes32 specHash) 
        external 
        nonReentrant 
        returns (uint256) 
    {
        require(stakeAmount > 0, "Invalid stake");
        require(specHash != bytes32(0), "Invalid spec hash");
        
        require(nrc.transferFrom(msg.sender, address(this), stakeAmount), "Transfer failed");
        
        uint256 jobId = nextJobId++;
        Job storage job = jobs[jobId];
        
        job.id = jobId;
        job.requester = msg.sender;
        job.stake = stakeAmount;
        job.specHash = specHash;
        job.status = JobStatus.Open;
        job.createdAt = block.timestamp;
        
        openJobIds.push(jobId);
        
        emit JobSubmitted(jobId, msg.sender, stakeAmount);
        return jobId;
    }

    function assignJob(uint256 jobId, address provider, uint256 reward) 
        external 
        onlyOwner 
    {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Open, "Job not open");
        require(registeredProviders[provider], "Provider not registered");
        require(reward > 0, "Invalid reward");
        
        job.provider = provider;
        job.reward = reward;
        job.status = JobStatus.Assigned;
        
        emit JobAssigned(jobId, provider);
    }

    // ── Job Completion ────────────────────────────────────────────────────────

    function submitJobOutput(uint256 jobId, bytes32 outputHash) 
        external 
        nonReentrant 
    {
        Job storage job = jobs[jobId];
        require(msg.sender == job.provider, "Only provider can submit");
        require(job.status == JobStatus.Assigned, "Job not assigned");
        require(outputHash != bytes32(0), "Invalid output hash");
        
        job.outputHash = outputHash;
        job.status = JobStatus.Completed;
        job.completedAt = block.timestamp;
        
        emit JobCompleted(jobId, outputHash);
    }

    // ── Dispute Mechanism ──────────────────────────────────────────────────────

    /**
     * @notice Flag a completed job for dispute
     * @param jobId The ID of the job to dispute
     * @param reason The reason for the dispute (stored on-chain, max 256 chars)
     */
    function flagDispute(uint256 jobId, string calldata reason) 
        external 
        nonReentrant 
    {
        Job storage job = jobs[jobId];
        require(msg.sender == job.requester, "Only requester can flag dispute");
        require(