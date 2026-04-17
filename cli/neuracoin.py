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

    return Web3.to_checksum_address(value)


def validate_positive_number(ctx, param, value: Any) -> float:
    """Validate that a number is positive."""
    if value is None:
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise click.BadParameter("Number cannot be empty")

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


def validate_json_file(ctx, param, value: Optional[str]) -> Dict[str, Any]:
    """Validate and load JSON file."""
    if not value:
        raise click.BadParameter("JSON file path cannot be empty")

    file_path = Path(value).resolve()

    if not file_path.exists():
        raise click.BadParameter(
            f"File not found: {file_path}\n"
            f"Please provide a valid path to a JSON file"
        )

    if not file_path.is_file():
        raise click.BadParameter(
            f"Path is not a file: {file_path}"
        )

    if file_path.suffix.lower() != ".json":
        raise click.BadParameter(
            f"File must be JSON format (.json), got: {file_path.suffix}"
        )

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(
            f"Invalid JSON in file: {e.msg} at line {e.lineno}, column {e.colno}"
        )
    except IOError as e:
        raise click.BadParameter(
            f"Failed to read file: {e}"
        )


def validate_job_spec(spec: Dict[str, Any]) -> None:
    """Validate job specification structure."""
    required_fields = ["model", "input_data", "hardware_requirements"]

    for field in required_fields:
        if field not in spec:
            raise ValidationError(
                f"Job spec missing required field: '{field}'\n"
                f"Required fields: {', '.join(required_fields)}"
            )

    if not isinstance(spec.get("model"), str) or not spec["model"]:
        raise ValidationError("'model' must be a non-empty string")

    if not isinstance(spec.get("hardware_requirements"), dict):
        raise ValidationError("'hardware_requirements' must be an object")

    hw_req = spec["hardware_requirements"]
    if "gpu_memory_gb" in hw_req:
        try:
            gpu_mem = float(hw_req["gpu_memory_gb"])
            if gpu_mem <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError("'gpu_memory_gb' must be a positive number")


def validate_environment() -> None:
    """Validate that required environment variables are set."""
    if not NRC_ADDRESS:
        print_error(
            "NRC_TOKEN_ADDRESS not set",
            "Environment",
            exit_code=1
        )

    if not JOB_REGISTRY:
        print_error(
            "JOB_REGISTRY_ADDR not set",
            "Environment",
            exit_code=1
        )

    if not WEB3_AVAILABLE:
        print_error(
            "Required packages not installed: web3, click, rich",
            "Dependencies",
            exit_code=1
        )


# ── CLI Commands ──────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """
    NeuraCoin Protocol CLI
    
    Manage GPU compute sharing and NRC token operations.
    """
    pass


@cli.command()
def status() -> None:
    """Check NeuraCoin network status."""
    try:
        validate_environment()

        if not WEB3_AVAILABLE:
            print_error("Web3 not available", "Network")

        w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC))

        if not w3.is_connected():
            print_error(
                f"Cannot connect to RPC endpoint: {DEFAULT_RPC}",
                "Connection"
            )

        block = w3.eth.block_number
        gas_price = w3.eth.gas_price

        table = Table(title="NeuraCoin Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Network", "Connected")
        table.add_row("Block Number", str(block))
        table.add_row("Gas Price (Wei)", str(gas_price))
        table.add_row("RPC Endpoint", DEFAULT_RPC)