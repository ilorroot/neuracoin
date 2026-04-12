// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "./NeuraCoin.sol";

/**
 * @title JobRegistry
 * @notice Manages the lifecycle of AI compute jobs on the NeuraCoin protocol.
 *         Handles job submission, provider matching, escrow, and settlement.
 */
contract JobRegistry is Ownable, ReentrancyGuard {

    // ── Types ─────────────────────────────────────────────────────────────────

    enum JobStatus { Open, Assigned, Completed, Disputed, Cancelled }

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

    // ── Constants ─────────────────────────────────────────────────────────────

    uint256 public constant PROTOCOL_FEE_BPS = 10;      // 0.1% in basis points
    uint256 public constant MIN_PROVIDER_STAKE = 1_000 * 10 ** 18;  // 1,000 NRC
    uint256 public constant JOB_TIMEOUT = 24 hours;

    // ── State ─────────────────────────────────────────────────────────────────

    NeuraCoin public immutable nrc;
    address public treasury;

    uint256 public nextJobId;
    mapping(uint256 => Job) public jobs;
    mapping(address => uint256) public providerStakes;
    mapping(address => bool) public registeredProviders;

    // ── Events ────────────────────────────────────────────────────────────────

    event JobSubmitted(uint256 indexed jobId, address indexed requester, uint256 stake);
    event JobAssigned(uint256 indexed jobId, address indexed provider);
    event JobCompleted(uint256 indexed jobId, bytes32 outputHash);
    event JobCancelled(uint256 indexed jobId);
    event ProviderRegistered(address indexed provider, uint256 stake);
    event ProviderUnregistered(address indexed provider);

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor(address _nrc, address _treasury) Ownable(msg.sender) {
        nrc      = NeuraCoin(_nrc);
        treasury = _treasury;
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
     * @notice Unregister and withdraw stake (only if no active jobs).
     */
    function unregisterProvider() external {
        require(registeredProviders[msg.sender], "JobRegistry: not registered");
        uint256 stake = providerStakes[msg.sender];
        providerStakes[msg.sender] = 0;
        registeredProviders[msg.sender] = false;
        nrc.transfer(msg.sender, stake);
        emit ProviderUnregistered(msg.sender);
    }

    // ── Job lifecycle ─────────────────────────────────────────────────────────

    /**
     * @notice Submit a new compute job.
     * @param specHash  IPFS CID of the job specification JSON.
     * @param stake     NRC amount to lock as payment.
     */
    function submitJob(bytes32 specHash, uint256 stake) external nonReentrant returns (uint256) {
        require(stake > 0, "JobRegistry: stake must be positive");
        require(
            nrc.transferFrom(msg.sender, address(this), stake),
            "JobRegistry: payment transfer failed"
        );

        uint256 jobId = nextJobId++;
        jobs[jobId] = Job({
            id:          jobId,
            requester:   msg.sender,
            provider:    address(0),
            stake:       stake,
            reward:      0,
            specHash:    specHash,
            outputHash:  bytes32(0),
            status:      JobStatus.Open,
            createdAt:   block.timestamp,
            completedAt: 0
        });

        emit JobSubmitted(jobId, msg.sender, stake);
        return jobId;
    }

    /**
     * @notice Accept and begin working on a job.
     * @param jobId  ID of the job to accept.
     */
    function acceptJob(uint256 jobId) external {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Open, "JobRegistry: job not open");
        require(registeredProviders[msg.sender], "JobRegistry: not a registered provider");

        job.provider = msg.sender;
        job.status   = JobStatus.Assigned;
        emit JobAssigned(jobId, msg.sender);
    }

    /**
     * @notice Submit completed job output and claim payment.
     * @param jobId       ID of the completed job.
     * @param outputHash  Hash of the output artifacts (IPFS CID).
     */
    function submitOutput(uint256 jobId, bytes32 outputHash) external nonReentrant {
        Job storage job = jobs[jobId];
        require(job.status == JobStatus.Assigned, "JobRegistry: job not assigned");
        require(job.provider == msg.sender, "JobRegistry: not the assigned provider");

        job.outputHash  = outputHash;
        job.status      = JobStatus.Completed;
        job.completedAt = block.timestamp;

        // Calculate fee and provider reward
        uint256 fee    = (job.stake * PROTOCOL_FEE_BPS) / 10_000;
        uint256 reward = job.stake - fee;

        // Transfer fee to treasury, reward to provider
        nrc.transfer(treasury, fee);
        nrc.transfer(msg.sender, reward);

        emit JobCompleted(jobId, outputHash);
    }

    /**
     * @notice Cancel an open job and reclaim stake.
     * @param jobId  ID of the job to cancel.
     */
    function cancelJob(uint256 jobId) external nonReentrant {
        Job storage job = jobs[jobId];
        require(job.requester == msg.sender, "JobRegistry: not job owner");
        require(job.status == JobStatus.Open, "JobRegistry: cannot cancel assigned job");

        job.status = JobStatus.Cancelled;
        nrc.transfer(msg.sender, job.stake);
        emit JobCancelled(jobId);
    }

    // ── View ──────────────────────────────────────────────────────────────────

    function getJob(uint256 jobId) external view returns (Job memory) {
        return jobs[jobId];
    }

    function totalJobs() external view returns (uint256) {
        return nextJobId;
    }
}
