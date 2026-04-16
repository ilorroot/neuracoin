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

    // ── View Functions ────────────────────────────────────────────────────────

    /**
     * @notice Returns all open job IDs
     * @return Array of job IDs with status == Open
     */
    function getOpenJobs() external view returns (uint256[] memory) {
        uint256 openCount = 0;
        
        // Count open jobs
        for (uint256 i = 1; i < nextJobId; i++) {
            if (jobs[i].status == JobStatus.Open) {
                openCount++;
            }
        }
        
        // Allocate result array
        uint256[] memory result = new uint256[](openCount);
        uint256 index = 0;
        
        // Populate result array
        for (uint256 i = 1; i < nextJobId; i++) {
            if (jobs[i].status == JobStatus.Open) {
                result[index] = i;
                index++;
            }
        }
        
        return result;
    }

    /**
     * @notice Returns the total number of jobs in the registry
     * @return Total job count
     */
    function getJobCount() external view returns (uint256) {
        return nextJobId - 1;
    }

    /**
     * @notice Retrieves full job details by ID
     * @param jobId The job ID to query
     * @return Job struct containing all job details
     */
    function getJob(uint256 jobId) external view returns (Job memory) {
        require(jobId > 0 && jobId < nextJobId, "Job does not exist");
        return jobs[jobId];
    }

}