"""
Health Check Service for Proteus
Provides production monitoring for blockchain and API health.

Note: Database-dependent checks were removed in Phase 7 (chain-only mode).
This service now focuses on blockchain connectivity and external API status.
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import os

from web3 import Web3

from services.blockchain_base import BaseBlockchainService
from services.xcom_api_service import XComAPIService
from services.node_communication import NodeCommunicationService

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Health check service for production monitoring.

    Checks blockchain connectivity, smart contract accessibility,
    and external API status. All data comes from on-chain sources.
    """

    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.xcom_service = XComAPIService()
        self.node_comm_service = NodeCommunicationService()

        # Define health checks (chain-only, no database)
        self.checks = {
            'base_connection': self.check_base_rpc,
            'smart_contracts': self.check_smart_contracts,
            'twitter_api': self.check_twitter_api,
            'network_connectivity': self.check_network_connectivity,
            'time_sync': self.check_time_synchronization,
            'v2_market_status': self.check_v2_market_status
        }

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }

        failed_checks = 0
        critical_failures = 0

        for name, check_func in self.checks.items():
            try:
                # Run check (handle both sync and async functions)
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()

                results['checks'][name] = result

                # Track failures
                if result.get('status') == 'error':
                    failed_checks += 1
                    if result.get('critical', False):
                        critical_failures += 1

            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results['checks'][name] = {
                    'status': 'error',
                    'message': str(e),
                    'critical': True
                }
                failed_checks += 1
                critical_failures += 1

        # Determine overall status
        if critical_failures > 0:
            results['overall_status'] = 'critical'
        elif failed_checks > 0:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'healthy'

        results['summary'] = {
            'total_checks': len(self.checks),
            'passed': len(self.checks) - failed_checks,
            'failed': failed_checks,
            'critical': critical_failures
        }

        return results

    def check_base_rpc(self) -> Dict[str, Any]:
        """Check BASE blockchain RPC connection"""
        try:
            # Check if connected
            if not self.blockchain_service.w3.is_connected():
                return {
                    'status': 'error',
                    'message': 'Not connected to BASE RPC',
                    'critical': True
                }

            # Get network info
            chain_id = self.blockchain_service.w3.eth.chain_id
            latest_block = self.blockchain_service.w3.eth.block_number
            gas_price = self.blockchain_service.w3.eth.gas_price
            gas_price_gwei = Web3.from_wei(gas_price, 'gwei')

            # Check if on correct network
            is_testnet = os.getenv('BASE_CHAIN_ID', '84532') == '84532'
            expected_chain_id = 84532 if is_testnet else 8453
            if chain_id != expected_chain_id:
                return {
                    'status': 'error',
                    'message': f'Wrong chain ID: {chain_id}, expected {expected_chain_id}',
                    'critical': True
                }

            return {
                'status': 'healthy',
                'chain_id': chain_id,
                'latest_block': latest_block,
                'gas_price_gwei': float(gas_price_gwei),
                'network': 'BASE Sepolia' if is_testnet else 'BASE Mainnet'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'RPC connection error: {str(e)}',
                'critical': True
            }

    def check_smart_contracts(self) -> Dict[str, Any]:
        """Check all smart contracts are accessible"""
        try:
            contracts = {
                'PredictionMarketV2': os.getenv('PREDICTION_MARKET_V2_ADDRESS', '0x5174Da96BCA87c78591038DEe9DB1811288c9286'),
                'GenesisNFT': os.getenv('GENESIS_NFT_ADDRESS', '0x1A5D4475881B93e876251303757E60E524286A24'),
            }

            results = {}
            all_healthy = True

            for name, address in contracts.items():
                if not address:
                    results[name] = {
                        'status': 'error',
                        'message': 'Contract address not configured'
                    }
                    all_healthy = False
                    continue

                try:
                    # Try to get contract instance
                    contract = self.blockchain_service.contracts.get(name)
                    if contract:
                        results[name] = {
                            'status': 'healthy',
                            'address': address
                        }
                    else:
                        results[name] = {
                            'status': 'warning',
                            'message': 'Contract not loaded',
                            'address': address
                        }

                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'message': str(e)
                    }
                    all_healthy = False

            return {
                'status': 'healthy' if all_healthy else 'warning',
                'contracts': results,
                'critical': False
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Contract check error: {str(e)}',
                'critical': True
            }

    def check_twitter_api(self) -> Dict[str, Any]:
        """Check X.com (Twitter) API connectivity"""
        try:
            # Check if X.com API client is initialized
            if not self.xcom_service.client:
                return {
                    'status': 'warning',
                    'message': 'X.com API client not initialized - credentials may not be configured',
                    'critical': False
                }

            return {
                'status': 'healthy',
                'message': 'X.com API client initialized',
                'note': 'Rate limit monitoring available when API is fully configured'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'X.com API check error: {str(e)}',
                'critical': False
            }

    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to other nodes"""
        try:
            # Get connection status
            connection_status = self.node_comm_service.get_connection_status()
            connected_nodes = 0
            total_known_nodes = len(connection_status)

            # Check each node's connection status
            for node_id, status in connection_status.items():
                if isinstance(status, dict) and status.get('connected'):
                    connected_nodes += 1
                elif isinstance(status, str) and status == 'connected':
                    connected_nodes += 1

            if connected_nodes == 0 and total_known_nodes > 0:
                return {
                    'status': 'warning',
                    'message': 'Not connected to any network nodes',
                    'connected_nodes': 0,
                    'total_known_nodes': total_known_nodes,
                    'critical': False
                }

            connectivity_percent = (connected_nodes / total_known_nodes * 100) if total_known_nodes > 0 else 0

            return {
                'status': 'healthy',
                'connected_nodes': connected_nodes,
                'total_known_nodes': total_known_nodes,
                'connectivity_percent': connectivity_percent
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Network connectivity check error: {str(e)}',
                'critical': False
            }

    def check_time_synchronization(self) -> Dict[str, Any]:
        """Check time synchronization"""
        try:
            current_time = datetime.now(timezone.utc)

            # Check if system time seems reasonable
            if current_time.year < 2024 or current_time.year > 2030:
                return {
                    'status': 'error',
                    'message': 'System time appears incorrect',
                    'current_time': current_time.isoformat(),
                    'critical': True
                }

            return {
                'status': 'healthy',
                'current_time': current_time.isoformat(),
                'timezone': 'UTC'
            }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'Time sync check error: {str(e)}',
                'critical': False
            }

    def check_v2_market_status(self) -> Dict[str, Any]:
        """Check PredictionMarketV2 contract status"""
        try:
            # Get V2 market count from blockchain
            market_count = self.blockchain_service.get_v2_market_count()

            # Get pending fees if available
            owner_address = os.getenv('OWNER_ADDRESS', '0x21a85AD98641827BFd89F4d5bC2fEB72F98aaecA')
            try:
                pending_fees = self.blockchain_service.get_v2_pending_fees(owner_address)
            except Exception:
                pending_fees = 0

            return {
                'status': 'healthy',
                'total_markets': market_count,
                'pending_fees_wei': pending_fees,
                'contract': '0x5174Da96BCA87c78591038DEe9DB1811288c9286'
            }

        except Exception as e:
            return {
                'status': 'warning',
                'message': f'V2 market check error: {str(e)}',
                'critical': False
            }


# Global health check service instance
health_check_service = HealthCheckService()
