# NeuraCoin Tokenomics

## Overview

NeuraCoin (NRC) is the native utility token of the NeuraCoin protocol. It serves three primary functions: payment for compute jobs, staking collateral for network participants, and governance voting power.

This document is the canonical specification of NRC tokenomics. The values defined here are the source of truth that downstream smart contracts (`contracts/NeuraCoin.sol`, `contracts/JobRegistry.sol`, `contracts/Governance.sol`) must encode.

---

## Supply

| Parameter     | Value                  |
|---------------|------------------------|
| Token Name    | NeuraCoin              |
| Symbol        | NRC                    |
| Total Supply  | 1,000,000,000 NRC      |
| Decimals      | 18                     |
| Standard      | ERC-20 (EVM)           |
| Inflation     | None (fixed cap)       |
| Mint Authority| Disabled after TGE + rewards pool minted lazily by `JobRegistry` up to the 400M cap |

The total supply is hard-capped at **1,000,000,000 NRC**. No additional tokens can ever be minted beyond this cap; the compute rewards pool is pre-allocated within the cap and released over time according to the emission schedule below.

---

## Allocation

| Bucket                  | Amount (NRC)   | % of Supply | Notes                                         |
|-------------------------|----------------|-------------|-----------------------------------------------|
| Compute Rewards         | 400,000,000    | 40%         | Emitted over ~10 years (halving every 2 yrs)  |
| Ecosystem & Grants      | 200,000,000    | 20%         | Developer grants, partnerships, integrations  |
| Team & Advisors         | 200,000,000    | 20%         | 4-year vest, 1-year cliff                     |
| Public Sale             | 150,000,000    | 15%         | TGE liquidity, exchange listings              |
| Reserve                 |  50,000,000    |  5%         | Emergency / protocol-owned liquidity          |
| **Total**               |**1,000,000,000**| **100%**   |                                               |

### Allocation Notes

- **Compute Rewards (400M):** Held by the `NeuraCoin` token contract and minted on demand by the authorized `rewardEmitter` (the `JobRegistry` contract) via `emitReward(provider, amount)`. The contract MUST enforce that cumulative emissions never exceed 400,000,000 NRC.
- **Ecosystem & Grants (200M):** Held by a multisig-controlled treasury. Released via on-chain governance proposals (`Governance.createProposal`).
- **Team & Advisors (200M):** Locked in a vesting contract; see schedule below.
- **Public Sale (150M):** Minted to the sale contract at TGE; unsold tokens revert to the Reserve bucket.
- **Reserve (50M):** Multisig-controlled, intended for emergency liquidity, audits, and unforeseen protocol needs.

---

## Vesting Schedule

Team and advisor tokens follow a **4-year linear vesting schedule with a 1-year cliff**. Ecosystem and Reserve buckets are not subject to time-based vesting but are gated by multisig/governance.

| Recipient Category | Amount (NRC) | Cliff (months) | Vest Duration (months) | Monthly Release | First Unlock |
|--------------------|--------------|----------------|------------------------|-----------------|--------------|
| Core Team          | 100,000,000  | 12             | 48                     | 2,777,778       | TGE + 12mo   |
| Advisors           |  50,000,000  | 12             | 48                     | 1,388,889       | TGE + 12mo   |
| Early Employees    |  50,000,000  | 12             | 48                     | 1,388,889       | TGE + 12mo   |
| **Total Vested**   | **200,000,000** |             |                        |                 |              |

**Monthly release** is computed as `amount / 36` (the 36 months *after* the cliff). At the cliff (month 12), no tokens are released; from month 13 through month 48, an equal monthly tranche unlocks.

### Vesting Rules

- **Cliff:** No tokens are released for the first 12 months after TGE (Token Generation Event).
- **Linear Vesting:** After the cliff, tokens vest linearly over the remaining 36 months.
- **No Acceleration:** Vesting schedules are non-accelerating, even in acquisition scenarios.
- **Locked Tokens:** Vesting tokens cannot be transferred, staked, or used for governance until released.
- **Smart Contract Enforcement:** Vesting is enforced by an immutable vesting contract deployed alongside `NeuraCoin.sol`.
- **Revocability:** Advisor and Early Employee schedules MAY be revoked by governance for cause; Core Team schedules are non-revocable.

---

## Emission Schedule (Compute Rewards)

Compute rewards are emitted to GPU providers as `JobRegistry.completeJob` settles successful jobs. Emission follows a **halving schedule** every 24 months, modeled on a network target of ~1,000,000 compute-hours per year at TGE growing to ~10,000,000 by year 4.

