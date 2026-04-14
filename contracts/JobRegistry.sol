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

    constructor(address _nrc, address _treasury) Ownable(msg.sender) {
        nrc                = NeuraCoin(_nrc);
        treasury           = _treasury;
        disputeResolver    = msg.sender;
    }

    // ── Provider management ───────────────────────────────────────────────────

    /**
     * @notice Register as a compute provider by staking NRC.
     */
    function registerProvider() external {
        require(!registeredProviders[msg.sender], "JobRegistry: already registered");
        require(
            nrc.transferFrom(msg.sender, address(this), MIN_PROVIDER_STAKE),
            "JobRegistry: stake transfer failed"
        );
        providerStakes[msg.sender] = MIN_PROVIDER_STAKE;
        registeredProviders[msg.sender] = true;
        emit ProviderRegistered(msg.sender, MIN_PROVIDER_STAKE);
    }

    /**
     * @notice Unregister as a compute provider and withdraw stake.
     */
    function unregisterProvider() external nonReentrant {
        require(registeredProviders[msg.sender], "JobRegistry: not registered");
        uint256 stakeAmount = providerStakes[msg.sender];
        providerStakes[msg.sender] = 0;
        registeredProviders[msg.sender] = false;
        require(nrc.transfer(msg.sender, stakeAmount), "JobRegistry: stake transfer failed");
        emit ProviderUnregistered(msg.sender);
    }

    // ── Job lifecycle ─────────────────────────────────────────────────────────

    /**
     * @notice Submit a new job for computation.
     * @param _specHash IPFS hash of job specification
     * @param _reward NRC reward offered to provider
     */
    function submitJob(bytes32 _specHash, uint256 _reward) external nonReentrant returns (uint256) {
        require(_specHash != bytes32(0), "JobRegistry: invalid spec hash");
        require(_reward > 0, "JobRegistry: reward must be positive");

        uint256 totalCost = _reward + (_reward * PROTOCOL_FEE_BPS) / 10000;
        require(
            nrc.transferFrom(msg.sender, address(this), totalCost),
            "JobRegistry: transfer failed"
        );

        uint256 jobId = nextJobId++;
        jobs[jobId] = Job({
            id: jobId,
            requester: msg.sender,
            provider: address(0),
            stake: totalCost,
            reward: _reward,
            specHash: _specHash,
            outputHash: bytes32(0),
            status: JobStatus.Open,
            createdAt: block.timestamp,
            completedAt: 0
        });

        emit JobSubmitted(jobId, msg.sender, totalCost);
        return jobId;
    }

    /**
     * @notice Assign a job to a provider.
     */
    function assignJob(uint256 _jobId, address _provider) external onlyOwner {
        Job storage job = jobs[_jobId];
        require(job.id != 0, "JobRegistry: job not found");
        require(job.status == JobStatus.Open, "JobRegistry: job not open");
        require(registeredProviders[_provider], "JobRegistry: provider not registered");

        job.provider = _provider;
        job.status = JobStatus.Assigned;
        emit JobAssigned(_jobId, _provider);
    }

    /**
     * @notice Submit job completion with output hash.
     */
    function completeJob(uint256 _jobId, bytes32 _outputHash) external nonReentrant {
        Job storage job = jobs[_jobId];
        require(job.id != 0, "JobRegistry: job not found");
        require(job.status == JobStatus.Assigned, "JobRegistry: job not assigned");
        require(msg.sender == job.provider, "JobRegistry: only provider can complete");
        require(_outputHash != bytes32(0), "JobRegistry: invalid output hash");

        job.outputHash = _outputHash;
        job.status = JobStatus.Completed;
        job.completedAt = block.timestamp;

        uint256 fee = (job.reward * PROTOCOL_FEE_BPS) / 10000;
        require(nrc.transfer(treasury, fee), "JobRegistry: fee transfer failed");
        require(nrc.transfer(job.provider, job.reward), "JobRegistry: reward transfer failed");

        emit JobCompleted(_jobId, _outputHash);