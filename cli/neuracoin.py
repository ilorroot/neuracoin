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

# ── Validators ────────────────────────────────────────────────────────────────

def validate_address(ctx, param, value: str) -> str:
    """Validate Ethereum address format."""
    if not value:
        raise click.BadParameter("Address cannot be empty")
    if not value.startswith("0x"):
        raise click.BadParameter("Address must start with '0x'")
    if len(value) != 42:
        raise click.BadParameter("Invalid address length (expected 42 characters)")
    try:
        int(value, 16)
    except ValueError:
        raise click.BadParameter("Address contains invalid hexadecimal characters")
    return value


def validate_positive_number(ctx, param, value) -> float:
    """Validate that a number is positive."""
    if value is None:
        return value
    try:
        num = float(value)
        if num <= 0:
            raise click.BadParameter(f"Value must be positive, got {num}")
        return num
    except ValueError:
        raise click.BadParameter(f"Invalid number format: {value}")


def validate_json_file(ctx, param, value: str) -> dict:
    """Validate and load JSON file."""
    if not value:
        raise click.BadParameter("File path cannot be empty")
    
    path = Path(value)
    if not path.exists():
        raise click.BadParameter(f"File not found: {value}")
    if not path.suffix.lower() == ".json":
        raise click.BadParameter(f"File must be JSON format, got: {path.suffix}")
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON in {value}: {str(e)}")
    except IOError as e:
        raise click.BadParameter(f"Cannot read file {value}: {str(e)}")


# ── ABI loading ───────────────────────────────────────────────────────────────

def load_abi(name: str) -> list:
    """Load contract ABI from the contracts/ directory by filename."""
    abi_path = Path(__file__).parent.parent / "contracts" / f"{name}.json"
    if not abi_path.exists():
        console.print(f"[yellow]⚠ ABI not found: {abi_path}[/yellow]")
        return []
    try:
        with open(abi_path) as f:
            return json.load(f).get("abi", [])
    except json.JSONDecodeError:
        console.print(f"[red]Error: Invalid JSON in ABI file {name}.json[/red]")
        return []
    except IOError as e:
        console.print(f"[red]Error: Cannot read ABI file: {str(e)}[/red]")
        return []


# ── Web3 connection ───────────────────────────────────────────────────────────

def get_web3() -> Optional["Web3"]:
    """Return a connected Web3 instance or None."""
    if not WEB3_AVAILABLE:
        console.print("[red]✗ web3 not installed[/red]")
        console.print("  Install with: [yellow]pip install web3[/yellow]")
        return None
    
    if not DEFAULT_RPC:
        console.print("[red]✗ No RPC endpoint configured[/red]")
        console.print("  Set NEURACOIN_RPC environment variable")
        return None
    
    try:
        w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC))
        if not w3.is_connected():
            console.print(f"[red]✗ Cannot connect to RPC endpoint[/red]")
            console.print(f"  Endpoint: {DEFAULT_RPC}")
            return None
        return w3
    except Exception as e:
        console.print(f"[red]✗ Web3 connection error: {str(e)}[/red]")
        return None


def check_config() -> bool:
    """Verify required environment variables are set."""
    required = {
        "NEURACOIN_RPC": DEFAULT_RPC,
        "NRC_TOKEN_ADDRESS": NRC_ADDRESS,
        "JOB_REGISTRY_ADDR": JOB_REGISTRY,
    }
    
    missing = [name for name, value in required.items() if not value]
    
    if missing:
        console.print("[yellow]⚠ Missing configuration:[/yellow]")
        for var in missing:
            console.print(f"  - {var}")
        console.print("[dim]Set these environment variables and try again[/dim]")
        return False
    
    return True


# ── CLI root ──────────────────────────────────────────────────────────────────

@click.group()
@click.version_option("0.1.0", prog_name="neuracoin")
def cli():
    """NeuraCoin Protocol CLI — Decentralized AI Compute Network"""
    pass


# ── Status ────────────────────────────────────────────────────────────────────

@cli.command()
def status():
    """Show protocol status and network info."""
    console.print("\n[bold cyan]NeuraCoin Protocol Status[/bold cyan]")
    console.print("─" * 50)

    w3 = get_web3()
    if w3:
        try:
            block = w3.eth.get_block('latest')
            console.print(f"[green]✓ Connected[/green]  RPC: {DEFAULT_RPC}")
            console.print(f"  Latest block:    {block['number']:,}")
            console.print(f"  Chain ID:        {w3.eth.chain_id}")
        except Exception as e:
            console.print(f"[yellow]⚠ Cannot fetch block info: {str(e)}[/yellow]")
    else:
        console.print("[yellow]⚠ Running in offline mode[/yellow]")

    console.print(f"  Token:           NRC ({NRC_ADDRESS or '[dim]not configured[/dim]'})")
    console.print(f"  Job Registry:    {JOB_REGISTRY or '[dim]not configured[/dim]'}")
    console.print()


# ── Wallet ────────────────────────────────────────────────────────────────────

@cli.group()
def wallet():
    """Wallet operations (balance, send, stake)."""
    pass


@wallet.command()
@click