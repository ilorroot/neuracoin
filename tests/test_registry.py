```python
"""
Comprehensive pytest tests for NeuraCoin job registry.
Tests job submission, acceptance, and completion flows.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
import json

from neuraca_cli.compute.registry import (
    JobRegistry,
    Job,
    JobStatus,
    ComputeNode,
    JobSubmissionError,
    JobNotFoundError,
)


class TestJobRegistry:
    """Test suite for JobRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh JobRegistry instance for each test."""
        return JobRegistry()

    @pytest.fixture
    def sample_job_params(self) -> Dict[str, Any]:
        """Create sample job parameters."""
        return {
            "model": "llama-7b",
            "dataset_url": "ipfs://QmSampleHash",
            "compute_requirements": {
                "gpu": "H100",
                "memory_gb": 40,
                "storage_gb": 100,
            },
            "priority": 5,
            "max_price_per_hour": 50.0,
            "timeout_hours": 24,
        }

    @pytest.fixture
    def sample_node(self) -> ComputeNode:
        """Create a sample compute node."""
        return ComputeNode(
            node_id="node_001",
            owner_address="0x1234567890123456789012345678901234567890",
            gpu_type="H100",
            available_memory_gb=80,
            available_storage_gb=500,
            hourly_rate=40.0,
            reputation_score=4.8,
            total_jobs_completed=150,
        )

    def test_submit_job_success(self, registry: JobRegistry, sample_job_params: Dict[str, Any]):
        """Test successful job submission."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        assert job_id is not None
        assert len(job_id) > 0

        job = registry.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.PENDING
        assert job.model == sample_job_params["model"]
        assert job.submitter_address == "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"

    def test_submit_job_invalid_priority(self, registry: JobRegistry, sample_job_params: Dict[str, Any]):
        """Test job submission with invalid priority."""
        sample_job_params["priority"] = 11  # Priority must be 1-10

        with pytest.raises(JobSubmissionError):
            registry.submit_job(
                submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                **sample_job_params,
            )

    def test_submit_job_negative_price(self, registry: JobRegistry, sample_job_params: Dict[str, Any]):
        """Test job submission with negative max price."""
        sample_job_params["max_price_per_hour"] = -10.0

        with pytest.raises(JobSubmissionError):
            registry.submit_job(
                submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                **sample_job_params,
            )

    def test_get_nonexistent_job(self, registry: JobRegistry):
        """Test retrieving a non-existent job."""
        with pytest.raises(JobNotFoundError):
            registry.get_job("nonexistent_job_id")

    def test_accept_job_success(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
        sample_node: ComputeNode,
    ):
        """Test successful job acceptance by a compute node."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        job = registry.get_job(job_id)
        assert job.status == JobStatus.PENDING

        result = registry.accept_job(job_id, sample_node.node_id)
        assert result is True

        job = registry.get_job(job_id)
        assert job.status == JobStatus.ACCEPTED
        assert job.assigned_node_id == sample_node.node_id
        assert job.accepted_at is not None

    def test_accept_job_already_assigned(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
    ):
        """Test accepting a job that's already been assigned."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        registry.accept_job(job_id, "node_001")

        with pytest.raises(JobSubmissionError):
            registry.accept_job(job_id, "node_002")

    def test_start_job_success(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
    ):
        """Test successful job startup."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        registry.accept_job(job_id, "node_001")

        result = registry.start_job(job_id)
        assert result is True

        job = registry.get_job(job_id)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_start_job_not_accepted(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
    ):
        """Test starting a job that hasn't been accepted."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        with pytest.raises(JobSubmissionError):
            registry.start_job(job_id)

    def test_complete_job_success(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
    ):
        """Test successful job completion."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        registry.accept_job(job_id, "node_001")
        registry.start_job(job_id)

        result_metadata = {
            "output_hash": "QmResultHash",
            "computation_time_seconds": 3600,
            "total_cost": 40.0,
        }

        result = registry.complete_job(job_id, result_metadata)
        assert result is True

        job = registry.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.result_metadata == result_metadata

    def test_complete_job_not_running(
        self,
        registry: JobRegistry,
        sample_job_params: Dict[str, Any],
    ):
        """Test completing a job that isn't running."""
        job_id = registry.submit_job(
            submitter_address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
            **sample_job_params,
        )

        result_metadata = {"output_