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

The Proof of Compute verification algorithm is the cryptographic core of NeuraCoin's trustless execution model. It ensures that compute providers have genuinely executed submitted jobs according to specification.

#### 3.4.1 Proof Generation (Provider Side)

When a compute provider executes a job, it generates a proof containing:

- **Job ID**: Unique identifier linking to the job specification contract
- **Output Hash**: SHA-3(flattened output tensor)
- **Execution Metadata**: GPU device fingerprint, wall-clock time, memory peak usage
- **Intermediate Checkpoints**: Layer-wise activation hashes at specified intervals (for deep learning jobs)
- **Nonce**: Random value to prevent replay attacks

All proof components are signed by the provider's secp256k1 private key and submitted on-chain as a transaction to the ProofVerification contract.

#### 3.4.2 Verification Process

Upon proof submission, the protocol executes a three-phase verification:

**Phase 1: Syntactic Validation**
- Verify provider signature matches registered compute node
- Check job ID exists and is not already settled
- Validate proof timestamp is within acceptable submission window (within job deadline + 1 hour grace period)
- Confirm provider stake is above minimum threshold

**Phase 2: Stochastic Sampling Verification**
- A randomized subset of validators (selected via VRF) re-execute the job independently
- Each validator runs the job in an isolated Docker container with identical hyperparameters
- Validators produce reference output tensors using deterministic seeds
- Compare provider output against validator outputs using L2 norm distance:
  ```
  distance = sqrt(sum((provider_output - validator_output)^2)) / norm(validator_output)
  ```
- Accept if `distance < epsilon_tolerance` (default: 0.01 for float32 operations)
- This accounts for hardware-specific floating point rounding variations

**Phase 3: Consensus Aggregation**
- Require supermajority (66.7%) of sampling validators to agree on validity
- If consensus reached: mark proof as **VERIFIED** and proceed to settlement
- If consensus not reached: slash provider stake by 5% and emit **INVALID** event
- If fewer than 10% of validators respond within timeout (2 hours): pause job and require manual arbitration

#### 3.4.3 Handling Hardware Variance

Different GPUs (NVIDIA A100, RTX 4090, etc.) produce slightly different floating-point results due to:
- Kernel implementation differences
- Precision of transcendental functions
- Tensor core precision modes

NeuraCoin mitigates this via:
- **Epsilon Calibration**: Per-device epsilon values stored on-chain (e.g., 0.008 for NVIDIA A100, 0.012 for consumer GPUs)
- **Reduced Precision Mode**: Jobs can opt for float16 execution (stricter tolerance: 0.005)
- **Reference Hardware**: Validators use a specified reference GPU model for their executions; provider outputs are normalized to equivalent reference device precision

#### 3.4.4 Computational Integrity Bonds

To prevent Sybil attacks where malicious providers submit many false proofs, providers must maintain:
- **Minimum Stake**: 100 NRC per concurrent job (forfeit on slashing)
- **Reputation Score**: Exponential moving average of successful verifications; new providers start at 0.5x validator sampling multiplier
- **Timeout Penalty**: Failure to complete within deadline triggers 2% stake slash per day overdue

#### 3.4.5 Validator Economics

Validators earn rewards:
- **Base Verification Fee**: 0.1 NRC per proof verified (paid from job requester's stake)
- **Consensus Bonus**: +50% if their vote matches final consensus
- **Slashing Dividend**: Slashed provider stake distributed equally among validators who voted correctly

This incentivizes honest verification while penalizing false consensus.

---

## 4. Tokenomics

NRC total supply: 1 billion tokens.

- 40% to compute providers (rewards pool)
- 20% to protocol treasury (development & governance)
- 15% to validators (verification rewards)
- 15% to early backers
- 10% to team (4-year vesting)

Emissions follow a halvening schedule every 2 years.

---

## 5. Security Considerations

### 5.1 Attacks & Mitigations

**False Output Submission**: Provider submits incorrect computation result.
- *Mitigation*: Validator re-execution with supermajority consensus; stake slashing.

**Sybil Attack**: Attacker registers many fake validators.
- *Mitigation*: Minimum validator stake (10k NRC); time-lock on validator registration.

**Timing Side Channels**: Provider extracts information via execution time.
- *Mitigation*: Jobs run in timing-oblivious containers; all providers see identical wall-clock allowance.

**Dataset Poisoning**: Requester supplies malicious dataset to extract provider secrets.
- *Mitigation*: Providers execute in privacy-preserving containers (future: TEE integration); input data hashed and versioned.

### 5.2 Future Enhancements

- **Zero-Knowledge Proofs**: Replace sampling validators with ZK circuits to reduce verification overhead
- **Hardware Attestation**: Integrate Intel SGX / ARM TrustZone for tamper-proof execution environments
- **Cross-Chain Verification**: Enable compute verification on non-EVM chains via light clients

---

## 6. Conclusion

NeuraCoin democratizes access to AI compute by replacing centralized intermediaries with a transparent, cryptographically-secured protocol. Proof of Compute ensures economic fin