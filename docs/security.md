# NeuraCoin Security Model

## Overview

NeuraCoin implements a multi-layered security architecture to protect GPU contributors, job requesters, and the protocol itself. This document outlines sandboxing mechanisms, slashing conditions, and audit procedures.

## 1. Container Sandboxing

### 1.1 Execution Environment

All AI jobs execute within isolated Docker containers with restricted capabilities:

```yaml
SecurityContext:
  RunAsNonRoot: true
  RunAsUser: 1000
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
  NetworkPolicy: Egress to trusted validator nodes only
  ProcessLimit: 256
  FileDescriptors: 1024
  MaxFileSize: 10Gi
```

### 1.2 File System Isolation

- **Read-only layers**: OS and application libraries mounted immutable via overlay2
- **Ephemeral scratch**: `/tmp` and `/home/worker` created fresh per job, cleaned on termination with secure wipe
- **Network segregation**: Internal network only via network namespacing, no direct internet access
- **Volume mounts**: Restricted to job-specific `/input` and `/output` directories with `noexec`, `nodev`, `nosuid` flags
- **Device access**: No access to `/dev/mem`, `/dev/kmem`, or host GPU device files (passed explicitly via allowlist)
- **IPC namespace**: Isolated from host and other containers

### 1.3 Runtime Monitoring

- **Seccomp profiles**: Block dangerous syscalls (`ptrace`, `execve`, `mount`, `setuid`, `clone`, `fork`, `ioctl`)
- **AppArmor/SELinux**: Enforce mandatory access control policies with deny-by-default approach
- **CRI-O/containerd**: Prevent privilege escalation and kernel module loading
- **Resource enforcement**: cgroups v2 with strict memory/CPU throttling and OOM killer protection
- **System call auditing**: Log all syscalls to immutable audit log for forensic analysis

### 1.4 GPU Isolation

- **GPU namespacing**: Jobs assigned specific GPU indices via environment variables
- **VRAM limits**: Enforced via NVIDIA Container Runtime memory constraints
- **Device file restrictions**: Only assigned GPU device nodes mounted in container
- **Compute capability restrictions**: Jobs execute with reduced compute privileges

## 2. Smart Contract Slashing

### 2.1 Slashing Events

GPU contributors face penalties for protocol violations:

| Violation | Slash Amount | Conditions | Appeal Window | Recovery |
|-----------|-------------|-----------|----------------|-----------|
| Job timeout/crash | 2% | Job exceeds agreed time by >20% | 7 days | Automatic after appeal resolution |
| Memory violation | 5% | Memory usage exceeds requested by >10% | 7 days | Automatic after appeal resolution |
| Output mismatch | 10% | Verifiable difference from reference run | 14 days | Automatic after appeal resolution |
| Missed heartbeat | 1% per occurrence | No health signal for 15+ minutes | 3 days | Automatic after appeal resolution |
| Malicious code injection | 100% | Detected exploit/backdoor/rootkit | 30 days | None - permanent ban eligible |
| Data exfiltration | 50% | Unauthorized data access/copy detected | 14 days | None - permanent ban eligible |
| Hardware failure | 0% | Legitimate equipment failure with proof | N/A | Stake restored |

### 2.2 Smart Contract Implementation

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

interface ISlashingManager {
    event SlashingEvent(
        address indexed contributor,
        uint256 indexed jobId,
        uint256 slashAmount,
        string reason,
        uint256 timestamp
    );

    event AppealSubmitted(
        address indexed contributor,
        uint256 indexed jobId,
        bytes32 evidenceHash,
        uint256 timestamp
    );

    event AppealResolved(
        uint256 indexed jobId,
        bool slashConfirmed,
        address indexed resolver,
        uint256 timestamp
    );

    event ContributorBanned(
        address indexed contributor,
        string reason,
        uint256 timestamp
    );
}

contract SlashingManager is ISlashingManager {
    struct SlashingRecord {
        address contributor;
        uint256 jobId;
        uint256 slashAmount;
        string reason;
        uint256 timestamp;
        bool appealed;
        bool resolved;
    }

    struct AppealRecord {
        uint256 slashingId;
        bytes32 evidenceHash;
        uint256 submittedAt;
        bool resolved;
        bool slashConfirmed;
        address resolver;
    }

    mapping(uint256 => SlashingRecord) public slashings;
    mapping(uint256 => AppealRecord) public appeals;
    mapping(address => bool) public bannedContributors;
    mapping(address => uint256) public totalSlashed;
    
    uint256 public slashingCounter;
    uint256 public appealWindowDays = 7;
    uint256 public constant MAJOR_SLASH_THRESHOLD = 50;
    
    address public slashingAuthority;
    address public appealsDAO;

    modifier onlySlashingAuthority() {
        require(msg.sender == slashingAuthority, "Unauthorized");
        _;
    }

    modifier onlyAppealDAO() {
        require(msg.sender == appealsDAO, "Only DAO can resolve");
        _;
    }

    constructor(address _authority, address _appealsDAO) {
        slashingAuthority = _authority;
        appealsDAO = _appealsDAO;
    }

    function submitSlashing(
        address contributor,
        uint256 jobId,
        uint256 slashPercentage,
        string calldata reason
    ) external onlySlashingAuthority returns (uint256) {
        require(!bannedContributors[contributor], "Contributor banned");
        require(slashPercentage > 0 && slashPercentage <= 100, "Invalid percentage");

        uint256 slashingId = slashingCounter++;
        SlashingRecord storage record = slashings[slashingId];
        
        record.contributor = contributor;
        record.jobId = jobId;
        record.slashAmount = slashPercentage;
        record.reason = reason;
        record.timestamp = block.timestamp;
        record.appealed = false;
        record.resolved = false;

        if (slashPercentage >= MAJOR_SLASH_THRESHOLD) {
            bannedContributors[contributor] = true;
            emit ContributorBanned(contributor, reason, block.timestamp);
        }

        totalSlashed[contributor] += slashPercentage;
        emit SlashingEvent(contributor, jobId, slashPercentage, reason, block.timestamp);

        return slashingId;
    }

    function submitAppeal(
        uint256 slashingId,
        bytes32 evidenceHash
    ) external {
        SlashingRecord storage record = slashings[slashingId];
        require(msg.sender == record.contributor, "Not contributor");
        require(!record.resolved, "Already resolved");
        require(record.appealed == false, "Appeal already submitted");
        require(
            block.timestamp <= record.timestamp + (appealWindowDays * 1 days),
            "Appeal window closed"
        );

        record.appealed = true;
        appeals[slashingId] = AppealRecord({
            slashingId: slashingId,
            evidenceHash: evidenceHash,
            submittedAt: block.timestamp,
            resolved: false,
            slashConfirmed: false