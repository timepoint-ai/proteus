"""
Unit tests for V2 Resolution Service
Tests the market resolution logic without blockchain calls
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

# Mock the blockchain and xcom services before importing
with patch('services.v2_resolution.BaseBlockchainService'), \
     patch('services.v2_resolution.XComAPIService'):
    from services.v2_resolution import V2ResolutionService


class TestV2ResolutionServiceInit:
    """Test V2ResolutionService initialization"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    @patch('services.v2_resolution.Account')
    def test_init_without_owner_key(self, mock_account, mock_xcom, mock_blockchain):
        """Service initializes without owner key"""
        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            assert service.owner_private_key is None
            assert service.owner_address == '0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA'

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    @patch('services.v2_resolution.Account')
    def test_init_with_valid_owner_key(self, mock_account, mock_xcom, mock_blockchain):
        """Service initializes with valid owner key"""
        mock_account_instance = Mock()
        mock_account_instance.address = '0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA'
        mock_account.from_key.return_value = mock_account_instance

        with patch.dict('os.environ', {
            'OWNER_PRIVATE_KEY': '0x' + 'a' * 64,
            'OWNER_ADDRESS': '0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA'
        }):
            service = V2ResolutionService()
            assert service.owner_private_key == '0x' + 'a' * 64


class TestGetPendingMarkets:
    """Test get_pending_markets method"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_no_pending_markets(self, mock_xcom, mock_blockchain):
        """Returns empty list when no pending markets"""
        mock_bc = Mock()
        mock_bc.get_v2_market_count.return_value = 0
        mock_blockchain.return_value = mock_bc

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.get_pending_markets()
            assert result == []

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_finds_pending_markets(self, mock_xcom, mock_blockchain):
        """Correctly identifies pending markets"""
        mock_bc = Mock()
        mock_bc.get_v2_market_count.return_value = 2

        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        future_time = int((datetime.now() + timedelta(hours=1)).timestamp())

        # Market 0: ended, not resolved (pending)
        # Market 1: not ended yet (active)
        mock_bc.get_v2_market.side_effect = [
            {'id': 0, 'resolved': False, 'end_time': past_time, 'actor_handle': '@test'},
            {'id': 1, 'resolved': False, 'end_time': future_time, 'actor_handle': '@test2'}
        ]
        mock_bc.get_v2_market_submissions.return_value = [1, 2]  # 2 submissions

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.get_pending_markets()
            assert len(result) == 1
            assert result[0]['id'] == 0
            assert result[0]['can_resolve'] is True

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_pending_market_insufficient_submissions(self, mock_xcom, mock_blockchain):
        """Pending market with <2 submissions cannot resolve"""
        mock_bc = Mock()
        mock_bc.get_v2_market_count.return_value = 1

        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': False, 'end_time': past_time, 'actor_handle': '@test'}
        mock_bc.get_v2_market_submissions.return_value = [1]  # Only 1 submission

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.get_pending_markets()
            assert len(result) == 1
            assert result[0]['can_resolve'] is False


class TestResolveMarketValidation:
    """Test resolve_market validation logic"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_nonexistent_market(self, mock_xcom, mock_blockchain):
        """Returns error for nonexistent market"""
        mock_bc = Mock()
        mock_bc.get_v2_market.return_value = None

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.resolve_market(999, "test text")
            assert result['success'] is False
            assert 'not found' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_already_resolved(self, mock_xcom, mock_blockchain):
        """Returns error for already resolved market"""
        mock_bc = Mock()
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': True}

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.resolve_market(0, "test text")
            assert result['success'] is False
            assert 'already resolved' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_not_ended(self, mock_xcom, mock_blockchain):
        """Returns error if market has not ended"""
        mock_bc = Mock()
        future_time = int((datetime.now() + timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': False, 'end_time': future_time}

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.resolve_market(0, "test text")
            assert result['success'] is False
            assert 'not ended' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_insufficient_submissions(self, mock_xcom, mock_blockchain):
        """Returns error if fewer than 2 submissions"""
        mock_bc = Mock()
        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': False, 'end_time': past_time}
        mock_bc.get_v2_market_submissions.return_value = [1]  # Only 1 submission

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.resolve_market(0, "test text")
            assert result['success'] is False
            assert 'at least 2 submissions' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_empty_text(self, mock_xcom, mock_blockchain):
        """Returns error for empty actual text"""
        mock_bc = Mock()
        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': False, 'end_time': past_time}
        mock_bc.get_v2_market_submissions.return_value = [1, 2]

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.resolve_market(0, "")
            assert result['success'] is False
            assert 'cannot be empty' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_resolve_text_too_long(self, mock_xcom, mock_blockchain):
        """Returns error for text over 280 chars"""
        mock_bc = Mock()
        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {'id': 0, 'resolved': False, 'end_time': past_time}
        mock_bc.get_v2_market_submissions.return_value = [1, 2]

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            long_text = "x" * 300
            result = service.resolve_market(0, long_text)
            assert result['success'] is False
            assert 'too long' in result['error']


class TestGetMarketForResolution:
    """Test get_market_for_resolution method"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_market_not_found(self, mock_xcom, mock_blockchain):
        """Returns None for nonexistent market"""
        mock_bc = Mock()
        mock_bc.get_v2_market.return_value = None

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.get_market_for_resolution(999)
            assert result is None

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_market_with_submissions(self, mock_xcom, mock_blockchain):
        """Returns market with submissions populated"""
        mock_bc = Mock()
        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        mock_bc.get_v2_market.return_value = {
            'id': 0,
            'resolved': False,
            'end_time': past_time,
            'actor_handle': '@elonmusk'
        }
        mock_bc.get_v2_market_submissions.return_value = [1, 2]
        mock_bc.get_v2_submission.side_effect = [
            {'id': 1, 'predicted_text': 'Hello world'},
            {'id': 2, 'predicted_text': 'Hello there'}
        ]

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.get_market_for_resolution(0)
            assert result is not None
            assert result['submission_count'] == 2
            assert result['can_resolve'] is True
            assert len(result['submissions']) == 2


class TestGetResolutionStats:
    """Test get_resolution_stats method"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_empty_stats(self, mock_xcom, mock_blockchain):
        """Returns stats with zero markets"""
        mock_bc = Mock()
        mock_bc.get_v2_market_count.return_value = 0
        mock_bc.get_v2_pending_fees.return_value = 0

        mock_xcom_instance = Mock()
        mock_xcom_instance.get_api_status.return_value = {'api_configured': False}
        mock_xcom.return_value = mock_xcom_instance

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc
            service.xcom = mock_xcom_instance

            result = service.get_resolution_stats()
            assert result['total_markets'] == 0
            assert result['resolved_markets'] == 0
            assert result['pending_resolution'] == 0
            assert result['active_markets'] == 0

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_mixed_stats(self, mock_xcom, mock_blockchain):
        """Returns correct counts for mixed market states"""
        mock_bc = Mock()
        mock_bc.get_v2_market_count.return_value = 3

        past_time = int((datetime.now() - timedelta(hours=1)).timestamp())
        future_time = int((datetime.now() + timedelta(hours=1)).timestamp())

        mock_bc.get_v2_market.side_effect = [
            {'id': 0, 'resolved': True, 'end_time': past_time, 'total_pool': '1.0'},  # resolved
            {'id': 1, 'resolved': False, 'end_time': past_time, 'total_pool': '2.0'},  # pending
            {'id': 2, 'resolved': False, 'end_time': future_time, 'total_pool': '3.0'}  # active
        ]
        mock_bc.get_v2_pending_fees.return_value = 0.1

        mock_xcom_instance = Mock()
        mock_xcom_instance.get_api_status.return_value = {'api_configured': True}
        mock_xcom.return_value = mock_xcom_instance

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc
            service.xcom = mock_xcom_instance

            result = service.get_resolution_stats()
            assert result['total_markets'] == 3
            assert result['resolved_markets'] == 1
            assert result['pending_resolution'] == 1
            assert result['active_markets'] == 1
            assert result['total_pool'] == '6.0'


class TestWithdrawFees:
    """Test withdraw_fees method"""

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_withdraw_without_owner_key(self, mock_xcom, mock_blockchain):
        """Returns error without owner key"""
        mock_bc = Mock()
        mock_bc.contracts = {'PredictionMarketV2': Mock()}

        with patch.dict('os.environ', {}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc

            result = service.withdraw_fees()
            assert result['success'] is False
            assert 'Owner private key not configured' in result['error']

    @patch('services.v2_resolution.BaseBlockchainService')
    @patch('services.v2_resolution.XComAPIService')
    def test_withdraw_no_fees(self, mock_xcom, mock_blockchain):
        """Returns error when no fees to withdraw"""
        mock_bc = Mock()
        mock_bc.contracts = {'PredictionMarketV2': Mock()}
        mock_bc.get_v2_pending_fees.return_value = 0

        with patch.dict('os.environ', {'OWNER_PRIVATE_KEY': '0x' + 'a' * 64}, clear=True):
            service = V2ResolutionService()
            service.blockchain = mock_bc
            service.owner_private_key = '0x' + 'a' * 64

            result = service.withdraw_fees()
            assert result['success'] is False
            assert 'No fees to withdraw' in result['error']
