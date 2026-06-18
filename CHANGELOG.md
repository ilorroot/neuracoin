# Changelog

All notable changes to NeuraCoin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-02-26

Hardening release focused on closing the v0.1 gaps that blocked testnet
bring-up: governance execution is now functional, the Python clients have
real polling and CLI wiring, and the test suite has been expanded to cover
the contract paths that were previously only exercised on the happy path.

### Added

#### Smart contracts (`contracts/`)
- `Governance.sol` — `executeProposal` now performs real state changes
  against a wired-in protocol parameters contract (fee rate, minimum
  provider stake, dispute window) instead of only emitting events.
  Execution is gated on the queued state and a timelock delay.
- Governance test suite covering proposal creation, vote tallying,
  quorum enforcement, queueing, cancellation, and end-to-end execution
  against the parameters contract.

#### Tests (`tests/`)
- `test_token.py` — added coverage for `emitReward` (authorized emitter,
  unauthorized caller rejection, pool exhaustion) and the pause/unpause
  flows (transfers blocked while paused, owner-only control).
- `test_registry.py` — added dispute-resolution tests (flag, resolve in
  favor of requester vs. provider, escrow refund vs. release) and
  provider-stake tests (minimum stake enforcement, stake slashing on
  lost disputes, unstake after cooldown).
- `test_node_client.py` — new suite covering the `ComputeNodeClient`
  polling loop, job acceptance, earnings accumulation, and `NodeStats`
  aggregation.
- `test_cli.py` — argument-parsing tests for every `neuracoin.py`
  subcommand (`status`, `price`, `jobs`, `provider`) including required
  flags and error exit codes.

#### Python clients (`cli/`)
- `node_client.py` — replaced the mock dispatcher with a real polling
  loop that queries `JobRegistry` over JSON-RPC, filters jobs by
  declared GPU capability, submits acceptance transactions, and
  persists `NodeStats` to disk between runs.
- `neuracoin.py` — subcommands are now wired to concrete handlers:
  `status` reads on-chain protocol counters, `price` queries the NRC
  token contract, `jobs list/show/submit` interact with `JobRegistry`,
  and `provider register/stake/unstake` call the matching contract
  methods. Exit codes and `--json` output are standardized.

#### Documentation
- `docs/deployment.md` — deployment and testnet bring-up guide covering
  environment setup, contract deployment order (`NeuraCoin` →
  `JobRegistry` → `Governance`), reward-emitter wiring, Sepolia
  configuration, and post-deploy verification checklist.

### Changed
- `cli/node_client.py` no longer simulates job execution; the GPU
  execution hook is now a pluggable callable so integrators can supply
  their own runner.
- `cli/neuracoin.py` reads contract addresses from a single
  `NEURACOIN_CONFIG` file in addition to environment variables, with
  env vars taking precedence.

### Fixed
- `JobRegistry.sol` — dispute flagging now correctly locks provider
  stake until resolution; previously the stake could be withdrawn
  mid-dispute.
- `NeuraCoin.sol` — `emitReward` reverts cleanly when the 400M NRC
  compute-rewards pool is exhausted instead of silently minting zero.

### Known gaps / deferred to v0.3
- **No external audit.** Internal review and expanded tests only; the
  contracts must still not be used with real value.
- **No mainnet deployment.** Testnet (Sepolia) bring-up is documented
  and scripted, but mainnet deployment is gated on the audit.
- **Dashboard is still static.** `dashboard/index.html` does not yet
  call the deployed contracts; wallet-connect and live job views are
  planned for v0.3.

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
