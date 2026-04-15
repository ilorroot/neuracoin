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

    // ── Constructor ──────────────────────────────────────────────────────────

    constructor(address _nrc, address _treasury, address _disputeResolver) {
        require(_nrc != address(0), "Invalid NRC address");
        require(_treasury != address(0), "Invalid treasury address");
        require(_disputeResolver != address(0), "Invalid dispute resolver address");
        
        nrc = NeuraCoin(_nrc);
        treasury = _treasury;
        disputeResolver = _disputeResolver;
        nextJobId = 1;
    }

    // ── Provider Management ──────────────────────────────────────────────────

    /**
     * @notice Register as a GPU provider with minimum stake
     * @param _stake Amount of NRC to stake (must be >= MIN_PROVIDER_STAKE)
     */
    function registerProvider(uint256 _stake) external nonReentrant {
        require(_stake >= MIN_PROVIDER_STAKE, "Insufficient stake");
        require(!registeredProviders[msg.sender], "Already registered");
        
        require(nrc.transferFrom(msg.sender, address(this), _stake), "Transfer failed");
        
        registeredProviders[msg.sender] = true;
        providerStakes[msg.sender] = _stake;
        
        emit ProviderRegistered(msg.sender, _stake);
    }

    /**
     * @notice Unregister as a provider and recover stake
     */
    function unregisterProvider() external nonReentrant {
        require(registeredProviders[msg.sender], "Not registered");
        
        uint256 stake = providerStakes[msg.sender];
        registeredProviders[msg.sender] = false;
        providerStakes[msg.sender] = 0;
        
        require(nrc.transfer(msg.sender, stake), "Transfer failed");
        
        emit ProviderUnregistered(msg.sender);
    }

    // ── Job Lifecycle ────────────────────────────────────────────────────────

    /**
     * @notice Submit a new job for computation
     * @param _specHash IPFS hash of job specification
     * @param _reward NRC reward for completing the job
     */
    function submitJob(bytes32 _specHash, uint256 _reward) external nonReentrant returns (uint256) {
        require(_specHash != bytes32(0), "Invalid spec hash");
        require(_reward > 0, "Invalid reward");
        
        uint256 totalStake = _reward + (_reward * PROTOCOL_FEE_BPS) / 10000;
        require(nrc.transferFrom(msg.sender, address(this), totalStake), "Transfer failed");
        
        uint256 jobId = nextJobId++;
        jobs[jobId] = Job({
            id: jobId,
            requester: msg.sender,
            provider: address(0),
            stake: totalStake,
            reward: _reward,
            specHash: _specHash,
            outputHash: bytes32(0),
            status: JobStatus.Open,
            createdAt: block.timestamp,
            completedAt: 0
        });
        
        openJobIds.push(jobId);
        emit JobSubmitted(jobId, msg.sender, totalStake);
        
        return jobId;
    }

    /**
     * @notice Assign a job to a provider
     * @param _jobId ID of the job to assign
     * @param _provider Address of the provider
     */
    function assignJob(uint256 _jobId, address _provider) external onlyOwner {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.Open, "Job not open");
        require(registeredProviders[_provider], "Provider not registered");
        
        job.provider = _provider;
        job.status = JobStatus.Assigned;
        
        emit JobAssigned(_jobId, _provider);
    }

    /**
     * @notice Complete a job with output hash
     * @param _jobId ID of the job
     * @param _outputHash Hash of the job output
     */
    function completeJob(uint256 _jobId, bytes32 _outputHash) external nonReentrant {
        Job storage job = jobs[_jobId];
        require(job.status == JobStatus.Assigned, "Job not assigned");
        require(msg.sender == job.provider, "Only provider can complete");
        require(_outputHash != bytes32(0), "Invalid output hash");
        
        job.outputHash = _outputHash;
        job.completedAt = block.timestamp;
        job.status = JobStatus.