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
| Compute Provider  | 10,000 NRC     | Downtime >24h or job failure    |
| Validator         | 50,000 NRC     | Byzantine behavior or slashing  |
| Delegator         | 100 NRC        | No slashing (delegation only)    |