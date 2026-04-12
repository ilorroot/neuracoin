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

### 3.4 Governance
On-chain governance for protocol parameter updates via NRC token voting.

---

## 4. Tokenomics

### 4.1 Emission Schedule
Compute rewards follow a halving schedule every 2 years, starting at 10 NRC per verified compute-hour and halving until the 400M reward pool is exhausted (~10 years).

### 4.2 Fee Structure
All jobs pay a 0.1% protocol fee, distributed to validators and a community treasury.

### 4.3 Staking
Compute providers must stake a minimum of 1,000 NRC to participate. Validators must stake 10,000 NRC. Stake is slashable for provably dishonest behavior.

---

## 5. Security Considerations

- Job sandboxing via containerization prevents provider access to requester data
- Dataset hashes are verified before job execution
- Sybil resistance via staking requirements
- Slashing deters malicious validation

---

## 6. Conclusion

NeuraCoin creates a new primitive for the AI economy: trustless, permissionless access to distributed compute. By aligning incentives between hardware owners and AI builders, NeuraCoin aims to democratize access to the compute layer that underlies modern artificial intelligence.

---

*This whitepaper is a living document and will be updated as the protocol design matures.*
