# NeuraCoin Whitepaper v0.1

## Abstract

NeuraCoin (NRC) is a decentralized compute-sharing protocol built on EVM-compatible blockchain infrastructure. It enables trustless exchange of AI training compute between job requesters and compute providers, settled via cryptographic proof-of-compute verification and automated smart contract escrow.

---

## 1. Introduction

The artificial intelligence industry faces a fundamental resource asymmetry. On one side, researchers, startups, and enterprises require vast amounts of GPU compute for model training and inference. On the other, a globally distributed network of GPU-equipped machines sits underutilized ó gaming computers, workstations, and small data centers with excess capacity.

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

### 3.1 NRC Token

NRC is an ERC-20 compatible token with a fixed initial supply of 1,000,000,000 (one billion) units. The token contract exposes standard `transfer`, `approve`, and `transferFrom` semantics, plus protocol-specific hooks:

- `lockForJob(uint256 jobId, uint256 amount)` ó moves tokens into the JobEscrow contract.
- `releaseForJob(uint256 jobId, address provider)` ó callable only by the JobRegistry on settlement.
- `slash(address provider, uint256 amount)` ó callable only by the Validator contract on proven misbehavior.

### 3.2 JobRegistry

The JobRegistry contract is the canonical source of truth for job state. Each job transitions through a finite state machine:


PENDING -> ASSIGNED -> EXECUTING -> PROVED -> SETTLED
                                          \-> DISPUTED -> SLASHED | SETTLED


Job records include: requester address, provider address (once assigned), spec hash (IPFS CID), reward amount, deadline, and final proof hash.

### 3.3 ValidatorSet

Validators stake a minimum of 100,000 NRC to participate. The active validator set is rotated each epoch (~24 hours) using stake-weighted random selection. Validators earn a fee (default 2%) on every settled job they attest to. Equivocation or invalid attestations result in stake slashing.

### 3.4 JobEscrow

Holds locked NRC for the duration of a job. Releases funds atomically on settlement: provider receives reward minus validator fee, validators split the fee proportionally to stake, and the protocol treasury collects a small (0.5%) burn-or-fund toggle.

---

## 4. Token Utility

NRC has four primary uses inside the protocol:

1. **Payment.** Job requesters pay providers in NRC. All compute is denominated in NRC.
2. **Staking.** Providers stake NRC as collateral against the jobs they accept. Validators stake NRC to be eligible to attest.
3. **Governance.** NRC holders vote on protocol parameters (validator fee, minimum stake, epsilon tolerance, epoch length) via a standard on-chain governor contract.
4. **Slashing collateral.** Misbehaving providers and validators forfeit staked NRC, which is partially burned and partially redistributed to honest participants.

---

## 5. Economic Model

### 5.1 Supply

- Initial supply: 1,000,000,000 NRC, minted at genesis to the deployer-controlled treasury.
- Distribution: 40% community/airdrop, 25% provider incentives (4-year vesting), 20% team (4-year vesting, 1-year cliff), 15% treasury.
- No further inflation. Validator and provider rewards are sourced from job fees, not new issuance.

### 5.2 Fees

Each settled job incurs:

- Validator fee: 2% of reward (configurable via governance).
- Protocol fee: 0.5% of reward, sent to the treasury.
- Net to provider: 97.5% of the requester's posted reward.

### 5.3 Slashing

- Provider produces invalid output: up to 100% of provider stake for that job is slashed.
- Validator signs an attestation contradicted by supermajority: 10% of validator's total stake slashed.
- Slashed amounts: 50% burned, 50% to the job's honest counterparty (or treasury if no counterparty applies).

---

## 6. Security Considerations

- **Sybil resistance.** Stake requirements for both providers and validators make Sybil attacks economically prohibitive.
- **Output forgery.** Deterministic seed + reference re-execution by validators detects forged outputs within the epsilon tolerance.
- **Data privacy.** v0.1 assumes public datasets and public model weights. Confidential workloads (TEE-based execution, ZK proofs of training) are deferred to v0.2.
- **MEV / front-running.** Job assignment is performed by the protocol via commit-reveal scheduling to prevent providers from cherry-picking high-reward jobs.

---

## 7. Roadmap

- **v0.1 (this document):** Core contracts (NRCToken, JobRegistry, ValidatorSet, JobEscrow), reference Python client, deterministic CPU-only workloads.
- **v0.2:** GPU workload support, IPFS integration for job specs and outputs, governance contract.
- **v0.3:** TEE-attested execution for confidential workloads, cross-chain bridge for multi-EVM deployment.
- **v1.0:** ZK proofs of training step correctness, mainnet launch.

---

## 8. References

- Ethereum Yellow Paper, Wood (2014).
- ERC-20 Token Standard, Vogelsteller & Buterin (2015).
- Gensyn Litepaper (2022) ó comparable verifiable-compute primitives.
- Truebit: A scalable verification solution for blockchains, Teutsch & Reitwieﬂner (2017).

---

*This document is v0.1 and is intended as a normative reference for the initial NeuraCoin contracts and client implementations. Section numbering and contract names defined here are stable; subsequent revisions will be additive where possible.*
