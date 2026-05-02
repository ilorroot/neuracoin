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
from urllib.parse import urlparse

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
        raise click.BadParameter(f"Invalid address format: {str(e)}")


def validate_file_exists(ctx, param, value: str) -> str:
    """Validate that file exists and is readable."""
    if not value:
        raise click.BadParameter("File path cannot be empty")

    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"File not found: {value}")

    if not path.is_file():
        raise click.BadParameter(f"Path is not a file: {value}")

    if not os.access(path, os.R_OK):
        raise click.BadParameter(f"File is not readable: {value}")

    return str(path.absolute())


def validate_json_file(ctx, param, value: str) -> Dict[str, Any]:
    """Validate and parse JSON file."""
    if not value:
        raise click.BadParameter("JSON file path cannot be empty")

    file_path = validate_file_exists(ctx, param, value)

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON in {value}: {str(e)}")
    except IOError as e:
        raise click.BadParameter(f"Cannot read file {value}: {str(e)}")


def validate_positive_number(ctx, param, value: Any) -> Decimal:
    """Validate that value is a positive number."""
    if value is None:
        raise click.BadParameter("Value cannot be empty")

    try:
        decimal_value = Decimal(str(value))
    except Exception as e:
        raise click.BadParameter(f"Invalid number format: {str(e)}")

    if decimal_value <= 0:
        raise click.BadParameter(f"Value must be positive, got: {decimal_value}")

    return decimal_value


def validate_rpc_url(ctx, param, value: str) -> str:
    """Validate RPC URL format."""
    if not value:
        raise click.BadParameter("RPC URL cannot be empty")

    value = value.strip()

    try:
        parsed = urlparse(value)
        if not parsed.scheme in ('http', 'https'):
            raise click.BadParameter(f"RPC URL must use http or https, got: {parsed.scheme}")
        if not parsed.netloc:
            raise click.BadParameter(f"Invalid RPC URL format: {value}")
    except Exception as e:
        raise click.BadParameter(f"Invalid RPC URL: {str(e)}")

    return value


def validate_config() -> None:
    """Validate that required environment variables are set."""
    if not WEB3_AVAILABLE:
        print_error(
            "Required dependencies not installed. Run: pip install web3 click rich",
            context="Dependencies"
        )

    required_vars = {
        "NEURACOIN_RPC": DEFAULT_RPC,
        "NRC_TOKEN_ADDRESS": NRC_ADDRESS,
        "JOB_REGISTRY_ADDR": JOB_REGISTRY,
    }

    missing = [name for name, value in required_vars.items() if not value]
    if missing:
        print_warning(
            f"Missing environment variables: {', '.join(missing)}. "
            "Some features may not work correctly."
        )


# ── Main CLI Group ────────────────────────────────────────────────────────────

@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """NeuraCoin Protocol CLI - Decentralized AI Compute Sharing"""
    validate_config()


# ── Status Command ────────────────────────────────────────────────────────────

@cli.command()
def status() -> None:
    """Show network and protocol status."""
    try:
        if not WEB3_AVAILABLE:
            print_error("Web3 library not available", context="Status")

        w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC))

        if not w3.is_connected():
            print_error(
                f"Cannot connect to RPC endpoint: {DEFAULT_RPC}",
                context="Network"
            )

        block_number = w3.eth.block_number
        latest_block = w3.eth.get_block(block_number)

        table