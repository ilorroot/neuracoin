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

# ── ABI loading ───────────────────────────────────────────────────────────────

def load_abi(name: str) -> list:
    """Load contract ABI from the contracts/ directory."""
    abi_path = Path(__file__).parent.parent / "contracts" / f"{name}.json"
    if not abi_path.exists():
        return []
    with open(abi_path) as f:
        return json.load(f).get("abi", [])


# ── Web3 connection ───────────────────────────────────────────────────────────

def get_web3() -> Optional["Web3"]:
    """Return a connected Web3 instance or None."""
    if not WEB3_AVAILABLE:
        console.print("[red]web3 not installed. Run: pip install web3[/red]")
        return None
    w3 = Web3(Web3.HTTPProvider(DEFAULT_RPC))
    if not w3.is_connected():
        console.print(f"[red]Cannot connect to RPC: {DEFAULT_RPC}[/red]")
        return None
    return w3


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
    console.print("─" * 40)

    w3 = get_web3()
    if w3:
        block = w3.eth.get_block('latest')number
        console.print(f"[green]✓ Connected[/green]  RPC: {DEFAULT_RPC}")
        console.print(f"  Latest block:  {block:,}")
    else:
        console.print("[yellow]⚠ Running in offline mode[/yellow]")

    console.print(f"  Token:         NRC ({NRC_ADDRESS or 'not configured'})")
    console.print(f"  Job Registry:  {JOB_REGISTRY or 'not configured'}")
    console.print()


# ── Wallet ────────────────────────────────────────────────────────────────────

@cli.group()
def wallet():
    """Wallet and balance commands."""
    pass


@wallet.command("balance")
@click.option("--address", "-a", required=True, help="Wallet address to check")
def wallet_balance(address: str):
    """Check NRC token balance for an address."""
    w3 = get_web3()
    if not w3:
        return

    if not NRC_ADDRESS:
        console.print("[red]NRC_TOKEN_ADDRESS not set in environment.[/red]")
        return

    abi = load_abi("NeuraCoin")
    if not abi:
        console.print("[yellow]ABI not found — compile contracts first.[/yellow]")
        return

    contract = w3.eth.contract(address=Web3.to_checksum_address(NRC_ADDRESS), abi=abi)
    raw      = contract.functions.balanceOf(Web3.to_checksum_address(address)).call()
    balance  = raw / 10**18

    console.print(f"\n[bold]Address:[/bold] {address}")
    console.print(f"[bold]Balance:[/bold] [green]{balance:,.2f} NRC[/green]\n")


# ── Jobs ──────────────────────────────────────────────────────────────────────

@cli.group()
def jobs():
    """Compute job management."""
    pass


@jobs.command("list")
@click.option("--status", "-s", default="open", type=click.Choice(["open", "assigned", "completed", "all"]))
def jobs_list(status: str):
    """List compute jobs on the network."""
    w3 = get_web3()
    if not w3:
        return

    if not JOB_REGISTRY:
        console.print("[red]JOB_REGISTRY_ADDR not set in environment.[/red]")
        return

    abi   = load_abi("JobRegistry")
    if not abi:
        console.print("[yellow]ABI not found — compile contracts first.[/yellow]")
        return

    registry = w3.eth.contract(address=Web3.to_checksum_address(JOB_REGISTRY), abi=abi)
    total    = registry.functions.totalJobs().call()

    table = Table(title=f"NeuraCoin Jobs ({status})")
    table.add_column("ID",        style="cyan")
    table.add_column("Status",    style="green")
    table.add_column("Requester", style="dim")
    table.add_column("Stake (NRC)")

    status_map = {"open": 0, "assigned": 1, "completed": 2}

    for job_id in range(total):
        job = registry.functions.getJob(job_id).call()
        job_status_code = job[7]  # status enum index
        if status != "all" and job_status_code != status_map.get(status, -1):
            continue
        status_labels = ["Open", "Assigned", "Completed", "Disputed", "Cancelled"]
        table.add_row(
            str(job_id),
            status_labels[job_status_code],
            job[1][:10] + "...",
            f"{job[2] / 10**18:,.1f}",
        )

    console.print(table)


@jobs.command("submit")
@click.option("--spec",  "-s", required=True, help="Path to job spec JSON file")
@click.option("--stake", "-n", required=True, type=float, help="NRC amount to stake")
def jobs_submit(spec: str, stake: float):
    """Submit a new compute job."""
    spec_path = Path(spec)
    if not spec_path.exists():
        console.print(f"[red]Spec file not found: {spec}[/red]")
        return

    console.print(f"\n[bold]Submitting job...[/bold]")
    console.print(f"  Spec:  {spec}")
    console.print(f"  Stake: {stake:,.2f} NRC")
    console.print("\n[yellow]Connect to a live network to submit jobs.[/yellow]\n")


# ── Provider ──────────────────────────────────────────────────────────────────

@cli.group()
def provider():
    """Compute provider management."""
    pass


@provider.command("register")
def provider_register():
    """Register as a compute provider (stakes 1,000 NRC)."""
    console.print("\n[bold]Registering as compute provider...[/bold]")
    console.print("  Required stake: [cyan]1,000 NRC[/cyan]")
    console.print("\n[yellow]Connect to a live network and set NEURACOIN_KEY to register.[/yellow]\n")


@provider.command("status")
@click.option("--address", "-a", required=True, help="Provider address to check")
def provider_status(address: str):
    """Check provider registration and stake status."""
    console.print(f"\n[bold]Provider:[/bold] {address}")
    console.print("[yellow]Connect to a live network to check provider status.[/yellow]\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
