```python
"""
Pytest tests for NeuraCoin (NRC) token mint, transfer, and burn logic.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from decimal import Decimal
from typing import Dict, Tuple


class MockNRCToken:
    """Mock ERC20 token contract for testing NeuraCoin mechanics."""

    def __init__(self, initial_supply: int = 0):
        self.balances: Dict[str, int] = {}
        self.allowances: Dict[Tuple[str, str], int] = {}
        self.total_supply: int = initial_supply
        self.burnable: bool = True

    def mint(self, account: str, amount: int) -> bool:
        """Mint tokens to an account."""
        if amount <= 0:
            raise ValueError("Mint amount must be positive")
        self.balances[account] = self.balances.get(account, 0) + amount
        self.total_supply += amount
        return True

    def transfer(self, from_account: str, to_account: str, amount: int) -> bool:
        """Transfer tokens between accounts."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if self.balances.get(from_account, 0) < amount:
            raise ValueError("Insufficient balance")
        self.balances[from_account] -= amount
        self.balances[to_account] = self.balances.get(to_account, 0) + amount
        return True

    def burn(self, account: str, amount: int) -> bool:
        """Burn tokens from an account."""
        if not self.burnable:
            raise ValueError("Burning is disabled")
        if amount <= 0:
            raise ValueError("Burn amount must be positive")
        if self.balances.get(account, 0) < amount:
            raise ValueError("Insufficient balance to burn")
        self.balances[account] -= amount
        self.total_supply -= amount
        return True

    def approve(self, owner: str, spender: str, amount: int) -> bool:
        """Approve spender to transfer tokens on behalf of owner."""
        if amount < 0:
            raise ValueError("Approval amount cannot be negative")
        self.allowances[(owner, spender)] = amount
        return True

    def transfer_from(self, owner: str, spender: str, to_account: str, amount: int) -> bool:
        """Transfer tokens using allowance."""
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        allowance = self.allowances.get((owner, spender), 0)
        if allowance < amount:
            raise ValueError("Insufficient allowance")
        if self.balances.get(owner, 0) < amount:
            raise ValueError("Insufficient balance")
        self.balances[owner] -= amount
        self.balances[to_account] = self.balances.get(to_account, 0) + amount
        self.allowances[(owner, spender)] -= amount
        return True

    def balance_of(self, account: str) -> int:
        """Get balance of an account."""
        return self.balances.get(account, 0)


class TestNRCTokenMint:
    """Test cases for NRC token minting functionality."""

    @pytest.fixture
    def token(self) -> MockNRCToken:
        """Create a fresh token instance for each test."""
        return MockNRCToken(initial_supply=0)

    def test_mint_positive_amount(self, token: MockNRCToken) -> None:
        """Test minting positive amount of tokens."""
        assert token.mint("gpu_owner_1", 1000) is True
        assert token.balance_of("gpu_owner_1") == 1000
        assert token.total_supply == 1000

    def test_mint_to_multiple_accounts(self, token: MockNRCToken) -> None:
        """Test minting tokens to multiple accounts."""
        token.mint("account_a", 500)
        token.mint("account_b", 300)
        assert token.balance_of("account_a") == 500
        assert token.balance_of("account_b") == 300
        assert token.total_supply == 800

    def test_mint_incremental_amounts(self, token: MockNRCToken) -> None:
        """Test multiple mint operations to same account."""
        token.mint("gpu_owner", 100)
        token.mint("gpu_owner", 250)
        token.mint("gpu_owner", 150)
        assert token.balance_of("gpu_owner") == 500
        assert token.total_supply == 500

    def test_mint_zero_amount_raises_error(self, token: MockNRCToken) -> None:
        """Test that minting zero amount raises ValueError."""
        with pytest.raises(ValueError, match="Mint amount must be positive"):
            token.mint("account", 0)

    def test_mint_negative_amount_raises_error(self, token: MockNRCToken) -> None:
        """Test that minting negative amount raises ValueError."""
        with pytest.raises(ValueError, match="Mint amount must be positive"):
            token.mint("account", -500)

    def test_mint_large_amounts(self, token: MockNRCToken) -> None:
        """Test minting very large amounts."""
        large_amount = 10**18
        token.mint("account", large_amount)
        assert token.balance_of("account") == large_amount
        assert token.total_supply == large_amount

    def test_mint_preserves_existing_balance(self, token: MockNRCToken) -> None:
        """Test that minting adds to existing balance correctly."""
        token.balances["account"] = 1000
        token.total_supply = 1000
        token.mint("account", 500)
        assert token.balance_of("account") == 1500
        assert token.total_supply == 1500


class TestNRCTokenTransfer:
    """Test cases for NRC token transfer functionality."""

    @pytest.fixture
    def token(self) -> MockNRCToken:
        """Create a token instance with initial balances."""
        t = MockNRCToken()
        t.mint("sender", 1000)
        t.mint("recipient", 500)
        return t

    def test_transfer_valid_amount(self, token: MockNRCToken) -> None:
        """Test transferring valid amount between accounts."""
        assert token.transfer("sender", "recipient", 300) is True
        assert token.balance_of("sender") == 700
        assert token.balance_of("recipient") == 800
        assert token.total_supply == 1500

    def test_transfer_entire_balance(self, token: MockNRCToken) -> None:
        """Test transferring entire balance."""
        token.transfer("sender", "recipient", 1000)
        assert token.balance_of("sender") == 0
        assert token.balance_of("recipient") == 1500

    def test_transfer_to_new_account(self, token: MockNRCToken) -> None:
        """Test transferring to account with no prior balance."""
        token.transfer("sender", "new_account", 250)
        assert token.balance_of("new_account") == 250
        assert token.balance_of("sender") == 750

    def test_transfer_multiple_operations(self, token: MockNRCToken) -> None:
        """Test multiple sequential transfers."""
        token.transfer("sender", "recipient", 200)
        token.transfer("recipient", "sender", 100)
        token.transfer("sender", "recipient", 50)
        assert token.balance_of("sender") == 950
        assert token.balance_of("recipient") == 650

    def test_transfer_zero_amount_raises_error(self, token: MockNRCToken) -> None:
        """Test that transferring zero amount raises ValueError."""
        with pytest.raises(ValueError, match="Transfer amount must be positive"):
            token.transfer("sender", "recipient", 0)

    def test_transfer