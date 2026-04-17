# NeuraCoin Security Model

## Overview

NeuraCoin implements a multi-layered security architecture to protect GPU contributors, job requesters, and the protocol itself. This document outlines sandboxing mechanisms, slashing conditions, and audit procedures.

## 1. Container Sandboxing

### 1.1 Execution Environment

All AI jobs execute within isolated Docker containers with restricted capabilities:

```yaml
SecurityContext:
  RunAsNonRoot: true
  ReadOnlyRootFilesystem: true
  AllowPrivilegeEscalation: false
  Capabilities:
    Drop:
      - ALL
    Add:
      - NET_BIND_SERVICE
  SeccompProfile:
    Type: RuntimeDefault
  SELinuxOptions:
    Level: "s0:c123,c456"

ResourceLimits:
  Memory: 16Gi
  CPU: 8
  Disk: 100Gi
  EphemeralStorage: 50Gi
  NetworkPolicy: Egress to trusted nodes only
  ProcessLimit: 256
```

### 1.2 File System Isolation

- **Read-only layers**: OS and application libraries mounted immutable via overlay2
- **Ephemeral scratch**: `/tmp` and `/home/worker` created fresh per job, cleaned on termination
- **Network segregation**: Internal network only via network namespacing, no direct internet access
- **Volume mounts**: Restricted to job-specific `/input` and `/output` directories with noexec flag
- **Device access**: No access to `/dev/mem`, `/dev/kmem`, or GPU device files (passed explicitly)

### 1.3 Runtime Monitoring

- **Seccomp profiles**: Block dangerous syscalls (ptrace, execve, mount, setuid)
- **AppArmor/SELinux**: Enforce mandatory access control policies
- **CRI-O containerd**: Prevent privilege escalation and kernel module loading
- **Resource enforcement**: cgroups v2 with strict memory/CPU throttling and OOM killer protection

## 2. Smart Contract Slashing

### 2.1 Slashing Events

GPU contributors face penalties for protocol violations:

| Violation | Slash Amount | Conditions | Appeal Window |
|-----------|-------------|-----------|----------------|
| Job timeout/crash | 2% | Job exceeds agreed time by >20% | 7 days |
| Memory violation | 5% | Memory usage exceeds requested by >10% | 7 days |
| Output mismatch | 10% | Verifiable difference from reference run | 14 days |
| Missed heartbeat | 1% per occurrence | No health signal for 15+ minutes | 3 days |
| Malicious code injection | 100% | Detected exploit/backdoor/rootkit | 30 days |
| Data exfiltration | 50% | Unauthorized data access/copy detected | 14 days |

### 2.2 Smart Contract Implementation

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

interface ISlashingManager {
    event SlashingEvent(
        address indexed contributor,
        uint256 jobId,
        uint256 slashAmount,
        string reason,
        uint256 timestamp
    );

    event AppealSubmitted(
        address indexed contributor,
        uint256 jobId,
        bytes32 evidenceHash
    );

    event AppealResolved(
        uint256 indexed jobId,
        bool slashConfirmed,
        address resolver
    );
}

contract SlashingManager is ISlashingManager {
    struct SlashRecord {
        address contributor;
        uint256 jobId;
        uint256 stakedAmount;
        uint256 slashAmount;
        string reason;
        uint256 timestamp;
        bool appealed;
        bytes32 evidenceHash;
        uint256 resolutionTime;
        bool resolved;
    }

    mapping(uint256 => SlashRecord) public slashRecords;
    mapping(address => uint256) public totalSlashed;
    mapping(address => uint256) public stakedAmount;

    uint256 public constant APPEAL_WINDOW = 7 days;
    uint256 public constant MIN_SLASH_AMOUNT = 1e16;
    uint256 public slashCounter;

    address public governance;
    address public verificationOracle;

    event StakeDeposited(address indexed contributor, uint256 amount);
    event StakeWithdrawn(address indexed contributor, uint256 amount);

    constructor(address _governance, address _verificationOracle) {
        governance = _governance;
        verificationOracle = _verificationOracle;
    }

    /// @notice Execute slashing for a contributor
    /// @param _contributor Address of GPU provider
    /// @param _jobId Associated job identifier
    /// @param _slashPercent Percentage of stake to slash (0-100)
    /// @param _reason Description of violation
    function slash(
        address _contributor,
        uint256 _jobId,
        uint8 _slashPercent,
        string calldata _reason
    ) external onlyGovernance {
        require(_contributor != address(0), "Invalid contributor");
        require(_slashPercent > 0 && _slashPercent <= 100, "Invalid slash percent");
        require(stakedAmount[_contributor] > 0, "No stake found");

        uint256 slashAmount = (stakedAmount[_contributor] * _slashPercent) / 100;
        require(slashAmount >= MIN_SLASH_AMOUNT, "Slash amount too small");

        SlashRecord storage record = slashRecords[slashCounter];
        record.contributor = _contributor;
        record.jobId = _jobId;
        record.stakedAmount = stakedAmount[_contributor];
        record.slashAmount = slashAmount;
        record.reason = _reason;
        record.timestamp = block.timestamp;
        record.appealed = false;
        record.resolved = false;

        stakedAmount[_contributor] -= slashAmount;
        totalSlashed[_contributor] += slashAmount;

        emit SlashingEvent(_contributor, _jobId, slashAmount, _reason, block.timestamp);
        slashCounter++;
    }

    /// @notice Submit appeal for slashing decision
    /// @param _slashId ID of slash record
    /// @param _evidenceHash IPFS hash of appeal evidence
    function submitAppeal(uint256 _slashId, bytes32 _evidenceHash) external {
        SlashRecord storage record = slashRecords[_slashId];
        require(msg.sender == record.contributor, "Only contributor can appeal");
        require(!record.appealed, "Appeal already submitted");
        require(
            block.timestamp <= record.timestamp + APPEAL_WINDOW,
            "Appeal window closed"
        );

        record.appealed = true;
        record.evidenceHash = _evidenceHash;

        emit AppealSubmitted(msg.sender, record.jobId, _evidenceHash);
    }

    /// @notice Resolve appeal (called by governance/oracle)
    /// @param _slashId ID of slash record
    /// @param _slashConfirmed Whether to uphold the slash
    function resolveAppeal(uint256 _slashId, bool _slashConfirmed) external {
        require(msg.sender == governance || msg.sender == verificationOracle, "Unauthorized");
        SlashRecord storage record = slashRecords[_slashId];
        require(record.appealed, "No appeal submitted");
        require(!record.resolved, "Already resolved");

        record.resolved = true;
        record.resolutionTime = block.timestamp;

        if (!_slashConfirmed) {
            stakedAmount[record.contributor] += record.slashAmount;
            totalSlashed[record.contributor] -= record.slashAmount;
        }

        emit AppealResolved(record.jobId, _slashConfirmed, msg.sender);
    }

    /// @notice Deposit stake for GPU provider
    /// @param _amount Amount of NRC to stake
    function depositStake(uint256 _amount) external {
        require(_amount > 0, "Amount must be positive");
        stakedAmount[msg.sender] +=