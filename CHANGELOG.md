# Changelog

All notable changes to NeuraCoin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-15

First tagged pre-release. This version establishes the protocol foundations
(documentation, tokenomics, core contracts, and Python client scaffolding)
in preparation for a public testnet deployment in v0.2.

### Added

#### Documentation
- Whitepaper draft covering protocol motivation, actors (Users, Providers,
  Validators), and the Proof-of-Compute settlement flow (`docs/`).
- System architecture document describing the User → API Gateway →
  Coordinator → Provider → Settlement layers (`docs/architecture.md`).
- Tokenomics model: 1,000,000,000 NRC total supply with the 40/20/20/15/5
  distribution (compute rewards / ecosystem / team / public sale / reserve).
- Provider and requester FAQ (`docs/faq.md`).
- 12-month roadmap with quarterly milestones (`docs/roadmap.md`).

#### Smart contracts (`contracts/`)
- `NeuraCoin.sol` — ERC-20 NRC token with a 400M NRC compute-rewards pool
  minted lazily by an authorized reward emitter, owner-pausable transfers,
  and holder-side `burn`.
- `JobRegistry.sol` — provider registration with stake, job submission with
  NRC escrow, assignment, completion verification, and dispute flagging.
- `Governance.sol` — proposal creation, voting, queueing, cancellation, and
  execution scaffolding for NRC-weighted on-chain governance.

#### Python clients (`cli/`)
- `neuracoin.py` — CLI entrypoint exposing `status`, `price`, `jobs`, and
  `provider` subcommands; reads contract addresses and RPC endpoint from
  environment variables.
- `node_client.py` — compute-node client scaffold (`ComputeNodeClient`,
  `Job`, `NodeStats`) with a polling loop and earnings tracking against a
  mocked job dispatcher.

#### Tests (`tests/`)
- `test_token.py` — mint / transfer / burn / allowance coverage against a
  mock NRC token.
- `test_registry.py` — job lifecycle coverage
  (PENDING → ACCEPTED → RUNNING → COMPLETED) plus validation errors.

#### Tooling
- Pinned Python dependencies (`requirements.txt`).
- Static dashboard shell (`dashboard/index.html`) with wallet-connect UI
  placeholder.

### Known gaps / deferred to v0.2
- **No testnet deployment.** Contracts compile and are unit-tested locally
  but have not been deployed to Sepolia or any public network. No canonical
  contract addresses exist yet.
- **No external audit.** Only internal review has been performed; the
  contracts must not be used with real value.
- **Governance execution is a stub.** `Governance.sol` emits events on
  `executeProposal` but does not yet mutate protocol parameters; a
  parameters contract needs to be wired in.
- **Node client uses a mock dispatcher.** `cli/node_client.py` simulates
  job polling and execution; integration with the on-chain `JobRegistry`
  and a real GPU execution backend is pending.
- **Dashboard is frontend-only.** `dashboard/index.html` has no JavaScript
  for wallet connection, contract reads, or job monitoring.
- **No proof-of-compute verification.** Job completion currently trusts
  the assigned provider; validator network and result attestation are
  unimplemented.
- **No CI pipeline.** Tests run locally via `pytest` only.

### Changed
- N/A (initial release).

### Deprecated
- N/A.

### Removed
- N/A.

### Fixed
- N/A.

### Security
- Owner-pausable transfers on `NeuraCoin.sol` for emergency response.
- Reward minting gated to a single authorized emitter address
  (the `JobRegistry`) via `setRewardEmitter`.
- Provider stake requirement in `JobRegistry.sol` to disincentivize
  malicious job acceptance.
- Escrowed job payments released only on verified completion or returned
  on dispute resolution.
- **Reminder:** these controls are unaudited; see *Known gaps* above.
