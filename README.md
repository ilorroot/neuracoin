# NeuraCoin (NRC) ⚡🧠

> **Decentralized AI Compute Protocol** — Rent your idle GPU. Train the future.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: In Development](https://img.shields.io/badge/Status-In%20Development-blue.svg)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)]()

---

## What is NeuraCoin?

NeuraCoin is a decentralized protocol that connects **AI researchers and developers** who need compute power with **GPU owners** who have idle hardware. Contributors earn NRC tokens for every verified compute job they complete.

Think of it as **Airbnb for AI compute** — but trustless, transparent, and on-chain.

---

## The Problem

Training AI models is expensive. A single GPT-scale training run can cost millions of dollars on centralized cloud providers (AWS, GCP, Azure). Meanwhile, billions of dollars worth of GPU hardware sits idle in gaming rigs, workstations, and data centers around the world.

NeuraCoin bridges this gap.

---

## How It Works

```
[Job Requester]  →  submits training job + NRC stake
      ↓
[NeuraCoin Protocol]  →  matches job to available compute nodes
      ↓
[Compute Provider]  →  runs the job, submits proof-of-work
      ↓
[Validator Network]  →  verifies output integrity
      ↓
[Settlement]  →  NRC released to provider, job result to requester
```

---

## Token Economics

| Parameter        | Value              |
|------------------|--------------------|
| Token Symbol     | NRC                |
| Total Supply     | 1,000,000,000 NRC  |
| Consensus        | Proof of Compute   |
| Block Time       | ~3 seconds         |
| Job Fee          | 0.1% protocol fee  |

### Supply Distribution
- 40% — Compute provider rewards (emission over 10 years)
- 20% — Ecosystem & grants
- 20% — Team & advisors (4-year vest)
- 15% — Public sale
- 5%  — Reserve

---

## Repository Structure

```
neuracoin/
├── contracts/        # Solidity smart contracts
├── cli/              # Python CLI for interacting with the network
├── dashboard/        # Web dashboard for monitoring compute jobs
├── docs/             # Whitepaper, architecture, tokenomics
├── tests/            # Test suite
└── README.md
```

---

## Roadmap

- [x] Protocol design & whitepaper
- [x] Tokenomics model
- [ ] Smart contract development (ERC-20 + job registry)
- [ ] Compute node client (Python)
- [ ] Testnet launch
- [ ] Audit & mainnet

---

## Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/neuracoin
cd neuracoin
pip install -r requirements.txt
python cli/neuracoin.py --help
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

MIT © NeuraCoin Protocol