| Period      | Rate (NRC / compute-hour) | Period Emission | Cumulative Emitted |
|-------------|---------------------------|-----------------|--------------------|
| Year 1–2    | 10.0                      | ~120,000,000    | ~120,000,000       |
| Year 3–4    |  5.0                      | ~140,000,000    | ~260,000,000       |
| Year 5–6    |  2.5                      |  ~80,000,000    | ~340,000,000       |
| Year 7–8    |  1.25                     |  ~40,000,000    | ~380,000,000       |
| Year 9–10   |  0.625                    |  ~15,000,000    | ~395,000,000       |
| Year 11+    | Halves every 2 years      |  Asymptotic     | → 400,000,000 cap  |

### Emission Rules

- The 400,000,000 NRC cap is **absolute**. Once cumulative emissions reach this value, `emitReward` MUST revert.
- The per-compute-hour rate is set at deployment and updated at each 2-year halving epoch by the `Governance` contract calling a parameter-setter on `JobRegistry`.
- Unemitted rewards from underutilized periods do **not** roll forward; the cap is a ceiling, not a floor.

---

## Fee & Burn Mechanics

Every completed job in `JobRegistry` settles in NRC. The protocol applies a **0.5% protocol fee** on the job payment (the requester's stake), split as follows:

| Component        | Share of Fee | Destination                                   |
|------------------|--------------|-----------------------------------------------|
| Burn             | 50%          | Sent to `address(0)` via `NeuraCoin.burn`     |
| Treasury         | 30%          | Ecosystem & Grants multisig                   |
| Validator Reward | 20%          | Pro-rata to validators that verified the job  |

### Fee Flow Per Job


requester  ──stake (P)──>  JobRegistry (escrow)
                                  │
                  ┌─────────────┼─────────────────────�
                  ▼                                       ▼
            provider: 99.5% · P              protocol fee: 0.5% · P
                                                          │
                                  ┌──────────────────────┼────────────────────────�
                                  ▼                       ▼                       ▼
                            burn (50%)             treasury (30%)         validators (20%)


### Burn Specification

- The burn portion is executed atomically inside `JobRegistry.completeJob` by calling `NeuraCoin.burn(burnAmount)`.
- Burned tokens reduce `totalSupply` permanently; they are **not** recyclable into the rewards pool.
- Burn events MUST be indexed via the standard `Transfer(from, address(0), amount)` event for explorer compatibility.

### Disputed Jobs

For jobs flagged via `JobRegistry.flagDispute`:

- The escrowed payment remains locked until dispute resolution.
- If the provider is found at fault, their stake is slashed (see Staking) and the requester is refunded in full (no fee charged).
- If the requester's dispute is rejected, the standard fee + payment flow proceeds and the requester forfeits a 10% dispute bond.

---

## Staking Requirements

| Role              | Minimum Stake (NRC) | Lock Period | Slashing Condition                                      |
|-------------------|---------------------|-------------|---------------------------------------------------------|
| Compute Provider  | 1,000               | 14 days     | Failed/fraudulent job output, downtime > 5%             |
| Validator         | 10,000              | 30 days     | Incorrect verification vote (vs. supermajority)         |
| Governance Voter  | 100                 | Proposal +7d| Vote-buying detected via on-chain forensics             |

### Slashing Distribution

When a stake is slashed:
- 50% is **burned** (sent to `address(0)`).
- 50% is awarded to the harmed counterparty (job requester for provider slashing; honest validators for validator slashing).

---

## Governance

- **Voting Power:** 1 NRC = 1 vote (snapshot-based, taken at proposal creation).
- **Proposal Threshold:** 1,000,000 NRC (0.1% of supply) required to create a proposal.
- **Quorum:** 4% of circulating supply must participate for a proposal to pass.
- **Timelock:** 48 hours between proposal queue and execution.
- **Scope:** Governance can adjust fee percentages (within bounds: 0%–2%), emission rate parameters, treasury disbursements, and validator set membership. Governance **cannot** alter the 1B total supply cap or the 400M rewards cap.

---

## Summary

NeuraCoin's tokenomics are designed for long-term sustainability:

1. **Fixed supply** (1B NRC) prevents inflationary dilution.
2. **Halving emissions** front-load rewards to bootstrap the network, then taper.
3. **Deflationary fees** (50% burn) tie token value to protocol usage.
4. **Multi-year vesting** aligns team incentives with long-term protocol health.
5. **Stake-based security** ensures economic skin-in-the-game for providers and validators.

These parameters are encoded in the contracts implemented in subsequent v0.1 tasks and may be tuned only via the on-chain governance process described above.
