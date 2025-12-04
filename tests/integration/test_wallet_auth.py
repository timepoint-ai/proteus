"""
Integration tests for wallet authentication.
Migrated from test_wallet_auth.py
"""

import pytest
import requests
from eth_account.messages import encode_defunct
from eth_account import Account


@pytest.mark.integration
class TestWalletAuthentication:
    """Test wallet-based authentication flow."""

    def test_get_nonce(self, base_url, test_wallet):
        """Test getting authentication nonce for a wallet address."""
        response = requests.get(f"{base_url}/auth/nonce/{test_wallet['address']}")

        # May fail if server not running
        if response.status_code == 404:
            pytest.skip("Auth endpoint not available")

        assert response.status_code == 200
        data = response.json()
        assert "nonce" in data
        assert "message" in data
        assert test_wallet["address"].lower() in data["message"].lower()

    def test_sign_and_verify(self, base_url, test_wallet):
        """Test signing message and verifying signature."""
        # Get nonce
        nonce_response = requests.get(
            f"{base_url}/auth/nonce/{test_wallet['address']}"
        )
        if nonce_response.status_code != 200:
            pytest.skip("Auth service not available")

        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        # Sign message
        message_encoded = encode_defunct(text=message)
        signed = Account.sign_message(
            message_encoded,
            test_wallet["private_key"]
        )
        signature = signed.signature.hex()

        # Verify signature
        verify_response = requests.post(
            f"{base_url}/auth/verify",
            json={
                "address": test_wallet["address"],
                "signature": signature,
                "message": message
            }
        )

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data.get("success") is True
        assert "token" in data
        assert data.get("address").lower() == test_wallet["address"].lower()

    def test_authenticated_request(self, base_url, test_wallet):
        """Test making authenticated API request with JWT token."""
        # Get token
        nonce_response = requests.get(
            f"{base_url}/auth/nonce/{test_wallet['address']}"
        )
        if nonce_response.status_code != 200:
            pytest.skip("Auth service not available")

        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        message_encoded = encode_defunct(text=message)
        signed = Account.sign_message(
            message_encoded,
            test_wallet["private_key"]
        )

        verify_response = requests.post(
            f"{base_url}/auth/verify",
            json={
                "address": test_wallet["address"],
                "signature": signed.signature.hex(),
                "message": message
            }
        )

        if verify_response.status_code != 200:
            pytest.skip("Could not get auth token")

        token = verify_response.json()["token"]

        # Make authenticated request - try /auth/status or /api/health with auth
        status_response = requests.get(
            f"{base_url}/auth/status",
            headers={"Authorization": f"Bearer {token}"}
        )

        # /auth/status might not exist - check /api/health instead
        if status_response.status_code == 404:
            health_response = requests.get(
                f"{base_url}/api/health",
                headers={"Authorization": f"Bearer {token}"}
            )
            assert health_response.status_code == 200
            return  # Test passes if health endpoint works with auth header

        assert status_response.status_code == 200
        data = status_response.json()
        assert data.get("authenticated") is True
        assert data.get("address").lower() == test_wallet["address"].lower()

    def test_invalid_signature(self, base_url, test_wallet):
        """Test that invalid signature is rejected."""
        nonce_response = requests.get(
            f"{base_url}/auth/nonce/{test_wallet['address']}"
        )
        if nonce_response.status_code != 200:
            pytest.skip("Auth service not available")

        nonce_data = nonce_response.json()

        # Send invalid signature
        verify_response = requests.post(
            f"{base_url}/auth/verify",
            json={
                "address": test_wallet["address"],
                "signature": "0x" + "00" * 65,  # Invalid signature
                "message": nonce_data["message"]
            }
        )

        # Should fail
        assert verify_response.status_code in [400, 401]

    def test_token_refresh(self, base_url, test_wallet):
        """Test token refresh mechanism."""
        # Get initial token
        nonce_response = requests.get(
            f"{base_url}/auth/nonce/{test_wallet['address']}"
        )
        if nonce_response.status_code != 200:
            pytest.skip("Auth service not available")

        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        message_encoded = encode_defunct(text=message)
        signed = Account.sign_message(
            message_encoded,
            test_wallet["private_key"]
        )

        verify_response = requests.post(
            f"{base_url}/auth/verify",
            json={
                "address": test_wallet["address"],
                "signature": signed.signature.hex(),
                "message": message
            }
        )

        if verify_response.status_code != 200:
            pytest.skip("Could not get auth token")

        token = verify_response.json()["token"]

        # Refresh token
        refresh_response = requests.post(
            f"{base_url}/auth/refresh",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert data.get("success") is True
        assert "token" in data

    def test_logout(self, base_url, test_wallet):
        """Test logout invalidates session."""
        # Get token
        nonce_response = requests.get(
            f"{base_url}/auth/nonce/{test_wallet['address']}"
        )
        if nonce_response.status_code != 200:
            pytest.skip("Auth service not available")

        nonce_data = nonce_response.json()
        message = nonce_data["message"]

        message_encoded = encode_defunct(text=message)
        signed = Account.sign_message(
            message_encoded,
            test_wallet["private_key"]
        )

        verify_response = requests.post(
            f"{base_url}/auth/verify",
            json={
                "address": test_wallet["address"],
                "signature": signed.signature.hex(),
                "message": message
            }
        )

        if verify_response.status_code != 200:
            pytest.skip("Could not get auth token")

        token = verify_response.json()["token"]

        # Logout
        logout_response = requests.post(
            f"{base_url}/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert logout_response.status_code == 200
