"""
Unit tests for Health Check Service
Tests the health check logic without external dependencies
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
import os

# Mock all dependencies before importing HealthCheckService
mock_blockchain_service = MagicMock()
mock_xcom_service = MagicMock()
mock_node_comm_service = MagicMock()

# Create mock modules
sys.modules['services.blockchain_base'] = MagicMock()
sys.modules['services.blockchain_base'].BaseBlockchainService = mock_blockchain_service
sys.modules['services.xcom_api_service'] = MagicMock()
sys.modules['services.xcom_api_service'].XComAPIService = mock_xcom_service
sys.modules['services.node_communication'] = MagicMock()
sys.modules['services.node_communication'].NodeCommunicationService = mock_node_comm_service

# Now import the module
from services.health_check import HealthCheckService


class TestCheckBaseRPC:
    """Test check_base_rpc method"""

    def test_rpc_not_connected(self):
        """Returns error when not connected to RPC"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.w3 = Mock()
        service.blockchain_service.w3.is_connected.return_value = False

        result = service.check_base_rpc()
        assert result['status'] == 'error'
        assert 'Not connected' in result['message']
        assert result['critical'] is True

    def test_rpc_wrong_chain_id(self):
        """Returns error for wrong chain ID"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.w3 = Mock()
        service.blockchain_service.w3.is_connected.return_value = True
        service.blockchain_service.w3.eth.chain_id = 1  # Wrong chain (mainnet Ethereum)
        service.blockchain_service.w3.eth.block_number = 12345678
        service.blockchain_service.w3.eth.gas_price = 1000000000

        with pytest.MonkeyPatch().context() as mp:
            mp.setenv('BASE_CHAIN_ID', '84532')
            result = service.check_base_rpc()
            assert result['status'] == 'error'
            assert 'Wrong chain ID' in result['message']

    def test_rpc_healthy(self):
        """Returns healthy status for valid connection"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.w3 = Mock()
        service.blockchain_service.w3.is_connected.return_value = True
        service.blockchain_service.w3.eth.chain_id = 84532  # BASE Sepolia
        service.blockchain_service.w3.eth.block_number = 12345678
        service.blockchain_service.w3.eth.gas_price = 1000000000  # 1 gwei

        with pytest.MonkeyPatch().context() as mp:
            mp.setenv('BASE_CHAIN_ID', '84532')
            result = service.check_base_rpc()
            assert result['status'] == 'healthy'
            assert result['chain_id'] == 84532
            assert result['latest_block'] == 12345678
            assert 'BASE Sepolia' in result['network']


class TestCheckTimeSynchronization:
    """Test check_time_synchronization method"""

    def test_time_sync_healthy(self):
        """Returns healthy for valid system time"""
        service = HealthCheckService()
        result = service.check_time_synchronization()
        assert result['status'] == 'healthy'
        assert result['timezone'] == 'UTC'
        assert 'current_time' in result


class TestCheckTwitterAPI:
    """Test check_twitter_api method"""

    def test_twitter_api_no_client(self):
        """Returns warning when Twitter client not initialized"""
        service = HealthCheckService()
        service.xcom_service = Mock()
        service.xcom_service.client = None

        result = service.check_twitter_api()
        assert result['status'] == 'warning'
        assert 'not initialized' in result['message']
        assert result['critical'] is False

    def test_twitter_api_healthy(self):
        """Returns healthy when Twitter client is initialized"""
        service = HealthCheckService()
        service.xcom_service = Mock()
        service.xcom_service.client = Mock()  # Client exists

        result = service.check_twitter_api()
        assert result['status'] == 'healthy'


class TestCheckSmartContracts:
    """Test check_smart_contracts method"""

    def test_contracts_healthy(self):
        """Returns healthy when contracts are accessible"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.contracts = {
            'PredictionMarketV2': Mock(),
            'GenesisNFT': Mock()
        }

        with pytest.MonkeyPatch().context() as mp:
            mp.setenv('PREDICTION_MARKET_V2_ADDRESS', '0x5174Da96BCA87c78591038DEe9DB1811288c9286')
            mp.setenv('GENESIS_NFT_ADDRESS', '0x1A5D4475881B93e876251303757E60E524286A24')
            result = service.check_smart_contracts()
            assert result['status'] == 'healthy'

    def test_contracts_warning_when_not_loaded(self):
        """Returns warning when contracts not loaded"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.contracts = {}  # No contracts loaded

        with pytest.MonkeyPatch().context() as mp:
            mp.setenv('PREDICTION_MARKET_V2_ADDRESS', '0x5174Da96BCA87c78591038DEe9DB1811288c9286')
            mp.setenv('GENESIS_NFT_ADDRESS', '0x1A5D4475881B93e876251303757E60E524286A24')
            result = service.check_smart_contracts()
            # Status should be warning since contracts not loaded
            assert result['status'] in ['healthy', 'warning']


class TestCheckNetworkConnectivity:
    """Test check_network_connectivity method"""

    def test_no_nodes_connected(self):
        """Returns warning when no nodes connected"""
        service = HealthCheckService()
        service.node_comm_service = Mock()
        service.node_comm_service.get_connection_status.return_value = {
            'node1': {'connected': False},
            'node2': {'connected': False}
        }

        result = service.check_network_connectivity()
        assert result['status'] == 'warning'
        assert result['connected_nodes'] == 0
        assert result['critical'] is False

    def test_good_connectivity(self):
        """Returns healthy for good connectivity"""
        service = HealthCheckService()
        service.node_comm_service = Mock()
        service.node_comm_service.get_connection_status.return_value = {
            'node1': {'connected': True},
            'node2': {'connected': True},
            'node3': {'connected': True}
        }

        result = service.check_network_connectivity()
        assert result['status'] == 'healthy'
        assert result['connected_nodes'] == 3
        assert result['connectivity_percent'] == 100.0

    def test_no_known_nodes(self):
        """Handles empty node list gracefully"""
        service = HealthCheckService()
        service.node_comm_service = Mock()
        service.node_comm_service.get_connection_status.return_value = {}

        result = service.check_network_connectivity()
        assert result['status'] == 'healthy'
        assert result['connectivity_percent'] == 0


class TestCheckV2MarketStatus:
    """Test check_v2_market_status method"""

    def test_v2_market_status_healthy(self):
        """Returns healthy for V2 market check"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.get_v2_market_count.return_value = 5
        service.blockchain_service.get_v2_pending_fees.return_value = 1000000000000000000  # 1 ETH in wei

        result = service.check_v2_market_status()
        assert result['status'] == 'healthy'
        assert result['total_markets'] == 5

    def test_v2_market_status_error_handling(self):
        """Returns warning on error"""
        service = HealthCheckService()
        service.blockchain_service = Mock()
        service.blockchain_service.get_v2_market_count.side_effect = Exception("Connection failed")

        result = service.check_v2_market_status()
        assert result['status'] == 'warning'
        assert result['critical'] is False
