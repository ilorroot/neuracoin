# NeuraCoin Tokenomics

## Overview

NeuraCoin (NRC) is the native utility token of the NeuraCoin protocol. It serves three primary functions: payment for compute jobs, staking collateral for network participants, and governance voting power.

---

## Supply

| Parameter     | Value                  |
|---------------|------------------------|
| Total Supply  | 1,000,000,000 NRC      |
| Decimals      | 18                     |
| Standard      | ERC-20 (EVM)           |
| Inflation     | None (fixed supply)    |

---

## Allocation

| Bucket                  | Amount (NRC)   | % of Supply | Notes                            |
|-------------------------|----------------|-------------|----------------------------------|
| Compute Rewards         | 400,000,000    | 40%         | Emitted over ~10 years (halving) |
| Ecosystem & Grants      | 200,000,000    | 20%         | Developer grants, partnerships   |
| Team & Advisors         | 200,000,000    | 20%         | 4-year vest, 1-year cliff        |
| Public Sale             | 150,000,000    | 15%         | TGE liquidity                    |
| Reserve                 | 50,000,000     | 5%          | Emergency / protocol-owned       |

---

## Vesting Schedule

Team and advisor tokens follow a **4-year vesting schedule with a 1-year cliff**:

| Recipient Category | Amount (NRC) | Cliff (months) | Vest Duration (months) | Monthly Release | Unlock Date |
|--------------------|--------------|----------------|------------------------|-----------------|-------------|
| Core Team          | 100,000,000  | 12             | 48                     | 2,083,333       | TGE + 12mo  |
| Advisors           | 50,000,000   | 12             | 48                     | 1,041,667       | TGE + 12mo  |
| Early Employees    | 50,000,000   | 12             | 48                     | 1,041,667       | TGE + 12mo  |

**Vesting Details:**
- **Cliff:** No tokens are released for the first 12 months after TGE (Token Generation Event)
- **Linear Vesting:** After cliff, tokens vest linearly over remaining 36 months
- **No Acceleration:** Vesting schedules are non-accelerating, even in acquisition scenarios
- **Locked Tokens:** Vesting tokens cannot be transferred, staked, or used for governance until released
- **Smart Contract Enforcement:** Vesting is enforced by immutable smart contracts

---

## Emission Schedule

Compute rewards follow a **halving schedule** every 24 months:

| Period   | Rate (NRC / compute-hour) | Cumulative Emitted |
|----------|--------------------------|-------------------|
| Year 1-2 | 10 NRC                   | ~87.6M            |
| Year 3-4 | 5 NRC                    | ~131.4M           |
| Year 5-6 | 2.5 NRC                  | ~153.3M           |
| Year 7+  | Halves every 2 years     | → 400M total cap  |

---

## Staking Requirements

| Role              | Minimum Stake  | Slashing Condition              |
|-------------------|----------------|----------------------------------|
| Compute Provider  | 1,000 NRC      | Submitting fraudulent output     |
| Validator         | 10,000 NRC     | Dishonest verification           |

Slashed tokens are sent to the community treasury.

---

## Fee Structure

Every compute job pays a **0.1% protocol fee** on the job stake:

- 50% → Validator rewards (distributed proportionally to stake)
- 50% → Community treasury (governed by NRC holders)

---

## Governance

NRC holders can vote on:
- Protocol fee adjustments
- Staking requirement changes
- Emission schedule modifications
- Treasury fund allocation
- Smart contract upgrades

Voting power is proportional to staked NRC balance. Minimum proposal threshold: 100,000 NRC.

---

## Value Accrual

NRC accrues value through:
1. **Required for job payment** — all compute jobs must be paid in NRC
2. **Staking lock-up** — providers and validators lock NRC, reducing circulating supply
3. **Fee burn** — a portion of protocol fees may be burned via governance vote
4. **Growing demand** — as AI compute demand grows, protocol usage (and NRC demand) grows proportionally

---

<!-- Last reviewed: 2026-04-12 -->

## Contributing

Pull requests are welcome. For