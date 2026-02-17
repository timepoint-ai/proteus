"""
Shared pytest fixtures for Proteus tests.
"""

import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def base_url():
    """Base URL for API testing."""
    return os.environ.get("TEST_BASE_URL", "http://localhost:5000")


@pytest.fixture(scope="session")
def rpc_url():
    """RPC URL for BASE Sepolia."""
    return os.environ.get("RPC_URL", "https://sepolia.base.org")


@pytest.fixture(scope="session")
def chain_id():
    """BASE Sepolia chain ID."""
    return 84532


# =============================================================================
# Web3 Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def web3(rpc_url):
    """Create Web3 provider for BASE Sepolia."""
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    return w3


@pytest.fixture
def test_wallet():
    """Create a fresh test wallet for each test."""
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex(),
        "account": account
    }


@pytest.fixture
def funded_wallet():
    """
    Return a pre-funded test wallet.
    Uses DEPLOYER_PRIVATE_KEY from environment if available.
    """
    private_key = os.environ.get("DEPLOYER_PRIVATE_KEY")
    if private_key:
        account = Account.from_key(private_key)
        return {
            "address": account.address,
            "private_key": private_key,
            "account": account
        }
    # Fallback to creating a new wallet (won't have funds)
    account = Account.create()
    return {
        "address": account.address,
        "private_key": account.key.hex(),
        "account": account
    }


# =============================================================================
# Flask App Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def app():
    """Create Flask application for testing."""
    # Import here to avoid circular imports
    from app import app as flask_app

    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    return flask_app


@pytest.fixture(scope="session")
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client, test_wallet, base_url):
    """
    Get authenticated headers for a test wallet.
    Returns headers dict with Authorization Bearer token.
    """
    import requests

    address = test_wallet["address"]
    private_key = test_wallet["private_key"]

    # Get nonce
    nonce_response = requests.get(f"{base_url}/auth/nonce/{address}")
    if nonce_response.status_code != 200:
        pytest.skip("Auth service not available")

    nonce_data = nonce_response.json()
    message = nonce_data["message"]

    # Sign message
    message_encoded = encode_defunct(text=message)
    signed = Account.sign_message(message_encoded, private_key)
    signature = signed.signature.hex()

    # Verify and get token
    verify_response = requests.post(
        f"{base_url}/auth/verify",
        json={
            "address": address,
            "signature": signature,
            "message": message
        }
    )

    if verify_response.status_code != 200:
        pytest.skip("Auth verification failed")

    token = verify_response.json().get("token")
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Contract Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def contract_addresses():
    """Contract addresses for BASE Sepolia."""
    return {
        "genesis_nft": os.environ.get(
            "GENESIS_NFT_ADDRESS",
            "0x1A5D4475881B93e876251303757E60E524286A24"
        ),
        "payout_manager": os.environ.get(
            "PAYOUT_MANAGER_ADDRESS",
            "0xE9eE183b76A8BDfDa8EA926b2f44137Aa65379B5"
        ),
        "prediction_market": os.environ.get(
            "PREDICTION_MARKET_ADDRESS",
            "0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c"
        ),
        "oracle": os.environ.get(
            "ORACLE_ADDRESS",
            "0x7EF22e27D44E3f4Cc2f133BB4ab2065D180be3C1"
        ),
    }


# =============================================================================
# Utility Fixtures
# =============================================================================

@pytest.fixture
def sign_message(test_wallet):
    """Factory fixture to sign messages with test wallet."""
    def _sign(message: str) -> str:
        message_encoded = encode_defunct(text=message)
        signed = Account.sign_message(
            message_encoded,
            test_wallet["private_key"]
        )
        return signed.signature.hex()
    return _sign


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_market_data():
    """Sample data for creating a test market."""
    return {
        "actor_id": 1,
        "description": "Test prediction market",
        "end_time": 1735689600,  # Future timestamp
        "oracles": ["0x1234567890123456789012345678901234567890"]
    }


@pytest.fixture
def sample_submission_data():
    """Sample data for creating a test submission."""
    return {
        "market_id": 0,
        "predicted_text": "This is a test prediction"
    }


# =============================================================================
# Markers
# =============================================================================

def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_rpc: Tests requiring RPC connection")
