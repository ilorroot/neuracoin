# NeuraCoin Security Model

## Overview

NeuraCoin implements a multi-layered security architecture to protect GPU contributors, job requesters, and the protocol itself. This document outlines sandboxing mechanisms, slashing conditions, and audit procedures.

## 1. Container Sandboxing

### 1.1 Execution Environment

All AI jobs execute within isolated Docker containers with restricted capabilities:

```yaml
SecurityContext:
  - RunAsNonRoot: true
  - ReadOnlyRootFilesystem: true
  - AllowPrivilegeEscalation: false
  - Capabilities:
      Drop:
        - ALL
      Add:
        - NET_BIND_SERVICE
  - SeccompProfile:
      Type: RuntimeDefault

ResourceLimits:
  - Memory: 16Gi max
  - CPU: 8 cores max
  - Disk: 100Gi ephemeral
  - NetworkPolicy: Egress to trusted nodes only
```

### 1.2 File System Isolation

- **Read-only layers**: OS and libraries immutable
- **Ephemeral scratch**: `/tmp` and `/home/worker` isolated per job
- **Network segregation**: Internal network only, no direct internet access
- **Volume mounts**: Restricted to job-specific input/output directories

## 2. Smart Contract Slashing

### 2.1 Slashing Events

GPU contributors face penalties for:

| Violation | Slash Amount | Conditions |
|-----------|-------------|-----------|
| Job timeout/crash | 2% | Job exceeds agreed time by >20% |
| Memory violation | 5% | Memory usage exceeds requested by >10% |
| Output mismatch | 10% | Verifiable difference from reference run |
| Malicious code injection | 100% | Detected exploit/backdoor attempt |
| Missed heartbeat | 1% per 5min | No health signal for 15+ minutes |

### 2.2 Smart Contract Implementation

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

interface ISlashingManager {
    event SlashingEvent(
        address indexed contributor,
        uint256 amount,
        string reason,
        uint256 timestamp
    );
    
    event AppealSubmitted(
        address indexed contributor,
        uint256 jobId,
        bytes32 evidence
    );
    
    event AppealResolved(
        uint256 indexed jobId,
        bool slashingConfirmed,
        address resolver
    );
}

contract SlashingManager is ISlashingManager {
    struct SlashRecord {
        address contributor;
        uint256 stakedAmount;
        uint256 slashAmount;
        string reason;
        uint256 timestamp;
        bool appealed;
        bytes32 evidenceHash;
        uint256 resolutionTime;
    }
    
    mapping(uint256 => SlashRecord) public slashRecords;
    mapping(address => uint256) public totalSlashed;
    
    uint256 public constant APPEAL_WINDOW = 7 days;
    uint256 public constant MIN_SLASH_AMOUNT = 1e16; // 0.01 NRC
    
    address public governance;
    
    constructor(address _governance) {
        governance = _governance;
    }
    
    /// @notice Execute slashing for a contributor
    /// @param _contributor Address of GPU provider
    /// @param _jobId Associated job identifier
    /// @param _slashPercent Percentage of stake to slash (1-100)
    /// @param _reason Human-readable reason code
    function executeSlash(
        address _contributor,
        uint256 _jobId,
        uint256 _slashPercent,
        string memory _reason
    ) external onlyValidator returns (bool) {
        require(_slashPercent > 0 && _slashPercent <= 100, "Invalid slash %");
        require(_contributor != address(0), "Invalid contributor");
        
        uint256 stakedAmount = getContributorStake(_contributor);
        uint256 slashAmount = (stakedAmount * _slashPercent) / 100;
        
        require(slashAmount >= MIN_SLASH_AMOUNT, "Slash too small");
        
        SlashRecord storage record = slashRecords[_jobId];
        record.contributor = _contributor;
        record.stakedAmount = stakedAmount;
        record.slashAmount = slashAmount;
        record.reason = _reason;
        record.timestamp = block.timestamp;
        record.appealed = false;
        
        totalSlashed[_contributor] += slashAmount;
        
        // Transfer slashed amount to treasury
        _transferToTreasury(slashAmount);
        
        emit SlashingEvent(_contributor, slashAmount, _reason, block.timestamp);
        return true;
    }
    
    /// @notice Appeal a slashing decision within window
    /// @param _jobId Job associated with slash
    /// @param _evidenceHash IPFS hash of appeal evidence
    function submitAppeal(
        uint256 _jobId,
        bytes32 _evidenceHash
    ) external {
        SlashRecord storage record = slashRecords[_jobId];
        require(record.timestamp != 0, "Slash not found");
        require(
            block.timestamp <= record.timestamp + APPEAL_WINDOW,
            "Appeal window closed"
        );
        require(!record.appealed, "Already appealed");
        
        record.appealed = true;
        record.evidenceHash = _evidenceHash;
        
        emit AppealSubmitted(msg.sender, _jobId, _evidenceHash);
    }
    
    /// @notice Resolve an appeal (governance only)
    /// @param _jobId Job identifier
    /// @param _confirm True to keep slash, false to reverse
    function resolveAppeal(
        uint256 _jobId,
        bool _confirm
    ) external onlyGovernance {
        SlashRecord storage record = slashRecords[_jobId];
        require(record.appealed, "No appeal on record");
        require(record.resolutionTime == 0, "Already resolved");
        
        record.resolutionTime = block.timestamp;
        
        if (!_confirm) {
            // Reverse the slash
            totalSlashed[record.contributor] -= record.slashAmount;
            _refundFromTreasury(record.contributor, record.slashAmount);
        }
        
        emit AppealResolved(_jobId, _confirm, msg.sender);
    }
    
    function getContributorStake(address _contributor) 
        public 
        view 
        returns (uint256) 
    {
        // Implementation depends on staking contract
        // This is a placeholder
        return 100e18; // 100 NRC default
    }
    
    function _transferToTreasury(uint256 _amount) internal {
        // Transfer NRC to protocol treasury
    }
    
    function _refundFromTreasury(address _recipient, uint256 _amount) internal {
        // Refund NRC from treasury
    }
    
    modifier onlyValidator() {
        // Validator check
        _;
    }
    
    modifier onlyGovernance() {
        require(msg.sender == governance, "Governance only");
        _;
    }
}
```

## 3. Job Verification & Validation

### 3.1 Reference Execution

High-value jobs trigger reference execution verification:

```python
#!/usr/bin/env python3
"""
Job verification engine for NeuraCoin
"""

import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class VerificationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"

@dataclass
class VerificationResult:
    job_id: str
    status: VerificationStatus
    output_hash: str
    reference_hash: str
    tolerance_met: bool
    tolerance_percent: float
    evidence_cid: str
    timestamp: int

class JobVerifier:
    """Verifies