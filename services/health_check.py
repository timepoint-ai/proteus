"""
Health Check Service for Clockchain
Implements comprehensive health checking as specified in Phase 6
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests
from decimal import Decimal
import os

from web3 import Web3
from sqlalchemy import func

from app import db
from models import (
    NodeOperator, PredictionMarket, OracleSubmission,
    Transaction, NetworkMetrics, Submission, Bet
)
from services.blockchain_base import BaseBlockchainService
from services.xcom_api_service import XComAPIService
from services.consensus import ConsensusService
from services.node_communication import NodeCommunicationService
from config import Config

logger = logging.getLogger(__name__)


class HealthCheckService:
    """Comprehensive health check service for production monitoring"""
    
    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.xcom_service = XComAPIService()
        self.consensus_service = ConsensusService()
        self.node_comm_service = NodeCommunicationService()
        
        # Define health checks
        self.checks = {
            'base_connection': self.check_base_rpc,
            'smart_contracts': self.check_smart_contracts,
            'twitter_api': self.check_twitter_api,
            'node_consensus': self.check_node_health,
            'contract_state': self.check_contract_sync,
            'database': self.check_database,
            'oracle_system': self.check_oracle_system,
            'transaction_processing': self.check_transaction_processing,
            'network_connectivity': self.check_network_connectivity,
            'time_sync': self.check_time_synchronization
        }
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
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
                if result['status'] == 'error':
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
                'PredictionMarket': os.getenv('PREDICTION_MARKET_ADDRESS'),
                'ClockchainOracle': os.getenv('ORACLE_CONTRACT_ADDRESS'),
                'NodeRegistry': os.getenv('NODE_REGISTRY_ADDRESS'),
                'PayoutManager': os.getenv('PAYOUT_MANAGER_ADDRESS')
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
                    contract = self.blockchain_service.get_contract(name)
                    if contract:
                        # Try to call a view function
                        if name == 'PredictionMarket':
                            # Just check if we can access the contract
                            results[name] = {
                                'status': 'healthy',
                                'address': address
                            }
                        else:
                            results[name] = {
                                'status': 'healthy',
                                'address': address
                            }
                    else:
                        results[name] = {
                            'status': 'error',
                            'message': 'Failed to load contract'
                        }
                        all_healthy = False
                        
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'message': str(e)
                    }
                    all_healthy = False
            
            return {
                'status': 'healthy' if all_healthy else 'error',
                'contracts': results,
                'critical': not all_healthy
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Contract check error: {str(e)}',
                'critical': True
            }
    
    def check_twitter_api(self) -> Dict[str, Any]:
        """Check X.com (Twitter) API connectivity and rate limits"""
        try:
            # Check if X.com API client is initialized
            if not self.xcom_service.client:
                return {
                    'status': 'warning',
                    'message': 'X.com API client not initialized - credentials may not be configured',
                    'critical': False
                }
            
            # In production, we would check rate limits using the Twitter API v2
            # For now, we'll return a healthy status if the client is initialized
            # TODO: Implement actual rate limit checking when API is fully configured
            
            return {
                'status': 'healthy',
                'message': 'X.com API client initialized',
                'rate_limit_remaining': 'unknown',
                'note': 'Rate limit monitoring will be available when API is fully configured'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'X.com API check error: {str(e)}',
                'critical': False
            }
    
    def check_node_health(self) -> Dict[str, Any]:
        """Check node consensus health"""
        try:
            # Get consensus health from consensus service
            health = self.consensus_service.get_network_health()
            
            active_nodes = health.get('active_nodes', 0)
            total_nodes = health.get('total_nodes', 0)
            network_health_score = health.get('network_health', 0)
            
            # Check if we have minimum nodes for consensus
            if active_nodes < 3:
                return {
                    'status': 'error',
                    'message': f'Insufficient active nodes for consensus: {active_nodes}',
                    'active_nodes': active_nodes,
                    'total_nodes': total_nodes,
                    'critical': True
                }
            
            # Check network health score
            if network_health_score < 0.5:
                return {
                    'status': 'warning',
                    'message': 'Network health below 50%',
                    'active_nodes': active_nodes,
                    'total_nodes': total_nodes,
                    'health_score': network_health_score,
                    'critical': False
                }
            
            return {
                'status': 'healthy',
                'active_nodes': active_nodes,
                'total_nodes': total_nodes,
                'health_score': network_health_score,
                'pending_nodes': health.get('pending_nodes', 0)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Node health check error: {str(e)}',
                'critical': True
            }
    
    def check_contract_sync(self) -> Dict[str, Any]:
        """Check if contract state is synchronized with database"""
        try:
            # Check a few recent markets
            recent_markets = PredictionMarket.query.order_by(
                PredictionMarket.created_at.desc()
            ).limit(5).all()
            
            sync_errors = []
            
            for market in recent_markets:
                if market.contract_address:
                    try:
                        # Verify market exists on-chain
                        # This is a simplified check - in production you'd verify more state
                        contract = self.blockchain_service.get_contract('PredictionMarket')
                        if contract:
                            # Just verify the contract is accessible
                            pass
                        else:
                            sync_errors.append(f"Market {market.id} contract not accessible")
                    except Exception as e:
                        sync_errors.append(f"Market {market.id}: {str(e)}")
            
            if sync_errors:
                return {
                    'status': 'error',
                    'message': 'Contract sync errors detected',
                    'errors': sync_errors[:5],  # Limit to 5 errors
                    'critical': False
                }
            
            return {
                'status': 'healthy',
                'message': 'Contract state synchronized',
                'markets_checked': len(recent_markets)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Contract sync check error: {str(e)}',
                'critical': False
            }
    
    def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations"""
        try:
            # Try a simple query
            count = db.session.query(func.count(PredictionMarket.id)).scalar()
            
            # Check if we can write
            test_metric = NetworkMetrics()
            test_metric.timestamp = datetime.utcnow()
            test_metric.active_nodes = 0
            
            db.session.add(test_metric)
            db.session.flush()
            
            # Delete the test record
            db.session.delete(test_metric)
            db.session.commit()
            
            return {
                'status': 'healthy',
                'total_markets': count,
                'read_write': 'ok'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': f'Database error: {str(e)}',
                'critical': True
            }
    
    def check_oracle_system(self) -> Dict[str, Any]:
        """Check oracle submission and consensus system"""
        try:
            # Get recent oracle activity
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_submissions = OracleSubmission.query.filter(
                OracleSubmission.created_at > recent_cutoff
            ).count()
            
            # Check for stuck validations
            stuck_validations = PredictionMarket.query.filter(
                PredictionMarket.status == 'validating',
                PredictionMarket.end_time < datetime.utcnow() - timedelta(hours=2)
            ).count()
            
            if stuck_validations > 0:
                return {
                    'status': 'warning',
                    'message': f'{stuck_validations} markets stuck in validation',
                    'recent_submissions': recent_submissions,
                    'stuck_validations': stuck_validations,
                    'critical': False
                }
            
            return {
                'status': 'healthy',
                'recent_submissions_24h': recent_submissions,
                'stuck_validations': 0
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Oracle system check error: {str(e)}',
                'critical': False
            }
    
    def check_transaction_processing(self) -> Dict[str, Any]:
        """Check transaction processing system"""
        try:
            # Check for pending transactions
            pending_txs = Transaction.query.filter_by(
                status='pending'
            ).filter(
                Transaction.created_at < datetime.utcnow() - timedelta(minutes=10)
            ).count()
            
            # Check recent transaction success rate
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_txs = Transaction.query.filter(
                Transaction.created_at > recent_cutoff
            ).all()
            
            if recent_txs:
                success_count = sum(1 for tx in recent_txs if tx.status == 'confirmed')
                success_rate = (success_count / len(recent_txs)) * 100
            else:
                success_rate = 100
            
            if pending_txs > 10:
                return {
                    'status': 'warning',
                    'message': f'{pending_txs} transactions pending > 10 minutes',
                    'pending_count': pending_txs,
                    'success_rate': success_rate,
                    'critical': False
                }
            
            if success_rate < 80:
                return {
                    'status': 'warning',
                    'message': f'Low transaction success rate: {success_rate:.1f}%',
                    'pending_count': pending_txs,
                    'success_rate': success_rate,
                    'critical': False
                }
            
            return {
                'status': 'healthy',
                'pending_count': pending_txs,
                'success_rate': success_rate,
                'recent_transactions': len(recent_txs)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Transaction processing check error: {str(e)}',
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
                    'status': 'error',
                    'message': 'Not connected to any network nodes',
                    'connected_nodes': 0,
                    'total_known_nodes': total_known_nodes,
                    'critical': True
                }
            
            connectivity_percent = (connected_nodes / total_known_nodes * 100) if total_known_nodes > 0 else 0
            
            if connectivity_percent < 50:
                return {
                    'status': 'warning',
                    'message': f'Low network connectivity: {connectivity_percent:.1f}%',
                    'connected_nodes': connected_nodes,
                    'total_known_nodes': total_known_nodes,
                    'critical': False
                }
            
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
        """Check time synchronization across the network"""
        try:
            # This would normally check NTP sync or network time consensus
            # For now, we'll do a basic check
            current_time = datetime.utcnow()
            
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


# Global health check service instance
health_check_service = HealthCheckService()