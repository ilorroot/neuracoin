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
│  │ Job Coordinator │  │ Matcher      │  │ Result Verifier  │   │
│  │ - Queue mgmt    │  │ - Match jobs │  │ - Verify proofs  │   │
│  │ - Task dispatch │  │   to GPUs    │  │ - Detect fraud   │   │
│  └──────┬──────────┘  └──────┬───────┘  └────────┬─────────┘   │
│         │                    │                   │              │
└─────────┼────────────────────┼───────────────────┼──────────────┘
          │                    │                   │
┌─────────┼────────────────────┼───────────────────┼──────────────┐
│         │       PROVIDER NETWORK LAYER                          │
│         │                    │                   │              │
│  ┌──────▼──────────┐  ┌──────▼───────┐  ┌──────▼────────┐     │
│  │ Provider Node 1 │  │Provider Node2 │  │Provider Node N│     │
│  │ ┌────────────┐  │  │ ┌────────────┐│  │┌────────────┐│     │
│  │ │GPU Executor│  │  │ │GPU Executor││  ││GPU Executor││     │
│  │ │ - CUDA     │  │  │ │ - CUDA     ││  ││ - CUDA     ││     │
│  │ │ - Runtime  │  │  │ │ - Runtime  ││  ││ - Runtime  ││     │
│  │ └────────────┘  │  │ └────────────┘│  │└────────────┘│     │
│  │ ┌────────────┐  │  │ ┌────────────┐│  │┌────────────┐│     │
│  │ │Attestation │  │  │ │Attestation ││  ││Attestation ││     │
│  │ │ Service    │  │  │ │ Service    ││  ││ Service    ││     │
│  │ └────────────┘  │  │ └────────────┘│  │└────────────┘│     │
│  └─────────────────┘  └────────────────┘  └───────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │                    │                   │
          └────────────────────┼───────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                    STORAGE LAYER                               │
├──────────────────────────────┼──────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ IPFS/Arweave │  │ State DB     │  │ Blockchain   │          │
│  │ - Models     │  │ - Job state  │  │ - Immutable  │          │
│  │ - Datasets   │  │ - Provider   │  │ - Settlement │          │
│  │ - Results    │  │   profiles   │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Description

### User Layer
- **Web UI**: User-friendly dashboard for job submission and monitoring
- **CLI Tool**: Command-line interface for advanced users and automation
- **SDK/Library**: Python, JavaScript libraries for programmatic access

### API Gateway Layer
- REST API endpoints for all operations
- GraphQL support for flexible querying
- Authentication and rate limiting
- Request validation and routing

### Smart Contract Layer (Ethereum L1/L2)

#### TokenERC20 (NRC Token)
- Standard ERC-20 token for payments and rewards
- Minting/burning for system economics

#### JobRegistry
- Register new