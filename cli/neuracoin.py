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
    python neuracoin.py price

Requirements:
    pip install web3 click rich requests
"""

import os
import json
import click
import requests
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
PRICE_API_ENDPOINT = os.getenv("PRICE_API_ENDPOINT", "https://api.neuracoin.network/v1/price")

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
    except ValueError as e:
        raise click.BadParameter(f"Invalid address: {str(e)}")


# ── Price API ─────────────────────────────────────────────────────────────────

def fetch_nrc_price(timeout: int = 5) -> Dict[str, Any]:
    """
    Fetch NRC token price from mock API endpoint.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        Dict containing price data with keys: price, usd, currency, timestamp
        
    Raises:
        ValidationError: If API request fails or returns invalid data
    """
    try:
        response = requests.get(
            PRICE_API_ENDPOINT,
            timeout=timeout,
            headers={"User-Agent": "NeuraCoin-CLI/1.0"}
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ValidationError(
            f"Failed to connect to price API: {PRICE_API_ENDPOINT}"
        )
    except requests.exceptions.Timeout:
        raise ValidationError(
            f"Price API request timed out after {timeout}s"
        )
    except requests.exceptions.RequestException as e:
        raise ValidationError(f"Price API request failed: {str(e)}")

    try:
        data = response.json()
    except json.JSONDecodeError:
        raise ValidationError("Price API returned invalid JSON")

    # Validate required fields
    required_fields = ["price", "currency", "timestamp"]
    missing_fields = [f for f in required_fields if f not in data]
    if missing_fields:
        raise ValidationError(
            f"Price API response missing fields: {', '.join(missing_fields)}"
        )

    return data


# ── CLI Commands ──────────────────────────────────────────────────────────────

@click.group()
def cli():
    """NeuraCoin Protocol CLI"""
    pass


@cli.command()
def status():
    """Check NeuraCoin network status."""
    console.print("[cyan]NeuraCoin Network Status[/cyan]")
    console.print(f"RPC Endpoint: {DEFAULT_RPC}")
    console.print("Status: [green]✓ Connected[/green]")


@cli.command()
@click.option("--currency", default="usd", type=str, help="Currency for price display (usd, eur, gbp)")
@click.option("--format", "output_format", default="table", type=click.Choice(["table", "json"]), help="Output format")
def price(currency: str, output_format: str):
    """
    Fetch and display current NRC token price.
    
    Example:
        python neuracoin.py price
        python neuracoin.py price --currency eur
        python neuracoin.py price --format json
    """
    try:
        price_data = fetch_nrc_price()
    except ValidationError as e:
        print_error(str(e), context="price")

    # Format price value
    try:
        price_value = float(price_data.get("price", 0))
    except (ValueError, TypeError):
        print_error("Invalid price value received from API", context="price")

    if output_format == "json":
        console.print_json(data=price_data)
    else:
        # Table format
        table = Table(title="NRC Token Price")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Current Price", f"${price_value:.6f}")
        table.add_row("Currency", price_data.get("currency", "USD").upper())
        table.add_row("Updated At", str(price_data.get("timestamp", "N/A")))

        if "market_cap" in price_data:
            market_cap = float(price_data.get("market_cap", 0))
            table.add_row("Market Cap", f"${market_cap:,.2f}")

        if "volume_24h" in price_data:
            volume = float(price_data.get("volume_24h", 0))
            table.add_row("24h Volume", f"${volume: