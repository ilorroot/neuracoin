# NeuraCoin Whitepaper v0.1

## Abstract

NeuraCoin (NRC) is a decentralized compute-sharing protocol built on EVM-compatible blockchain infrastructure. It enables trustless exchange of AI training compute between job requesters and compute providers, settled via cryptographic proof-of-compute verification and automated smart contract escrow.

---

## 1. Introduction

The artificial intelligence industry faces a fundamental resource asymmetry. On one side, researchers, startups, and enterprises require vast amounts of GPU compute for model training and inference. On the other, a globally distributed network of GPU-equipped machines sits underutilized — gaming computers, workstations, and small data centers with excess capacity.

Existing solutions (AWS, GCP, Lambda Labs) are centralized, expensive, and opaque. NeuraCoin proposes a permissionless alternative: a protocol layer where compute supply and demand meet directly, mediated by smart contracts and verified by a decentralized validator network.

---

## 2. Protocol Architecture

### 2.1 Participants

**Job Requesters** submit training or inference jobs to the NeuraCoin network. They stake NRC tokens as payment, which are held in escrow until job completion is verified.

**Compute Providers** run the NeuraCoin node client on their hardware. They accept jobs from the network, execute them in isolated containers, and submit cryptographic proofs of completion.

**Validators** are a subset of high-stake NRC holders who verify proof-of-compute submissions and slash dishonest providers.

### 2.2 Job Lifecycle

1. Requester submits job specification (model architecture, dataset hash, hyperparameters) and NRC stake to the Job Registry contract.
2. Protocol matches job to eligible compute nodes based on hardware requirements and availability.
3. Compute provider downloads job, executes in sandboxed environment, produces output + proof hash.
4. Validators check proof. Supermajority agreement triggers settlement.
5. NRC released from escrow to provider. Output delivered to requester.

### 2.3 Proof of Compute

NeuraCoin uses a novel **Proof of Compute (PoC)** mechanism. Rather than wasteful hash computation (Proof of Work), PoC requires nodes to produce verifiable outputs from deterministic ML workloads. A reference execution is run by a validator subset, and output tensors are compared within an epsilon tolerance to account for floating point variance across hardware.

---

## 3. Smart Contracts

### 3.1 NRC Token (ERC-20)
Standard ERC-20 token with additional staking and slashing logic.

### 3.2 Job Registry
Stores job specifications, matches providers, manages escrow lifecycle.

### 3.3 Validator Registry
Manages validator set, stake requirements, and slashing conditions.

### 3.4 Proof of Compute Verification Algorithm

The Proof of Compute verification algorithm is the cryptographic core of NeuraCoin's trustless execution model. It ensures that compute providers have genuinely executed submitted jobs and produced correct outputs, without requiring full re-execution by every network participant.

#### 3.4.1 Overview

The verification process consists of three phases:

1. **Commitment Phase**: Provider commits to job execution before completion
2. **Submission Phase**: Provider submits output hash, execution metrics, and cryptographic proof
3. **Challenge & Verification Phase**: Validators verify the proof deterministically

#### 3.4.2 Execution Commitment

When a compute provider accepts a job, they commit to an execution context:

```
ExecutionCommitment = {
  jobId: bytes32,
  providerId: address,
  hardwareSpec: {
    gpuModel: string,
    vramGb: uint32,
    cpuCores: uint32
  },
  estimatedDuration: uint64,
  timestamp: uint256,
  nonce: bytes32
}

CommitmentHash = keccak256(abi.encode(ExecutionCommitment))
```

This commitment is signed by the provider and recorded on-chain, creating an immutable record that the computation occurred within a specific time window and hardware context.

#### 3.4.3 Output Proof Generation

Upon job completion, the provider generates a Merkle tree of intermediate tensor checkpoints at regular intervals (every N batches). This allows validators to spot-check computation at arbitrary depths without reprocessing the entire job.

```
ProofArtifacts = {
  finalOutputHash: bytes32,           // SHA-256 of output tensor
  intermediateCheckpoints: bytes32[], // Merkle tree of internal states
  executionMetrics: {
    totalBatches: uint32,
    computeTimeMs: uint64,
    peakMemoryMb: uint32,
    flopsEstimate: uint64
  },
  systemSignature: bytes,             // Provider's ECDSA signature
  gpuTelemetry: {
    gpuUtilization: uint8,   // 0-100
    gpuMemoryUsed: uint32,
    thermalEvents: uint8
  }
}
```

The provider submits these artifacts to the VerificationRegistry contract along with a bond (additional NRC collateral).

#### 3.4.4 Deterministic Reference Execution

A small subset of validators (selected via VRF-based random sampling) are assigned to perform a reference execution. These validators:

1. Download the exact job specification and seed dataset
2. Execute the job on standardized GPU hardware (or via attestation-capable TEE)
3. Produce their own output hash and intermediate checkpoints
4. Compare their results against the provider's submission

The reference execution uses deterministic ML kernels (fixed cuDNN versions, seeded RNG initialization, no async operations) to ensure bit-identical outputs across hardware variants.

#### 3.4.5 Floating Point Tolerance

Due to hardware variance and parallel reduction operations, exact byte-for-byte output matching is infeasible. Instead, validators apply L2-norm distance verification:

```
maxAllowedError = sqrt(sum((referenceOutput - submittedOutput)^2)) / sqrt(sum(referenceOutput^2))

if maxAllowedError <= toleranceThreshold:
    proof_valid = true
else:
    proof_valid = false
```

The tolerance threshold is dynamically adjusted based on:
- Job complexity (larger models allow higher tolerance)
- Output precision (float32 vs float64)
- Hardware class of execution

For inference jobs, accuracy metrics (classification error rate, mean absolute error) are verified directly against a reference model evaluation.

#### 3.4.6 Consensus & Slashing

Validators submit their verification results (valid/invalid) with a cryptographic signature. The protocol requires:

- **Minimum supermajority** (66%+) of assigned validators to agree
- **Unanimous agreement** among validators to slash the provider

If fewer than 66% of validators agree that a proof is valid:
- Provider's bond is slashed (50% to the validator set, 50% to the protocol treasury)
- Job result is marked as disputed, requester can resubmit

If a validator submits a false verification (provably dishonest):
- Validator's stake is slashed and locked for 90 days
- Validator is temporarily removed from the validator set

#### 3.4.7 Computational Complexity Constraints

To prevent validators from being overloaded, jobs are restricted by a **Proof Complexity Budget**:

```
proofComplexityScore = (modelFLOPs / 1e12) * (executionTimeSeconds / 3600) * (gpuMemoryGb / 80)

maxComplexityScore = 1000  // Equivalent to ~100 hours on an RTX 4090
```

Jobs exceeding this threshold are split into subjobs by the Job Router contract, each verified independently.

#### 3.4.8 Fraud Detection

The protocol implements several anti-fraud mechanisms:

- **Output Sanity Checks**: Validators verify that output tensor magnitudes are within expected ranges (detects zero-output or NaN injection)
- **Timing Analysis**: Execution time must be within 20% of the provider's committed estimate
- **Checkpoint Consistency**: Intermediate checkpoints must form a valid Merkle tree path
- **Hardware Attestation**: For high-value jobs, GPU providers can enable remote attestation (SGX, SEV) to prove genuine execution

---

## 4. Governance
On-chain governance for protocol parameter updates via NRC token voting.

---

## 5. Tokenomics

### 5.1