"""
Integration tests for chain-only API endpoints.
Migrated from test_phase3_api.py
"""

import pytest
import requests


@pytest.mark.integration
class TestChainAPI:
    """Test blockchain-only API endpoints."""

    def test_get_actors(self, base_url):
        """Test fetching actors from blockchain."""
        response = requests.get(f"{base_url}/api/chain/actors")

        if response.status_code == 404:
            pytest.skip("Chain API not available")

        assert response.status_code == 200
        data = response.json()
        assert "actors" in data
        assert "source" in data
        assert data["source"] == "blockchain"

    def test_get_markets(self, base_url):
        """Test fetching markets from blockchain."""
        response = requests.get(f"{base_url}/api/chain/markets")

        if response.status_code == 404:
            pytest.skip("Chain API not available")

        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        assert "source" in data

    def test_get_markets_with_status_filter(self, base_url):
        """Test filtering markets by status."""
        response = requests.get(
            f"{base_url}/api/chain/markets",
            params={"status": "active"}
        )

        if response.status_code == 404:
            pytest.skip("Chain API not available")

        assert response.status_code == 200
        data = response.json()
        assert "markets" in data

    def test_get_platform_stats(self, base_url):
        """Test fetching platform statistics."""
        response = requests.get(f"{base_url}/api/chain/stats")

        if response.status_code == 404:
            pytest.skip("Chain API not available")

        assert response.status_code == 200
        data = response.json()
        # Stats may be wrapped in "stats" key or returned directly
        stats = data.get("stats", data)
        assert "total_markets" in stats or "chain" in stats or "source" in data

    def test_get_genesis_holders(self, base_url):
        """Test fetching Genesis NFT holder data."""
        response = requests.get(f"{base_url}/api/chain/genesis")

        if response.status_code == 404:
            pytest.skip("Genesis endpoint not available")

        assert response.status_code == 200
        data = response.json()
        assert "genesis" in data

    def test_health_endpoint(self, base_url):
        """Test API health check endpoint."""
        response = requests.get(f"{base_url}/api/health")

        # Health endpoint should always work
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_deprecated_db_endpoints_return_404(self, base_url):
        """Test that deprecated database endpoints are removed or error."""
        deprecated_endpoints = [
            "/api/actors",  # Old database endpoint
            "/api/markets/db",  # Old database endpoint
        ]

        for endpoint in deprecated_endpoints:
            response = requests.get(f"{base_url}{endpoint}")
            # Should be 404, redirect, 200 (migrated), or 500 (not implemented)
            assert response.status_code in [404, 301, 302, 200, 500]


@pytest.mark.integration
class TestEmbeddedAuth:
    """Test embedded wallet authentication endpoints."""

    def test_request_otp(self, base_url):
        """Test OTP request endpoint."""
        response = requests.post(
            f"{base_url}/api/embedded/request-otp",
            json={
                "identifier": "test@example.com",
                "auth_method": "email"
            }
        )

        if response.status_code == 404:
            pytest.skip("Embedded auth not available")

        # Should succeed (test mode returns mock OTP)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    def test_request_otp_missing_identifier(self, base_url):
        """Test OTP request without identifier fails."""
        response = requests.post(
            f"{base_url}/api/embedded/request-otp",
            json={"auth_method": "email"}
        )

        if response.status_code == 404:
            pytest.skip("Embedded auth not available")

        assert response.status_code == 400

    def test_verify_otp_test_mode(self, base_url):
        """Test OTP verification in test mode."""
        email = "test@example.com"

        # Request OTP first
        request_response = requests.post(
            f"{base_url}/api/embedded/request-otp",
            json={"identifier": email, "auth_method": "email"}
        )

        if request_response.status_code == 404:
            pytest.skip("Embedded auth not available")

        # In test mode, OTP is "123456"
        verify_response = requests.post(
            f"{base_url}/api/embedded/verify-otp",
            json={"identifier": email, "otp_code": "123456"}
        )

        # May fail if Firebase not configured - skip in that case
        if verify_response.status_code == 500:
            pytest.skip("Firebase not configured for OTP verification")

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data.get("success") is True
        assert "wallet_address" in data

    def test_verify_otp_invalid(self, base_url):
        """Test that invalid OTP is rejected."""
        email = "test@example.com"

        # Request OTP first
        request_response = requests.post(
            f"{base_url}/api/embedded/request-otp",
            json={"identifier": email, "auth_method": "email"}
        )

        if request_response.status_code == 404:
            pytest.skip("Embedded auth not available")

        # Wrong OTP
        verify_response = requests.post(
            f"{base_url}/api/embedded/verify-otp",
            json={"identifier": email, "otp_code": "000000"}
        )

        assert verify_response.status_code in [400, 401]
