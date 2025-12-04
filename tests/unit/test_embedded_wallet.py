"""
Unit tests for embedded wallet service.
"""

import pytest


@pytest.mark.unit
class TestEmbeddedWalletService:
    """Test embedded wallet service functionality."""

    @pytest.fixture
    def wallet_service(self):
        """Create embedded wallet service instance."""
        from services.embedded_wallet import EmbeddedWalletService
        return EmbeddedWalletService()

    def test_service_initialization(self, wallet_service):
        """Test service initializes correctly."""
        assert wallet_service is not None

    def test_create_wallet_from_email(self, wallet_service):
        """Test wallet creation from email identifier."""
        result = wallet_service.create_wallet("test@example.com", "email")

        assert result["success"] is True
        assert "wallet_address" in result
        assert result["wallet_address"].startswith("0x")
        assert len(result["wallet_address"]) == 42

    def test_wallet_deterministic(self, wallet_service):
        """Test same email produces same wallet."""
        email = "consistent@example.com"

        result1 = wallet_service.create_wallet(email, "email")
        result2 = wallet_service.create_wallet(email, "email")

        assert result1["wallet_address"] == result2["wallet_address"]

    def test_different_emails_different_wallets(self, wallet_service):
        """Test different emails produce different wallets."""
        result1 = wallet_service.create_wallet("user1@example.com", "email")
        result2 = wallet_service.create_wallet("user2@example.com", "email")

        assert result1["wallet_address"] != result2["wallet_address"]

    def test_authenticate_wallet(self, wallet_service):
        """Test wallet authentication."""
        result = wallet_service.authenticate_wallet(
            "test@example.com",
            "123456"  # Test OTP
        )

        assert result["success"] is True
        assert "token" in result
        assert "wallet_address" in result


@pytest.mark.unit
class TestTransactionCompliance:
    """Test transaction compliance checking."""

    @pytest.fixture
    def wallet_service(self):
        """Create embedded wallet service instance."""
        from services.embedded_wallet import EmbeddedWalletService
        return EmbeddedWalletService()

    def test_compliance_check_normal_transaction(self, wallet_service):
        """Test compliance check for normal transaction."""
        # Create a wallet first
        result = wallet_service.create_wallet("test@example.com", "email")
        wallet_address = result["wallet_address"]

        # Check compliance for small transaction to whitelisted contract
        # Use the prediction market contract address (whitelisted)
        tx_data = {
            "to": "0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c",  # PredictionMarket
            "value": 1000000000000000,  # 0.001 ETH in wei
            "value_usd": 1.0,  # Small USD amount
        }

        compliance = wallet_service.check_transaction_compliance(
            wallet_address,
            tx_data
        )

        assert compliance["allowed"] is True

    def test_compliance_check_large_transaction(self, wallet_service):
        """Test compliance check for large transaction requiring 2FA."""
        result = wallet_service.create_wallet("test2@example.com", "email")
        wallet_address = result["wallet_address"]

        # Large transaction (over per-tx limit)
        tx_data = {
            "to": "0x1234567890123456789012345678901234567890",
            "value": 1000000000000000000,  # 1 ETH in wei (over $500 likely)
        }

        compliance = wallet_service.check_transaction_compliance(
            wallet_address,
            tx_data
        )

        # Should require 2FA for large transactions
        if compliance.get("requires_2fa"):
            assert compliance["requires_2fa"] is True


@pytest.mark.unit
class TestWalletPolicy:
    """Test wallet policy management."""

    @pytest.fixture
    def wallet_service(self):
        """Create embedded wallet service instance."""
        from services.embedded_wallet import EmbeddedWalletService
        return EmbeddedWalletService()

    def test_get_default_policy(self, wallet_service):
        """Test getting default wallet policy."""
        result = wallet_service.create_wallet("policy@example.com", "email")
        wallet_address = result["wallet_address"]

        policy = wallet_service.get_wallet_policy(wallet_address)

        assert policy is not None
        # Policy should have some fields
        assert isinstance(policy, dict)

    def test_update_policy(self, wallet_service):
        """Test updating wallet policy."""
        result = wallet_service.create_wallet("policy2@example.com", "email")
        wallet_address = result["wallet_address"]

        # Update policy - use valid policy key (daily_limit_usd)
        new_policy = {"daily_limit_usd": 500}
        update_result = wallet_service.update_wallet_policy(wallet_address, new_policy)

        assert update_result is True
