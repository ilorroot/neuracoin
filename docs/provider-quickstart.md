# Provider Onboarding Quickstart

This guide walks GPU owners through the steps required to become a NeuraCoin compute provider: verifying hardware, installing the client, staking NRC, running the node daemon, and monitoring earnings.

For deeper background on economics and use cases, see the [Provider section of the FAQ](./faq.md#for-gpu-providers).

---

## 1. Hardware Requirements

**Minimum**

- NVIDIA GPU with 4 GB+ VRAM (RTX 3060, RTX 4060 Ti, A6000, etc.)
- 8 GB system RAM
- Stable internet connection (10+ Mbps up/down)
- Linux, Windows, or macOS
- ~50 GB free disk for model caches

**Recommended**

- NVIDIA A100 / H100 / RTX 4090 for competitive earnings
- 32 GB+ system RAM
- Gigabit network connection
- Dedicated PSU with UPS

Before continuing, confirm your GPU is visible to the driver:

bash
nvidia-smi


If `nvidia-smi` fails, install the appropriate CUDA drivers before proceeding — the node client will refuse to register a provider it cannot benchmark.

---

## 2. Install the NeuraCoin Client

Clone the repo and install Python dependencies (Python 3.10+ required):

bash
git clone https://github.com/YOUR_USERNAME/neuracoin
cd neuracoin
pip install -r requirements.txt


Verify the CLI is available:

bash
python cli/neuracoin.py --help


---

## 3. Configure Environment

The CLI and node client read connection details from environment variables:

bash
export NEURACOIN_RPC_URL="https://sepolia.infura.io/v3/<YOUR_KEY>"
export NEURACOIN_TOKEN_ADDRESS="0x..."        # NRC ERC-20
export NEURACOIN_REGISTRY_ADDRESS="0x..."     # JobRegistry
export NEURACOIN_PRIVATE_KEY="0x..."          # provider signing key


Current testnet addresses are published in `docs/architecture.md` and on the [NeuraCoin status page](https://status.neuracoin.example).

---

## 4. Fund and Stake NRC

Providers must lock NRC as collateral through `JobRegistry.registerProvider`. The stake is slashable if you drop jobs or produce invalid results.

1. Acquire testnet NRC from the faucet (see `docs/faq.md`).
2. Approve the `JobRegistry` to move your stake:

   bash
   python cli/neuracoin.py provider approve --amount 1000
   

3. Register with your hardware specs and stake amount:

   bash
   python cli/neuracoin.py provider register \
     --stake 1000 \
     --gpu-model "RTX 4090" \
     --vram-gb 24 \
     --endpoint "https://my-node.example:8443"
   

Under the hood this calls:

solidity
// contracts/JobRegistry.sol
function registerProvider(
    uint256 stakeAmount,
    string calldata hardwareSpec,
    string calldata endpoint
) external;


The transaction transfers `stakeAmount` NRC from your wallet into the registry escrow and marks the provider as `ACTIVE`.

---

## 5. Start the Node Client

The node client (`cli/node_client.py`) polls the JobRegistry, accepts assigned jobs, executes them on your GPU, and submits results for settlement.

bash
python cli/node_client.py \
  --provider-address $NEURACOIN_PROVIDER_ADDRESS \
  --poll-interval 5


Expected startup output:


[NeuraCoin] Node client starting…
[NeuraCoin] Provider 0xabc… ACTIVE, stake=1000 NRC
[NeuraCoin] Polling JobRegistry every 5s


Run the client under `systemd`, `tmux`, or a process supervisor so it survives reboots. A sample unit file lives in `docs/deployment/neuracoin-node.service`.

---

## 6. Monitor Earnings

### CLI

Query accumulated NRC rewards and job counts:

bash
python cli/neuracoin.py status --provider $NEURACOIN_PROVIDER_ADDRESS
python cli/neuracoin.py jobs --provider $NEURACOIN_PROVIDER_ADDRESS --limit 20


### Local node stats

The node client tracks per-session metrics (see `NodeStats` in `cli/node_client.py`): jobs completed, jobs failed, NRC earned, uptime, average job duration. Stats are logged on every poll cycle and persisted to `~/.neuracoin/stats.json`.

### Dashboard

The web dashboard (`dashboard/index.html`) exposes a provider view once you connect the wallet used for registration. It surfaces:

- Live job assignments
- Rolling 24h / 7d earnings
- Reputation score
- Slash / dispute events

---

## 7. Unregistering and Withdrawing Stake

To exit the network cleanly:

bash
python cli/neuracoin.py provider deregister


Stake is released after the cooldown period defined in `JobRegistry` (default: 7 days on testnet), during which any outstanding disputes must resolve.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `registerProvider` reverts with `InsufficientStake` | Below `MIN_PROVIDER_STAKE` | Increase `--stake` |
| `registerProvider` reverts with `ERC20: insufficient allowance` | Approval step skipped | Run `provider approve` first |
| Node client logs `no jobs assigned` for hours | Endpoint unreachable from dispatcher | Check firewall / TLS cert on `--endpoint` |
| Rewards not increasing | Jobs failing verification | Inspect `jobs --status DISPUTED` |

For further help, open an issue on GitHub or ask in the `#providers` channel of the community Discord.
