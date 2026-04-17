# NeuraCoin (NRC) FAQ

## General Questions

### What is NeuraCoin?

NeuraCoin (NRC) is a decentralized protocol that enables GPU owners to monetize their computing resources by running AI inference and training jobs. It creates a peer-to-peer marketplace where job requesters can access affordable GPU compute and providers earn tokens for their contributions.

### How does NeuraCoin work?

1. **GPU Providers** register their hardware on the network and make it available for AI workloads
2. **Job Requesters** submit computational tasks (inference, fine-tuning, etc.) with specified requirements and budgets
3. **Smart Contracts** match jobs to suitable providers, execute work, and distribute rewards
4. **NRC Tokens** incentivize participation and serve as the settlement mechanism

### Is NeuraCoin decentralized?

Yes. The protocol operates on a decentralized blockchain (Ethereum mainnet) with no central authority controlling job allocation, pricing, or token distribution. All participants interact directly through smart contracts.

### What are the use cases for NeuraCoin?

- Running open-source LLM inference (Llama 2, Mistral, etc.)
- Fine-tuning models on custom datasets
- Batch processing for computer vision tasks
- Real-time inference for applications
- Training small-to-medium models
- Distributed RAG (Retrieval-Augmented Generation) pipelines

---

## For GPU Providers

### How do I earn NRC tokens?

1. **Register your GPU(s)** on the NeuraCoin network with hardware specifications
2. **Run the provider daemon** to accept and execute jobs
3. **Complete AI workloads** submitted by job requesters
4. **Receive NRC tokens** upon successful job completion and verification

### What hardware do I need?

**Minimum Requirements:**
- NVIDIA GPU with 4GB+ VRAM (RTX 3060, RTX 4060 Ti, A6000, etc.)
- 8GB system RAM
- Stable internet connection (10+ Mbps)
- Linux/Windows/macOS

**Recommended:**
- NVIDIA A100, H100, or RTX 4090 for competitive earnings
- 32GB+ system RAM for larger models
- Gigabit network connection
- Dedicated power supply

### How much can I earn?

Earnings depend on:
- **GPU tier** (higher VRAM/compute = higher rates)
- **Utilization** (percentage of time running jobs)
- **Model complexity** (longer jobs = more tokens)
- **Network competition** (supply/demand dynamics)

**Example estimates:**
- RTX 3060: $2-5/day
- RTX 4090: $10-20/day
- A100: $30-50/day

### How do I get started as a provider?

```bash
# 1. Install NeuraCoin provider
pip install neuracoin-provider

# 2. Configure your setup
neuracoin-provider init --gpu-memory 24000 --region us-east

# 3. Start earning
neuracoin-provider start
```

See [Provider Setup Guide](./provider-setup.md) for detailed instructions.

### What is the revenue split?

- **90%** of job payment goes to GPU provider
- **10%** to NeuraCoin protocol (maintenance, development)

### Can I run multiple GPUs?

Yes. You can register multiple GPUs under one account and the daemon will load-balance jobs across them. Each GPU is tracked independently for earnings and performance metrics.

### How do I withdraw my earnings?

```bash
# Check your balance
neuracoin-provider balance

# Withdraw to your wallet
neuracoin-provider withdraw --amount 100 --wallet 0x...

# Earnings are transferred directly to your Ethereum wallet address
```

Withdrawals are processed within 24 hours via smart contract settlement.

### What happens if a job fails?

- **Provider-side failures** (hardware crash, disconnect): Job is reassigned, you receive partial payment (if work was completed)
- **Invalid results**: Smart contract verification detects errors; you don't receive payment and job is reassigned
- **Network issues**: Automatic reconnection with up to 5-minute grace period before reassignment

### Is there a minimum uptime requirement?

Providers should maintain **80%+ availability** per week. Consistent downtime may result in lower job prioritization.

---

## For Job Requesters

### How do I submit a job?

```python
from neuracoin import JobClient

client = JobClient(api_key="your_api_key")

job = client.submit_job(
    model="meta-llama/Llama-2-7b",
    task_type="inference",
    input_data={"prompt": "What is AI?"},
    gpu_requirement={"min_vram_gb": 8, "gpu_type": "A100"},
    budget_nrc=10.0,
    timeout_seconds=3600
)

print(f"Job ID: {job.id}")
print(f"Status: {job.status}")
```

See [Job Submission Guide](./job-submission.md) for detailed examples.

### What formats do you support?

**Models:**
- Hugging Face Hub models (GGUF, SafeTensors, PyTorch)
- ONNX models
- Custom Docker containers with inference servers

**Input/Output:**
- JSON
- CSV
- Images (PNG, JPEG, WebP)
- Text files
- Parquet (for batch processing)

### How much does it cost?

Pricing is **dynamic** based on:
- GPU tier required
- Model size
- Job duration
- Network demand

**Typical costs:**
- Llama-2-7b inference: 0.01-0.05 NRC per request
- Fine-tuning job: 5-50 NRC (varies by dataset size)
- Batch processing: 0.1-1 NRC per item

You set a budget ceiling; jobs won't execute if costs exceed it.

### How do I monitor my job?

```python
# Check job status
job = client.get_job(job_id="abc123")
print(f"Status: {job.status}")  # pending, running, completed, failed
print(f"Progress: {job.progress}%")
print(f"Cost so far: {job.cost_nrc} NRC")

# Stream results in real-time
for result in client.stream_results(job_id="abc123"):
    print(result)
```

### What SLAs do you offer?

- **99% uptime** for job completion (averaged monthly)
- **10-minute average job startup** time
- **24-hour maximum job duration** (longer custom arrangements available)
- No SLA penalty guarantee; results are best-effort

---

## Token & Economics

### What is NRC?

NRC is an ERC-20 token on Ethereum that serves as the settlement and incentive mechanism for the NeuraCoin protocol. It represents computing value and can be traded on decentralized exchanges.

### Where can I buy NRC?

- **Uniswap** (primary DEX): [NRC/USDC pool](https://uniswap.org)
- **Aave**: Lending protocol integration
- Centralized exchanges (coming soon)

### How many NRC tokens exist?

- **Total supply**: 1,000,000,000 NRC
- **Distribution:**
  - 40% to providers (mining rewards)
  - 30% to requesters (early adopter incentives)
  - 20% to team & development
  - 10% to ecosystem & partnerships

### Is there token inflation?

Yes, gradually. Tokens are emitted at a decreasing rate over 10 years to incentivize early participants.

---

## Security & Trust

### How do I know jobs are executed correctly?

1. **Cryptographic proofs**: Providers submit computation proofs
2. **Spot verification**: Random jobs are re-executed by validators
3. **Smart contract arbitration**: Disputes resolved on-chain
4. **Reputation system**: Providers/requesters rated by counterparties

### Is my data private?

- Jobs execute in isolated Docker containers on providers' hardware
- Data is encrypted in transit (TLS 1.3)
- **Important**: NeuraCoin does not guarantee data deletion; use sensitive data at your own risk
- For sensitive workloads, consider private deployment options

### What happens in case of disputes?