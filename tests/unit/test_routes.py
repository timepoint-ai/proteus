"""
Integration tests for route handlers.
Tests API endpoints using Flask test client.

These tests require the full Flask app with Celery.
They are marked as integration tests to be run separately.
"""

import pytest
from unittest.mock import patch, MagicMock

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestBaseApiRoutes:
    """Tests for base API routes (/api/base/*)."""

    @pytest.mark.unit
    def test_health_endpoint_returns_200(self, client):
        """GET /api/base/health returns 200."""
        response = client.get('/api/base/health')
        assert response.status_code == 200
        data = response.get_json()
        assert 'status' in data

    @pytest.mark.unit
    def test_health_endpoint_returns_json(self, client):
        """GET /api/base/health returns JSON response."""
        response = client.get('/api/base/health')
        assert response.content_type == 'application/json'


class TestChainApiActorsRoute:
    """Tests for /api/chain/actors endpoint."""

    @pytest.mark.unit
    def test_actors_endpoint_returns_json(self, client):
        """GET /api/chain/actors returns JSON."""
        response = client.get('/api/chain/actors')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    @pytest.mark.unit
    def test_actors_endpoint_returns_list_structure(self, client):
        """GET /api/chain/actors returns expected structure."""
        response = client.get('/api/chain/actors')
        data = response.get_json()
        assert 'actors' in data
        assert 'total' in data
        assert 'source' in data
        assert data['source'] == 'blockchain'

    @pytest.mark.unit
    def test_actors_returns_empty_list_when_no_contract(self, client):
        """GET /api/chain/actors returns empty list when contract unavailable."""
        with patch('routes.api_chain.blockchain_service') as mock_service:
            mock_service.contracts.get.return_value = None
            response = client.get('/api/chain/actors')
            data = response.get_json()
            assert data['actors'] == []
            assert data['total'] == 0


class TestChainApiMarketsRoute:
    """Tests for /api/chain/markets endpoint."""

    @pytest.mark.unit
    def test_markets_endpoint_returns_json(self, client):
        """GET /api/chain/markets returns JSON."""
        response = client.get('/api/chain/markets')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    @pytest.mark.unit
    def test_markets_endpoint_returns_list_structure(self, client):
        """GET /api/chain/markets returns expected structure."""
        response = client.get('/api/chain/markets')
        data = response.get_json()
        assert 'markets' in data
        assert 'total' in data
        assert 'source' in data
        assert data['source'] == 'blockchain'

    @pytest.mark.unit
    def test_markets_returns_empty_when_no_contract(self, client):
        """GET /api/chain/markets returns empty when contract unavailable."""
        with patch('routes.api_chain.blockchain_service') as mock_service:
            mock_service.contracts.get.return_value = None
            response = client.get('/api/chain/markets')
            data = response.get_json()
            assert data['markets'] == []
            assert data['total'] == 0

    @pytest.mark.unit
    def test_markets_accepts_status_filter(self, client):
        """GET /api/chain/markets accepts status query parameter."""
        response = client.get('/api/chain/markets?status=active')
        assert response.status_code == 200
        # Should not error even if filtering returns empty


class TestChainApiStatsRoute:
    """Tests for /api/chain/stats endpoint."""

    @pytest.mark.unit
    def test_stats_endpoint_returns_json(self, client):
        """GET /api/chain/stats returns JSON."""
        response = client.get('/api/chain/stats')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    @pytest.mark.unit
    def test_stats_returns_expected_fields(self, client):
        """GET /api/chain/stats returns expected fields."""
        response = client.get('/api/chain/stats')
        data = response.get_json()
        expected_fields = [
            'total_markets', 'active_markets', 'resolved_markets',
            'total_volume', 'total_actors', 'genesis_nft_holders',
            'gas_price', 'source'
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"


class TestChainApiGenesisHoldersRoute:
    """Tests for /api/chain/genesis/holders endpoint."""

    @pytest.mark.unit
    def test_genesis_holders_returns_json(self, client):
        """GET /api/chain/genesis/holders returns JSON."""
        response = client.get('/api/chain/genesis/holders')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    @pytest.mark.unit
    def test_genesis_holders_returns_expected_structure(self, client):
        """GET /api/chain/genesis/holders returns expected structure."""
        response = client.get('/api/chain/genesis/holders')
        data = response.get_json()
        assert 'holders' in data
        assert 'total_holders' in data
        assert 'total_supply' in data
        assert data['total_supply'] == 100  # Fixed supply


class TestAuthRoutes:
    """Tests for authentication routes."""

    @pytest.mark.unit
    def test_nonce_endpoint_returns_nonce(self, client):
        """GET /auth/nonce/<address> returns nonce."""
        test_address = "0x1234567890123456789012345678901234567890"
        response = client.get(f'/auth/nonce/{test_address}')
        assert response.status_code == 200
        data = response.get_json()
        assert 'nonce' in data
        assert 'message' in data

    @pytest.mark.unit
    def test_nonce_generates_unique_values(self, client):
        """GET /auth/nonce/<address> generates unique nonces."""
        test_address = "0x1234567890123456789012345678901234567890"
        response1 = client.get(f'/auth/nonce/{test_address}')
        response2 = client.get(f'/auth/nonce/{test_address}')
        nonce1 = response1.get_json()['nonce']
        nonce2 = response2.get_json()['nonce']
        assert nonce1 != nonce2

    @pytest.mark.unit
    def test_verify_requires_all_fields(self, client):
        """POST /auth/verify requires address, signature, message."""
        # Missing all fields
        response = client.post('/auth/verify', json={})
        assert response.status_code == 400

        # Missing signature
        response = client.post('/auth/verify', json={
            'address': '0x123',
            'message': 'test'
        })
        assert response.status_code == 400

    @pytest.mark.unit
    def test_refresh_requires_auth_header(self, client):
        """POST /auth/refresh requires Authorization header."""
        response = client.post('/auth/refresh')
        assert response.status_code == 401

    @pytest.mark.unit
    def test_jwt_status_returns_unauthenticated_without_token(self, client):
        """GET /auth/jwt-status returns unauthenticated without token."""
        response = client.get('/auth/jwt-status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False


class TestEmbeddedAuthRoutes:
    """Tests for embedded wallet authentication routes."""

    @pytest.mark.unit
    def test_send_otp_requires_email(self, client):
        """POST /api/embedded/auth/send-otp requires email."""
        response = client.post('/api/embedded/auth/send-otp', json={})
        assert response.status_code == 400

    @pytest.mark.unit
    def test_verify_otp_requires_email_and_otp(self, client):
        """POST /api/embedded/auth/verify-otp requires email and otp."""
        response = client.post('/api/embedded/auth/verify-otp', json={
            'email': 'test@example.com'
        })
        assert response.status_code == 400

    @pytest.mark.unit
    def test_auth_status_returns_unauthenticated(self, client):
        """GET /api/embedded/auth/status returns unauthenticated by default."""
        response = client.get('/api/embedded/auth/status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False


class TestErrorHandling:
    """Tests for error handling across routes."""

    @pytest.mark.unit
    def test_404_returns_json(self, client):
        """404 errors return JSON response."""
        response = client.get('/nonexistent/route')
        assert response.status_code == 404
        # Should be JSON if error handlers are registered
        assert response.content_type == 'application/json'

    @pytest.mark.unit
    def test_invalid_json_returns_400(self, client):
        """Invalid JSON body returns 400."""
        response = client.post(
            '/auth/verify',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code == 400
