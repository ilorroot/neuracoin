# Changelog

All notable changes to NeuraCoin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2024-03-25

Testnet-readiness release that finishes the contract hardening and Python
tooling work started in v0.2 and ships the operational documentation
needed to bring the protocol up on Sepolia. With this release every
subsystem (token, registry, governance, node client, CLI) is covered by
tests and wired to real on-chain calls.

### Added

#### Smart contracts (`contracts/`)
- `NeuraCoin.sol` — test coverage for `emitReward` (authorized emitter
  path, unauthorized caller rejection, reward pool exhaustion) and the
  pause/unpause flows (transfers blocked while paused, owner-only
  control of the pause switch).
- `JobRegistry.sol` — test coverage for the dispute path (`flagDispute`,
  resolution in favor of requester vs. provider, escrow refund vs.
  release) and for provider stake mechanics (minimum stake enforcement
  on `registerProvider`, stake slashing on lost disputes, unstake after
  the cooldown window).
- `Governance.sol` — `executeProposal` now performs real state changes
  against a wired-in protocol parameters contract (fee rate, minimum
  provider stake, dispute window) instead of only emitting events.
  Execution is gated on the queued state and a timelock delay.
- Governance test suite covering proposal creation, vote tallying,
  quorum enforcement, queueing, cancellation, and end-to-end execution
  against the parameters contract.

#### Python clients (`cli/`)
- `node_client.py` — replaced the mock dispatcher with a real polling
  loop that queries `JobRegistry` over JSON-RPC, filters jobs by
  declared GPU capability, submits acceptance transactions, and
  persists `NodeStats` to disk between runs. The GPU execution hook is
  now a pluggable callable so integrators can supply their own runner.
- `neuracoin.py` — subcommands are wired to concrete handlers:
  `status` reads on-chain protocol counters, `price` queries the NRC
  token contract, `jobs list/show/submit` interact with `JobRegistry`,
  and `provider register/stake/unstake` call the matching contract
  methods. Exit codes and `--json` output are standardized.

#### Tests (`tests/`)
- `test_node_client.py` — new suite covering the `ComputeNodeClient`
  polling loop, job acceptance, earnings accumulation, and `NodeStats`
  aggregation across restarts.
- `test_cli.py` — argument-parsing tests for every `neuracoin.py`
  subcommand (`status`, `price`, `jobs`, `provider`) including required
  flags, mutually exclusive options, and error exit codes.

#### Documentation
- `docs/deployment.md` — deployment and testnet bring-up guide covering
  environment setup, contract deployment order (`NeuraCoin` →
  `JobRegistry` → `Governance`), reward-emitter wiring, Sepolia RPC and
  faucet configuration, and a post-deploy verification checklist.

### Changed
- `cli/node_client.py` no longer simulates job execution; jobs are
  dispatched through the pluggable runner and earnings reflect on-chain
  settlement events.
- `cli/neuracoin.py` reads contract addresses from a single
  `NEURACOIN_CONFIG` environment variable (with per-address overrides
  retained for local development) so the same binary works against
  testnet and mainnet without code changes.

### Fixed
- `JobRegistry.sol` — escrow accounting no longer underflows when a
  dispute is resolved in favor of the requester after a partial
  provider payout was queued.
- `Governance.sol` — queued proposals can no longer be executed twice;
  the executed flag is now checked before applying parameter changes.

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
  `N