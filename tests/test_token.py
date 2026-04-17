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
        """Fixture to provide a fresh token instance."""
        return MockNRCToken()

    def test_mint_tokens_basic(self, token: MockNRCToken):
        """Test basic token minting to an account."""
        account = "0x1234567890abcdef"
        amount = 1000

        result = token.mint(account, amount)

        assert result is True
        assert token.balance_of(account) == amount
        assert token.total_supply == amount

    def test_mint_multiple_accounts(self, token: MockNRCToken):
        """Test minting tokens to multiple accounts."""
        account_a = "0xaaaa"
        account_b = "0xbbbb"
        amount = 500

        token.mint(account_a, amount)
        token.mint(account_b, amount)

        assert token.balance_of(account_a) == amount
        assert token.balance_of(account_b) == amount
        assert token.total_supply == amount * 2

    def test_mint_accumulation(self, token: MockNRCToken):
        """Test minting multiple times to the same account."""
        account = "0x1111"

        token.mint(account, 100)
        token.mint(account, 200)
        token.mint(account, 300)

        assert token.balance_of(account) == 600
        assert token.total_supply == 600

    def test_mint_invalid_amount(self, token: MockNRCToken):
        """Test that minting with invalid amounts raises error."""
        account = "0x1234"

        with pytest.raises(ValueError, match="Mint amount must be positive"):
            token.mint(account, 0)

        with pytest.raises(ValueError, match="Mint amount must be positive"):
            token.mint(account, -100)

    def test_mint_large_amount(self, token: MockNRCToken):
        """Test minting very large amounts."""
        account = "0xbeef"
        large_amount = 10**18  # 1 billion tokens with 18 decimals

        token.mint(account, large_amount)

        assert token.balance_of(account) == large_amount
        assert token.total_supply == large_amount


class TestNRCTokenTransfer:
    """Test cases for NRC token transfer functionality."""

    @pytest.fixture
    def token_with_balance(self) -> MockNRCToken:
        """Fixture providing a token with pre-minted balances."""
        token = MockNRCToken()
        token.mint("0xaccount_a", 1000)
        token.mint("0xaccount_b", 500)
        return token

    def test_transfer_tokens_basic(self, token_with_balance: MockNRCToken):
        """Test basic token transfer between accounts."""
        token = token_with_balance
        from_account = "0xaccount_a"
        to_account = "0xaccount_b"
        amount = 100

        initial_from_balance = token.balance_of(from_account)
        initial_to_balance = token.balance_of(to_account)

        result = token.transfer(from_account, to_account, amount)

        assert result is True
        assert token.balance_of(from_account) == initial_from_balance - amount
        assert token.balance_of(to_account) == initial_to_balance + amount
        assert token.total_supply == 1500  # Total supply unchanged

    def test_transfer_full_balance(self, token_with_balance: MockNRCToken):
        """Test transferring entire balance."""
        token = token_with_balance
        from_account = "0xaccount_a"
        to_account = "0xaccount_c"
        amount = 1000

        token.transfer(from_account, to_account, amount)

        assert token.balance_of(from_account) == 0
        assert token.balance_of(to_account) == amount

    def test_transfer_insufficient_balance(self, token_with_balance: MockNRCToken):
        """Test that transfer with insufficient balance fails."""
        token = token_with_balance
        from_account = "0xaccount_a"
        to_account = "0xaccount_b"

        with pytest.raises(ValueError, match="Insufficient balance"):
            token.transfer(from_account, to_account, 2000)

    def test_transfer_invalid_amount(self, token_with_balance: MockNRCToken):
        """Test that transfer with invalid amounts raises error."""
        token = token_with_balance

        with pytest.raises(ValueError, match="Transfer amount must be positive"):
            token.transfer("0xaccount_a", "0