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
    except ValueError:
        raise click.BadParameter(
            f"Invalid number format: '{value}' is not a valid number"
        )


def validate_json_file(ctx, param, filepath: Optional[str]) -> Dict[str, Any]:
    """Validate and load JSON file."""
    if not filepath:
        raise click.BadParameter("JSON file path cannot be empty")

    filepath = filepath.strip()
    path = Path(filepath)

    if not path.exists():
        raise click.BadParameter(
            f"File not found: {filepath}"
        )

    if not path.is_file():
        raise click.BadParameter(
            f"Path is not a file: {filepath}"
        )

    if path.suffix.lower() != ".json":
        raise click.BadParameter(
            f"File must be JSON format, got: {path.suffix}"
        )

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(
            f"Invalid JSON in {filepath}: {str(e)}"
        )
    except IOError as e:
        raise click.BadParameter(
            f"Cannot read file {filepath}: {str(e)}"
        )


def validate_job_spec(spec: Dict[str, Any]) -> None:
    """Validate job specification structure."""
    required_fields = ["model", "input_size", "output_size"]

    for field in required_fields:
        if field not in spec:
            raise ValidationError(
                f"Job spec missing required field: '{field}'"
            )

    if not isinstance(spec["model"], str) or not spec["model"].strip():
        raise ValidationError("Field 'model' must be non-empty string")

    if not isinstance(spec["input_size"], (int, float)) or spec["input_size"] <= 0:
        raise ValidationError("Field 'input_size' must be positive number")

    if not isinstance(spec["output_size"], (int, float)) or spec["output_size"] <= 0:
        raise ValidationError("Field 'output_size' must be positive number")


def validate_rpc_url(url: str) -> None:
    """Validate RPC URL format."""
    if not url:
        raise ValidationError("RPC URL cannot be empty")

    url = url.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ValidationError("RPC URL must start with http:// or https://")

    if not WEB3_AVAILABLE:
        raise ValidationError("Web3 library not available. Install with: pip install web3")


def validate_private_key(key: str) -> str:
    """Validate private key format."""
    if not key:
        raise ValidationError("Private key cannot be empty")

    key = key.strip()

    if not key.startswith("0x"):
        raise ValidationError("Private key must start with '0x'")

    if len(key) != 66:
        raise ValidationError(
            f"Invalid private key length: expected 66 characters, got {len(key)}"
        )

    try:
        int(key, 16)
    except ValueError:
        raise ValidationError("Private key contains invalid hexadecimal characters")

    return key


# ── CLI Commands ──────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """NeuraCoin - Decentralized AI compute-sharing protocol"""
    if not WEB3_AVAILABLE:
        print_warning("Web3 library not available. Install with: pip install web3")


@cli.command()
def status():
    """Check NeuraCoin network status."""
    try:
        if not DEFAULT_RPC:
            print_error("RPC URL not configured", "config", 1)

        try:
            validate_rpc_url(DEFAULT_RPC)
        except ValidationError as e:
            print_error(str(e