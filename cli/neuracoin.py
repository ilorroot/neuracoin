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

Requirements:
    pip install web3 click rich
"""

import os
import json
import click
from pathlib import Path
from typing import Optional
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
    
    return value


def validate_positive_number(ctx, param, value) -> float:
    """Validate that a number is positive."""
    if value is None:
        return value
    
    if isinstance(value, str):
        value = value.strip()
    
    try:
        num = float(value)
        if num <= 0:
            raise click.BadParameter(
                f"Value must be positive (> 0), got: {num}"
            )
        return num
    except (ValueError, TypeError):
        raise click.BadParameter(
            f"Invalid number format: '{value}' is not a valid number"
        )


def validate_json_file(ctx, param, value: str) -> dict:
    """Validate and load JSON file."""
    if not value:
        raise click.BadParameter("File path cannot be empty")

    value = value.strip()
    path = Path(value).resolve()
    
    if not path.exists():
        raise click.BadParameter(
            f"File not found: {path}\nPlease provide a valid path to an existing file"
        )
    
    if not path.is_file():
        raise click.BadParameter(
            f"Path is not a file: {path}"
        )
    
    if path.suffix.lower() != ".json":
        raise click.BadParameter(
            f"File must be JSON format (*.json), got: {path.suffix}"
        )

    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            raise click.BadParameter(
                f"JSON file must contain an object, got: {type(data).__name__}"
            )
        
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(
            f"Invalid JSON in {path.name}:\n  Line {e.lineno}, Column {e.colno}: {e.msg}"
        )
    except IOError as e:
        raise click.BadParameter(
            f"Cannot read file {path}: {str(e)}"
        )


def validate_job_spec(spec: dict) -> None:
    """Validate job specification structure."""
    required_fields = ["model", "input_data", "timeout"]
    missing = [f for f in required_fields if f not in spec]
    
    if missing:
        raise click.BadParameter(
            f"Job spec missing required fields: {', '.join(missing)}"
        )
    
    if not isinstance(spec.get("timeout"), (int, float)) or spec["timeout"] <= 0:
        raise click.BadParameter(
            "Job spec 'timeout' must be a positive number (seconds)"
        )


def validate_stake_amount(amount: float, min_stake: float = 1.0) -> float:
    """Validate stake amount."""
    if amount < min_stake:
        raise click.BadParameter(
            f"Stake amount must be at least {min_stake} NRC, got: {amount}"
        )
    
    if amount > 1_000_000:
        raise click.BadParameter(
            f"Stake amount is unusually high: {amount} NRC (max recommended: 1,000,000)"
        )
    
    return amount


# ── Config Validators ─────────────────────────────────────────────────────────

def check_environment() -> None:
    """Check that required environment variables are set."""
    errors = []
    
    if not NRC_ADDRESS:
        errors.append("NRC_TOKEN_ADDRESS not set")
    elif not NRC_ADDRESS.startswith("0x"):
        errors.append("NRC_TOKEN_ADDRESS is invalid (must start with '0x')")
    
    if not JOB_REGISTRY:
        errors.append("JOB_REGISTRY_ADDR not set")
    elif not JOB_REGISTRY.startswith("0x"):
        errors.append("JOB_REGISTRY_ADDR is invalid (must start with '0x')")
    
    if errors:
        console.print(format_error(
            "Missing or invalid environment configuration:\n  " + "\n  ".join(errors),
            "Configuration"
        ))
        raise click.Exit(1)


def check_web3() -> None:
    """Check that Web3 is available."""
    if not WEB3_AVAILABLE:
        console.print(format_error(
            "web3 library not installed. Run: pip install web3 click rich",
            "Dependencies"
        ))
        raise click.Exit(1)


# ── ABI loading ───────────────────────────────────────────────────────────────

def load_abi(name: str) -> list:
    """Load contract ABI from the contracts directory."""
    abi_path = Path(__file__).parent.parent / "contracts" / "abi" / f"{name}.json"
    
    if not abi_path.exists():
        console.print(format_error(
            f"ABI file not found: {abi_path}\nMake sure contract ABIs are in contracts/abi/",
            "ABI Loading"
        ))
        raise click.Exit(1)
    
    try:
        with open(abi_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e: