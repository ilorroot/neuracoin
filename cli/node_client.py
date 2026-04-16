```python
#!/usr/bin/env python3
"""
NeuraCoin Compute Node Client
A simple client that polls for AI compute jobs and logs activity.
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NeuraCoin.ComputeNode")


@dataclass
class Job:
    """Represents a compute job."""
    job_id: str
    model_name: str
    input_data: dict
    gpu_required: str
    reward: float
    timestamp: str


@dataclass
class NodeStats:
    """Represents compute node statistics."""
    node_id: str
    gpu_model: str
    total_memory_gb: int
    available_memory_gb: int
    total_jobs_completed: int
    total_earnings: float
    uptime_seconds: int


class ComputeNodeClient:
    """
    A client for the NeuraCoin compute node that polls for jobs and tracks activity.
    """

    def __init__(
        self,
        node_id: str,
        gpu_model: str = "NVIDIA RTX 4090",
        total_memory_gb: int = 24,
        poll_interval: int = 5
    ):
        """
        Initialize the compute node client.

        Args:
            node_id: Unique identifier for this compute node
            gpu_model: GPU model available on this node
            total_memory_gb: Total GPU memory in GB
            poll_interval: Polling interval in seconds
        """
        self.node_id = node_id
        self.gpu_model = gpu_model
        self.total_memory_gb = total_memory_gb
        self.available_memory_gb = total_memory_gb
        self.poll_interval = poll_interval
        self.total_jobs_completed = 0
        self.total_earnings = 0.0
        self.start_time = time.time()
        self.job_queue: list[Job] = []
        self.is_running = False

        logger.info(f"Initialized compute node: {node_id}")
        logger.info(f"GPU: {gpu_model}, Memory: {total_memory_gb}GB")

    def get_stats(self) -> NodeStats:
        """Get current node statistics."""
        uptime = int(time.time() - self.start_time)
        return NodeStats(
            node_id=self.node_id,
            gpu_model=self.gpu_model,
            total_memory_gb=self.total_memory_gb,
            available_memory_gb=self.available_memory_gb,
            total_jobs_completed=self.total_jobs_completed,
            total_earnings=self.total_earnings,
            uptime_seconds=uptime
        )

    def poll_for_jobs(self) -> Optional[Job]:
        """
        Poll the job queue for available compute jobs.
        In a real implementation, this would connect to a central job dispatcher.

        Returns:
            A Job if available, None otherwise
        """
        # Simulate job polling - in production this would call the actual job dispatcher
        logger.debug("Polling for available compute jobs...")

        # For demo purposes, we'll simulate receiving jobs occasionally
        import random
        if random.random() < 0.3:  # 30% chance of getting a job
            job = Job(
                job_id=f"job_{int(time.time() * 1000)}",
                model_name=random.choice([
                    "GPT-3.5-Turbo",
                    "Llama-2-70B",
                    "Mistral-7B",
                    "LLaVA-Vision",
                    "Stable-Diffusion-XL"
                ]),
                input_data={
                    "prompt": "Sample compute task",
                    "parameters": {"temperature": 0.7, "max_tokens": 256}
                },
                gpu_required=self.gpu_model,
                reward=random.uniform(0.5, 5.0),
                timestamp=datetime.now().isoformat()
            )
            logger.info(f"Job received: {job.job_id} ({job.model_name})")
            return job

        return None

    def execute_job(self, job: Job) -> bool:
        """
        Execute a compute job.
        In a real implementation, this would run the actual AI model.

        Args:
            job: The job to execute

        Returns:
            True if job completed successfully, False otherwise
        """
        logger.info(f"Starting execution of job {job.job_id}")

        # Simulate job execution time
        execution_time = 2 + (hash(job.job_id) % 5)  # 2-7 seconds
        logger.info(f"Estimated execution time: {execution_time}s")

        try:
            # Simulate GPU memory usage
            memory_used = 4 + (hash(job.job_id) % 12)  # 4-16GB
            self.available_memory_gb -= min(memory_used, self.available_memory_gb)

            # Simulate execution
            time.sleep(1)  # Sleep for 1 second in demo mode instead of full time
            logger.info(f"Job {job.job_id} completed successfully")

            # Free up memory
            self.available_memory_gb = min(
                self.available_memory_gb + memory_used,
                self.total_memory_gb
            )

            # Update stats
            self.total_jobs_completed += 1
            self.total_earnings += job.reward

            logger.info(
                f"Earnings updated: +{job.reward} NRC (Total: {self.total_earnings:.2f} NRC)"
            )

            return True

        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {str(e)}")
            self.available_memory_gb = self.total_memory_gb  # Reset memory
            return False

    def log_activity(self) -> None:
        """Log current node activity and statistics."""
        stats = self.get_stats()
        uptime_hours = stats.uptime_seconds / 3600

        activity_log = {
            "timestamp": datetime.now().isoformat(),
            "node_id": stats.node_id,
            "gpu_model": stats.gpu_model,
            "memory_usage": {
                "total_gb": stats.total_memory_gb,
                "available_gb": stats.available_memory_gb,
                "utilization_percent": round(
                    100 * (1 - stats.available_memory_gb / stats.total_memory_gb), 2
                )
            },
            "performance": {
                "total_jobs_completed": stats.total_jobs_completed,
                "total_earnings_nrc": round(stats.total_earnings, 4),
                "uptime_hours": round(uptime_hours, 2)
            },
            "queue_status": {
                "pending_jobs": len(self.job_queue)
            }
        }

        logger.info(f"Activity Log: {json.dumps(activity_log, indent=2)}")

        return activity_log

    def run(self, duration: Optional[int] = None) -> None:
        """
        Run the compute node client main loop.

        Args:
            duration: Run duration in seconds. If None, run indefinitely.
        """
        self.is_running = True
        start_time = time.time()

        logger.info(f"Starting compute node client (duration: {duration}s or indefinite)")

        try:
            while self.is_running:
                # Check if we should stop
                if duration and (time.time() - start_time) > duration:
                    logger.info("Duration limit reached, stopping...")
                    break

                # Poll for jobs
                job = self.poll_for_jobs()