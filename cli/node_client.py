#!/usr/bin/env python3
"""
NeuraCoin Compute Node Client
A simple client that polls for AI compute jobs and logs activity.
"""

import json
import logging
import time
import random
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
        logger.debug("Polling for available compute jobs...")

        if random.random() < 0.3:
            job_id = f"job_{int(time.time())}_{random.randint(1000, 9999)}"
            models = ["gpt-3.5", "stable-diffusion", "llama-2", "bert-large"]
            job = Job(
                job_id=job_id,
                model_name=random.choice(models),
                input_data={"prompt": "sample inference task"},
                gpu_required=self.gpu_model,
                reward=random.uniform(0.1, 1.5),
                timestamp=datetime.utcnow().isoformat()
            )
            logger.info(f"Job received: {job_id} ({job.model_name}) - Reward: {job.reward:.2f} NRC")
            return job

        return None

    def execute_job(self, job: Job) -> bool:
        """
        Execute a compute job and update node statistics.

        Args:
            job: The job to execute

        Returns:
            True if job executed successfully, False otherwise
        """
        logger.info(f"Executing job: {job.job_id}")

        try:
            memory_needed = random.randint(4, 16)
            if memory_needed > self.available_memory_gb:
                logger.warning(f"Insufficient memory for job {job.job_id}")
                return False

            self.available_memory_gb -= memory_needed
            logger.info(f"Memory allocated: {memory_needed}GB")

            execution_time = random.uniform(2, 8)
            logger.info(f"Running inference for {execution_time:.1f} seconds...")
            time.sleep(min(execution_time, 2))

            self.available_memory_gb += memory_needed
            self.total_jobs_completed += 1
            self.total_earnings += job.reward

            logger.info(f"Job {job.job_id} completed! Earned {job.reward:.2f} NRC")
            logger.info(f"Total earnings: {self.total_earnings:.2f} NRC | Jobs completed: {self.total_jobs_completed}")

            return True

        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {str(e)}")
            return False

    def run(self, duration: Optional[int] = None) -> None:
        """
        Start the compute node client polling loop.

        Args:
            duration: Optional duration in seconds to run before stopping
        """
        self.is_running = True
        logger.info(f"Starting compute node client (poll interval: {self.poll_interval}s)")

        start_time = time.time()

        try:
            while self.is_running:
                if duration and (time.time() - start_time) > duration:
                    logger.info("Duration limit reached, shutting down...")
                    break

                job = self.poll_for_jobs()
                if job:
                    self.execute_job(job)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the compute node client and log final statistics."""
        self.is_running = False
        stats = self.get_stats()
        logger.info("Compute node shutting down...")
        logger.info(f"Final statistics: {json.dumps(asdict(stats), indent=2)}")

    def print_stats(self) -> None:
        """Print current node statistics to console."""
        stats = self.get_stats()
        print("\n" + "="*60)
        print("NeuraCoin Compute Node Statistics")
        print("="*60)
        print(f"Node ID:              {stats.node_id}")
        print(f"GPU Model:            {stats.gpu_model}")
        print(f"Total Memory:         {stats.total_memory_gb}GB")
        print(f"Available Memory:     {stats.available_memory_gb}GB")
        print(f"Jobs Completed:       {stats.total_jobs_completed}")
        print(f"Total Earnings:       {stats.total_earnings:.2f} NRC")
        print(f"Uptime:               {stats.uptime_seconds} seconds")
        print("="*60 + "\n")


if __name__ == "__main__":
    node = ComputeNodeClient(
        node_id="neuracoin-node-001",
        gpu_model="NVIDIA RTX 4090",
        total_memory_gb=24,
        poll_interval=3
    )

    try:
        node.run(duration=60)
    except Exception as e:
        logger.error(f"Node client error: {str(e)}")