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

Yes. You can register multiple GPUs under one account and the daemon will load-balance jobs across them automatically.

### What happens if my job fails or times out?

- **Failed jobs**: Your GPU receives a small penalty, no payment
- **Timeouts**: Job is reassigned to another provider after 5 minutes
- **Disputes**: Resolved through staking mechanism and on-chain verification

### Do I need to stake tokens?

Yes, providers must stake 100 NRC to register. This ensures reliability and prevents spam. Your stake is returned when you deregister.

---

## For Job Requesters

### How do I submit an AI job?

1. **Deploy the NeuraCoin requester library** in your application
2. **Define job parameters** (model, input data, hardware requirements)
3. **Set your budget** in NRC tokens
4. **Submit the job** to the network
5. **Retrieve results** once completed

### Example: Running Inference

```python
from neuracoin import NeuraCoinClient
from neuracoin.models import InferenceJob

# Initialize client
client = NeuraCoinClient(api_key="your_api_key")

# Define the job
job = InferenceJob(
    model_name="meta-llama/Llama-2-7b",
    prompt="What is artificial intelligence?",
    max_tokens=256,
    temperature=0.7,
    min_gpu_memory_gb=8,
    max_price_per_token=0.001  # in NRC
)

# Submit job
job_id = client.submit_job(job)

# Poll for results
result = client.wait_for_result(job_id, timeout=300)

print(f"Generated text: {result.output}")
print(f"Cost: {result.cost_nrc} NRC")
```

### Example: Fine-tuning a Model

```python
from neuracoin import NeuraCoinClient
from neuracoin.models import FineTuneJob

client = NeuraCoinClient()

job = FineTuneJob(
    base_model="mistralai/Mistral-7B",
    training_data_url="s3://my-bucket/training-data.jsonl",
    num_epochs=3,
    learning_rate=2e-5,
    batch_size=4,
    min_gpu_memory_gb=16,
    budget_nrc=50.0
)

job_id = client.submit_job(job)
events = client.stream_job_logs(job_id)

for event in events:
    print(f"Epoch {event.epoch}: Loss = {event.loss}")

fine_tuned_model = client.download_model(job_id)
```

### How much does it cost?

Pricing is **dynamic and determined by the market**:
- Base cost scales with GPU compute required
- Time-based: typical inference ~$0.0001-0.001 per token
- Storage-based: model weights cached at $0.01/GB/day
- Batch jobs receive discounts (20-40%)

You set a **max budget** before submission; jobs won't exceed this amount.

### Can I use custom models?

Yes. You can:
- Upload your own model to IPFS or S3
- Reference it by URL or hash in your job submission
- Providers download it automatically before execution

### What data privacy protections exist?

- **Input data** is never stored after job completion
- **Encrypted channels** (TLS 1.3) for all data transmission
- **Zero-knowledge proofs** optionally verify job execution without revealing inputs
- Providers never see unencrypted data without explicit consent

### How long do jobs take?

Typical latencies:
- **Inference**: 5-30 seconds (network + compute)
- **Fine-tuning**: 30 minutes - 4 hours
- **Training**: 1-7 days (depending on dataset/model)

---

## Tokenomics & Security

### What is the NRC token supply?

- **Total Supply**: 1,000,000,000 NRC
- **Distribution**:
  - 40% Community Rewards (provider/requester incentives)
  - 20% Core Development
  - 15% Early Backers
  - 15% Foundation Treasury
  - 10% Strategic Partners

### How do I buy NRC tokens?

Available on:
- **Uniswap** (Ethereum mainnet)
- **Kraken** (centralized exchange)
- **Curve** (for liquidity pools)

Minimum purchase: 0.01 NRC

### Is NeuraCoin audited?

Yes. Smart contracts audited by:
- Trail of Bits (May 2024)
- OpenZeppelin (Q4 2024)

Full audit reports available at [neuracoin.io/security](https://neuracoin.io/security)

### What about slashing penalties?

Providers risk losing stake if they:
- Produce incorrect outputs (detected via random re-execution)
- Go offline during job execution
- Lie about GPU