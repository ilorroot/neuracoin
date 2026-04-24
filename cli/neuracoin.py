#!/usr/bin/env python3
"""
NeuraCoin CLI
=============
Command-line interface for interacting with the NeuraCoin protocol.

Usage:
    python neuracoin.py --help
    python neuracoin.py status
    python neuracoin.py jobs list
    python neuracoin.py jobs submit --spec job.json --stake 100
    python neuracoin.py provider register
    python neuracoin.py wallet balance --address 0x...
    python neuracoin.py network stats

Requirements:
    pip install web3 click rich
"""

import os
import json
import click
from pathlib import Path
from typing import Optional, Any, Dict
from decimal import Decimal

try:
    from web3 import Web3
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

# ── Config ────────────────────────────────────────────────────────────────────

console = Console()

DEFAULT_RPC    = os.getenv("NEURACOIN_RPC",      "https://rpc.neuracoin.network")
NRC_ADDRESS    = os.getenv("NRC_TOKEN_ADDRESS",  "")
JOB_REGISTRY   = os.getenv("JOB_REGISTRY_ADDR", "")
PROVIDER_REGISTRY = os.getenv("PROVIDER_REGISTRY_ADDR", "")
STAKING_CONTRACT = os.getenv("STAKING_CONTRACT_ADDR", "")
PRIVATE_KEY    = os.getenv("NEURACOIN_KEY",      "")

# ── Error Messages ────────────────────────────────────────────────────────────

class ValidationError(Exception):
    """Custom validation error for better error reporting."""
    pass


def format_error(message: str, context: Optional[str] = None) -> str:
    """Format error message with optional context."""
    if context:
        return f"[red]Error ({context}):[/red] {message}"
    return f"[red]Error:[/red] {message}"


def print_error(message: str, context: Optional[str] = None, exit_code: int = 1) -> None:
    """Print formatted error and exit."""
    console.print(format_error(message, context))
    raise SystemExit(exit_code)


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] {message}")


# ── Validators ────────────────────────────────────────────────────────────────

def validate_address(ctx, param, value: str) -> str:
    """Validate Ethereum address format."""
    if not value:
        raise click.BadParameter("Address cannot be empty")

    value = value.strip()

    if not value.startswith("0x"):
        raise click.BadParameter(
            f"Address must start with '0x', got: {value[:10]}..."
        )

    if len(value) != 42:
        raise click.BadParameter(
            f"Invalid address length: expected 42 characters, got {len(value)}"
        )

    try:
        int(value, 16)
    except ValueError:
        raise click.BadParameter(
            "Address contains invalid hexadecimal characters"
        )

    try:
        return Web3.to_checksum_address(value)
    except Exception as e:
        raise click.BadParameter(f"Failed to convert address to checksum format: {str(e)}")


def validate_positive_number(ctx, param, value: Any) -> Decimal:
    """Validate positive numeric input."""
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise click.BadParameter(f"Value must be positive, got: {value}")
        return decimal_value
    except (ValueError, TypeError):
        raise click.BadParameter(f"Invalid number format: {value}")


# ── Web3 Helpers ──────────────────────────────────────────────────────────────

def get_web3() -> Web3:
    """Initialize and return Web3 instance."""
    if not WEB3_AVAILABLE:
        print_error("Web3 library not available. Install with: pip install web3")

    w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC))
    if not w3.is_connected():
        print_error(f"Failed to connect to RPC endpoint: {DEFAULT_RPC}", "RPC Connection")

    return w3


def get_contract(address: str, abi: Dict[str, Any]) -> Any:
    """Load a contract instance."""
    if not address:
        print_error(f"Contract address not configured", "Configuration")

    w3 = get_web3()
    try:
        return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)
    except Exception as e:
        print_error(f"Failed to load contract: {str(e)}", "Contract Loading")


# ── Job Registry ABI (minimal) ────────────────────────────────────────────────

JOB_REGISTRY_ABI = [
    {
        "inputs": [],
        "name": "totalJobs",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "jobCount",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ── Provider Registry ABI (minimal) ───────────────────────────────────────────

PROVIDER_REGISTRY_ABI = [
    {
        "inputs": [],
        "name": "totalProviders",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "providerCount",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ── Staking Contract ABI (minimal) ────────────────────────────────────────────

STAKING_CONTRACT_ABI = [
    {
        "inputs": [],
        "name": "totalStaked",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getTotalStaked",
        "outputs": [{"type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# ── CLI Commands ──────────────────────────────────────────────────────────────

@click.group()
def cli() -> None:
    """NeuraCoin CLI - Decentralized AI Compute Protocol"""
    pass


@cli.group()
def network() -> None:
    """Network information and statistics"""
    pass


@network.command()
def stats() -> None:
    """Display network statistics (jobs, providers, staked NRC)"""
    try:
        w3 = get_web3()
        
        total_jobs = 0
        total_providers = 0
        total_staked = 0
        
        # Fetch total jobs
        if JOB_REGISTRY:
            try:
                job_contract = get_contract(JOB_REGISTRY, JOB_REGISTRY_ABI)
                total_jobs = job_contract.functions.totalJobs().call()
            except Exception as e:
                print_warning(f"Failed to fetch job count: {str(e)}")