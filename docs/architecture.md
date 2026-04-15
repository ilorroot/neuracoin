# NeuraCoin System Architecture

## Overview

NeuraCoin is a decentralized AI compute-sharing protocol where GPU owners (Providers) earn NRC tokens by executing AI inference and training jobs submitted by Users. The system is built on Ethereum with off-chain compute coordination.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Web UI       │  │ CLI Tool     │  │ SDK/Library  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         └────────────────────┬────────────────┘                 │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                    API GATEWAY LAYER                            │
├─────────────────────────────┼───────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ REST API / GraphQL Endpoint                             │    │
│  │ - Job Submission  - Status Queries  - Payment Handling  │    │
│  └──────┬──────────────────────────┬──────────────────────┘    │
│         │                          │                            │
└─────────┼──────────────────────────┼────────────────────────────┘
          │                          │
┌─────────┼──────────────────────────┼────────────────────────────┐
│         │      SMART CONTRACT LAYER (Ethereum)                  │
│         │                          │                            │
│  ┌──────▼──────────┐  ┌───────────▼──────┐  ┌──────────────┐   │
│  │ JobRegistry.sol │  │ PaymentManager   │  │ TokenERC20   │   │
│  │ - Post jobs     │  │ .sol             │  │ (NRC Token)  │   │
│  │ - Track state   │  │ - Escrow         │  │              │   │
│  │ - Verify proofs │  │ - Settlement     │  │              │   │
│  └──────┬──────────┘  └────────┬─────────┘  └──────────────┘   │
│         │                      │                                │
│  ┌──────▼──────────────────────▼────────────────────────────┐   │
│  │ ProviderRegistry.sol                                     │   │
│  │ - Register GPU providers  - Manage reputation           │   │
│  │ - Stake management        - Slashing on fraud           │   │
│  └──────┬─────────────────────────────────────────────────┘    │
│         │                                                       │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────────┐
│         │        COORDINATION LAYER (Off-chain)                 │
│         │                                                       │
│  ┌──────▼──────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ Job Coordinator │  │ Matchmaker   │  │ Proof Verifier   │   │
│  │ - Match jobs to │  │ - Algorithm  │  │ - ZK proof check │   │
│  │   providers     │  │ - Optimize   │  │ - Result valid.  │   │
│  └──────┬──────────┘  └──────────────┘  └──────┬───────────┘   │
│         │                                       │                │
└─────────┼───────────────────────────────────────┼────────────────┘
          │                                       │
┌─────────┼───────────────────────────────────────┼────────────────┐
│         │        COMPUTE PROVIDER LAYER                          │
│         │                                       │                │
│  ┌──────▼──────────────────┐  ┌────────────────▼────────────┐   │
│  │ Provider Node (p2p)     │  │ GPU Worker Pool             │   │
│  │ - Listen for jobs       │  │ - CUDA/ROCm execution       │   │
│  │ - Download models       │  │ - Model caching             │   │
│  │ - Register with network │  │ - Performance metrics       │   │
│  │ - Post completion proof │  │ - Hardware optimization     │   │
│  └─────────────────────────┘  └─────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Storage Integration (IPFS / Arweave)                     │   │
│  │ - Model artifacts  - Input datasets  - Output results    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Details

### Smart Contract Layer
- **JobRegistry**: Stores job metadata, tracks execution state, validates completion proofs
- **ProviderRegistry**: Manages provider stakes, reputation scores, and slashing conditions
- **PaymentManager**: Handles token escrow, dispute resolution, and settlement logic
- **NRC Token**: ERC-20 implementation for incentive distribution

### Coordination Layer
- **Job Coordinator**: Matches compute jobs to available providers based on requirements
- **Matchmaker**: Optimizes assignments for latency, cost, and reliability
- **Proof Verifier**: Validates cryptographic proofs of computation without re-running jobs

### Compute Provider Layer
- **Provider Node**: P2P daemon running on each GPU owner's machine
- **GPU Worker Pool**: Manages CUDA/ROCm kernels, memory, and concurrent job execution
- **Storage Integration**: Fetches models from IPFS, posts results to Arweave

### API Gateway
- REST/GraphQL endpoints for job submission, status tracking, and earnings queries
- Authentication via wallet signatures
- Rate limiting and usage quotas

## Data Flow

### Job Execution Pipeline
```
1. User submits job (model, inputs, hardware requirements)
   ↓
2. API Gateway validates and stores job metadata on JobRegistry
   ↓
3. Matchmaker selects optimal provider based on capabilities & cost
   ↓
4. Provider node receives job, downloads model and inputs from storage
   ↓
5. Provider executes inference/training on GPU worker
   ↓
6. Provider posts completion proof (hash of outputs + execution trace)
   ↓
7. Proof Verifier validates proof on-chain
   ↓
8. PaymentManager settles token transfer to provider
   ↓
9. User downloads results from storage
```

## Security Model

- **Stake-based accountability**: Providers must stake NRC to participate; misbehavior triggers slashing
- **Cryptographic proof of work**: zk-SNARKs validate computation without re-execution
- **Escrow mechanism**: Payments held in smart contract until proof verification
- **Reputation system**: On-chain reputation score influences job matching and rewards
- **Dispute resolution**: Multi-signature timelock for contested proofs

## Scalability Considerations

- **Layer 2 integration**: Payment settlement batched on Polygon/Arbitrum for cost efficiency
- **Off