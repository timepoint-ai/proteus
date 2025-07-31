"""
Production Monitoring Service for Clockchain
Implements Phase 6 monitoring requirements from CRYPTO_PLAN.md
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import threading
import time
import os

from web3 import Web3
from web3.eth import Contract
from sqlalchemy import func

from app import db
from models import (
    Transaction, PredictionMarket, OracleSubmission,
    NetworkMetrics, OracleVote, Submission, Bet
)
from services.blockchain_base import BaseBlockchainService
from services.xcom_api_service import XComAPIService
from config import Config

logger = logging.getLogger(__name__)


class MonitoringService:
    """Comprehensive monitoring service for production readiness"""
    
    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.xcom_service = XComAPIService()
        self.monitoring_active = False
        self.monitoring_thread = None
        self.alerts = []
        self.metrics = {
            'gas_price': {'current': 0, 'threshold': 0.002, 'alert_sent': False},
            'oracle_consensus': {'failures': 0, 'total': 0, 'alert_sent': False},
            'xcom_api': {'rate_limit_remaining': 100, 'reset_time': None, 'alert_sent': False},
            'screenshot_storage': {'used_mb': 0, 'total_screenshots': 0, 'alert_sent': False},
            'contract_events': {'last_check': None, 'events_processed': 0, 'gas_spikes': 0, 'consensus_failures': 0}
        }
        self.app = None
        
        # Initialize contract monitoring (single-node setup)
        try:
            from services.contract_monitoring import ContractMonitoringService
            self.contract_monitor = ContractMonitoringService()
            logger.info("Contract monitoring service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize contract monitoring: {e}")
            self.contract_monitor = None
        
    def start_monitoring(self, app=None):
        """Start the monitoring service"""
        if self.monitoring_active:
            logger.warning("Monitoring service already active")
            return
        
        if app:
            self.app = app
            
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Production monitoring service started")
        
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Production monitoring service stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Run monitoring checks that don't need app context
                self._monitor_gas_prices()
                self._monitor_xcom_api_limits()
                self._monitor_contract_events()
                
                # Run monitoring checks that need app context
                if self.app:
                    with self.app.app_context():
                        self._monitor_oracle_consensus()
                        self._monitor_screenshot_storage()
                        self._save_metrics()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _monitor_gas_prices(self):
        """Monitor BASE gas prices and alert if above threshold"""
        try:
            # Get current gas price from BASE
            current_gas_price = self.blockchain_service.w3.eth.gas_price
            gas_price_gwei = Web3.from_wei(current_gas_price, 'gwei')
            
            self.metrics['gas_price']['current'] = float(gas_price_gwei)
            
            # Check if above threshold
            if gas_price_gwei > self.metrics['gas_price']['threshold']:
                if not self.metrics['gas_price']['alert_sent']:
                    self._create_alert(
                        'HIGH_GAS_PRICE',
                        f'Gas price {gas_price_gwei} gwei exceeds threshold {self.metrics["gas_price"]["threshold"]} gwei',
                        'warning'
                    )
                    self.metrics['gas_price']['alert_sent'] = True
            else:
                self.metrics['gas_price']['alert_sent'] = False
                
            logger.debug(f"Current gas price: {gas_price_gwei} gwei")
            
        except Exception as e:
            logger.error(f"Error monitoring gas prices: {e}")
    
    def _monitor_oracle_consensus(self):
        """Monitor oracle consensus failures (< 66% agreement)"""
        try:
            # Get recent oracle submissions
            recent_cutoff = datetime.utcnow() - timedelta(hours=1)
            recent_submissions = OracleSubmission.query.filter(
                OracleSubmission.created_at > recent_cutoff
            ).all()
            
            if not recent_submissions:
                return
                
            # Check consensus for each submission
            failures = 0
            total = 0
            
            for submission in recent_submissions:
                total += 1
                
                # Get votes for this submission
                votes = OracleVote.query.filter_by(
                    oracle_submission_id=submission.id
                ).all()
                
                if votes:
                    approve_votes = sum(1 for v in votes if v.vote_type == 'approve')
                    consensus_percentage = (approve_votes / len(votes)) * 100
                    
                    if consensus_percentage < 66:
                        failures += 1
                        
            self.metrics['oracle_consensus']['failures'] = failures
            self.metrics['oracle_consensus']['total'] = total
            
            # Alert if failure rate is high
            if total > 0:
                failure_rate = (failures / total) * 100
                if failure_rate > 20:  # More than 20% failing consensus
                    if not self.metrics['oracle_consensus']['alert_sent']:
                        self._create_alert(
                            'ORACLE_CONSENSUS_FAILURE',
                            f'Oracle consensus failure rate {failure_rate:.1f}% (>{failures} of {total} submissions)',
                            'critical'
                        )
                        self.metrics['oracle_consensus']['alert_sent'] = True
                else:
                    self.metrics['oracle_consensus']['alert_sent'] = False
                    
        except Exception as e:
            logger.error(f"Error monitoring oracle consensus: {e}")
    
    def _monitor_contract_events(self):
        """Monitor on-chain contract events"""
        try:
            if not self.contract_monitor:
                return
                
            # Run contract monitoring cycle
            results = self.contract_monitor.run_monitoring_cycle()
            
            # Update metrics
            if 'events' in results:
                events_data = results['events']
                self.metrics['contract_events']['events_processed'] = events_data.get('events_processed', 0)
                self.metrics['contract_events']['gas_spikes'] = len(events_data.get('gas_spike_alerts', []))
                self.metrics['contract_events']['consensus_failures'] = len(events_data.get('consensus_failures', []))
                
                # Process gas spike alerts
                for alert in events_data.get('gas_spike_alerts', []):
                    self._create_alert(
                        'CONTRACT_GAS_SPIKE',
                        f'Contract gas spike detected: {alert["gas_price_gwei"]} gwei',
                        alert['severity']
                    )
                    
                # Process consensus failures
                for failure in events_data.get('consensus_failures', []):
                    self._create_alert(
                        'CONTRACT_CONSENSUS_FAILURE',
                        f'Oracle consensus failure for market {failure["market_id"]}: {failure["consensus_percentage"]}%',
                        'critical'
                    )
                    
            self.metrics['contract_events']['last_check'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error monitoring contract events: {e}")
    
    def _monitor_xcom_api_limits(self):
        """Monitor X.com API rate limits"""
        try:
            # For now, we'll track API usage through the X.com service
            # In production, this would query the actual rate limit status
            # from the Twitter API v2 rate_limit_status endpoint
            
            # Default values for monitoring
            remaining = self.metrics['xcom_api'].get('rate_limit_remaining', 100)
            reset_time = self.metrics['xcom_api'].get('reset_time')
            
            # TODO: When X.com API is fully configured, implement:
            # if self.xcom_service.client and hasattr(self.xcom_service.client, 'rate_limit_status'):
            #     rate_limit_info = self.xcom_service.client.rate_limit_status()
            #     remaining = rate_limit_info.get('remaining', 100)
            #     reset_time = rate_limit_info.get('reset_time')
            
            self.metrics['xcom_api']['rate_limit_remaining'] = remaining
            self.metrics['xcom_api']['reset_time'] = reset_time
            
            # Alert if rate limit is low
            if remaining < 10:
                if not self.metrics['xcom_api']['alert_sent']:
                    self._create_alert(
                        'XCOM_API_RATE_LIMIT',
                        f'X.com API rate limit low: {remaining} requests remaining',
                        'warning'
                    )
                    self.metrics['xcom_api']['alert_sent'] = True
            else:
                self.metrics['xcom_api']['alert_sent'] = False
                
        except Exception as e:
            logger.error(f"Error monitoring X.com API limits: {e}")
    
    def _monitor_screenshot_storage(self):
        """Monitor screenshot storage usage"""
        try:
            # Calculate total screenshot storage
            # Query all submissions that have screenshots
            all_submissions = OracleSubmission.query.all()
            
            total_size = 0
            screenshot_count = 0
            
            for submission in all_submissions:
                if submission.screenshot_proof:
                    # Calculate size of base64 string
                    total_size += len(submission.screenshot_proof)
                    screenshot_count += 1
            
            # Convert to MB (base64 is ~1.33x larger than binary)
            storage_mb = (total_size / 1024 / 1024) / 1.33
            
            self.metrics['screenshot_storage']['used_mb'] = float(storage_mb)
            self.metrics['screenshot_storage']['total_screenshots'] = screenshot_count
            
            # Alert if storage is high (> 1GB)
            if storage_mb > 1024:
                if not self.metrics['screenshot_storage']['alert_sent']:
                    self._create_alert(
                        'HIGH_SCREENSHOT_STORAGE',
                        f'Screenshot storage exceeds 1GB: {storage_mb:.1f}MB used',
                        'warning'
                    )
                    self.metrics['screenshot_storage']['alert_sent'] = True
            else:
                self.metrics['screenshot_storage']['alert_sent'] = False
                
        except Exception as e:
            logger.error(f"Error monitoring screenshot storage: {e}")
    
    def _monitor_contract_events(self):
        """Monitor smart contract events using Web3 filters"""
        try:
            # Get latest block
            latest_block = self.blockchain_service.w3.eth.block_number
            
            # Check each contract for events
            contracts_to_monitor = [
                ('PredictionMarket', os.getenv('PREDICTION_MARKET_ADDRESS')),
                ('ClockchainOracle', os.getenv('ORACLE_CONTRACT_ADDRESS')),
                ('NodeRegistry', os.getenv('NODE_REGISTRY_ADDRESS')),
                ('PayoutManager', os.getenv('PAYOUT_MANAGER_ADDRESS'))
            ]
            
            for contract_name, address in contracts_to_monitor:
                if not address:
                    continue
                    
                try:
                    # Get contract instance
                    contract = self.blockchain_service.get_contract(contract_name)
                    if not contract:
                        continue
                    
                    # Get events from last 100 blocks
                    from_block = max(0, latest_block - 100)
                    
                    # Monitor key events
                    if contract_name == 'PredictionMarket':
                        # MarketCreated events
                        events = contract.events.MarketCreated.get_logs(
                            fromBlock=from_block,
                            toBlock=latest_block
                        )
                        for event in events:
                            self._process_market_created_event(event)
                            
                    elif contract_name == 'ClockchainOracle':
                        # OracleSubmitted events
                        events = contract.events.OracleDataSubmitted.get_logs(
                            fromBlock=from_block,
                            toBlock=latest_block
                        )
                        for event in events:
                            self._process_oracle_submitted_event(event)
                            
                except Exception as e:
                    logger.error(f"Error monitoring {contract_name} events: {e}")
                    
            self.metrics['contract_events']['last_check'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error monitoring contract events: {e}")
    
    def _process_market_created_event(self, event):
        """Process MarketCreated event"""
        try:
            market_id = event.args.get('marketId')
            creator = event.args.get('creator')
            logger.info(f"MarketCreated event: ID={market_id}, creator={creator}")
            self.metrics['contract_events']['events_processed'] += 1
        except Exception as e:
            logger.error(f"Error processing MarketCreated event: {e}")
    
    def _process_oracle_submitted_event(self, event):
        """Process OracleSubmitted event"""
        try:
            market_id = event.args.get('marketId')
            oracle = event.args.get('oracle')
            logger.info(f"OracleSubmitted event: marketId={market_id}, oracle={oracle}")
            self.metrics['contract_events']['events_processed'] += 1
        except Exception as e:
            logger.error(f"Error processing OracleSubmitted event: {e}")
    
    def _create_alert(self, alert_type: str, message: str, severity: str = 'info'):
        """Create an alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.utcnow(),
            'acknowledged': False
        }
        self.alerts.append(alert)
        
        # Log based on severity
        if severity == 'critical':
            logger.critical(f"ALERT: {message}")
        elif severity == 'warning':
            logger.warning(f"ALERT: {message}")
        else:
            logger.info(f"ALERT: {message}")
    
    def _save_metrics(self):
        """Save current metrics to database"""
        try:
            # Create network metrics entry
            metrics = NetworkMetrics()
            metrics.timestamp = datetime.utcnow()
            metrics.active_nodes = 0  # Will be updated by consensus service
            metrics.consensus_accuracy = self._calculate_health_score()
            
            # Update with monitoring data
            metrics.total_markets = PredictionMarket.query.count()
            metrics.total_submissions = Submission.query.count()
            metrics.total_bets = Bet.query.count()
            
            # Note: Additional monitoring data could be stored in a separate monitoring table
            # For now, we're using the existing NetworkMetrics fields
            
            db.session.add(metrics)
            db.session.commit()
            
            # Log monitoring metrics separately
            logger.info(f"Monitoring metrics saved: "
                       f"gas_price={self.metrics['gas_price']['current']} gwei, "
                       f"oracle_failures={self.metrics['oracle_consensus']['failures']}, "
                       f"xcom_rate_limit={self.metrics['xcom_api']['rate_limit_remaining']}, "
                       f"screenshot_storage={self.metrics['screenshot_storage']['used_mb']:.1f}MB")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            db.session.rollback()
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score (0-1)"""
        score = 1.0
        
        # Deduct for high gas prices
        if self.metrics['gas_price']['current'] > self.metrics['gas_price']['threshold']:
            score -= 0.2
            
        # Deduct for oracle consensus failures
        if self.metrics['oracle_consensus']['total'] > 0:
            failure_rate = self.metrics['oracle_consensus']['failures'] / self.metrics['oracle_consensus']['total']
            score -= (failure_rate * 0.3)
            
        # Deduct for low API rate limit
        if self.metrics['xcom_api']['rate_limit_remaining'] < 10:
            score -= 0.2
            
        # Deduct for high storage usage
        if self.metrics['screenshot_storage']['used_mb'] > 1024:
            score -= 0.1
            
        return max(0.0, min(1.0, score))
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status and metrics"""
        return {
            'active': self.monitoring_active,
            'metrics': self.metrics,
            'alerts': [
                {
                    'type': alert['type'],
                    'message': alert['message'],
                    'severity': alert['severity'],
                    'timestamp': alert['timestamp'].isoformat(),
                    'acknowledged': alert['acknowledged']
                }
                for alert in self.alerts[-10:]  # Last 10 alerts
            ],
            'health_score': self._calculate_health_score(),
            'last_update': datetime.utcnow().isoformat()
        }
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current monitoring metrics (alias for dashboard compatibility)"""
        return self.metrics
    
    def acknowledge_alert(self, alert_type: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert['type'] == alert_type and not alert['acknowledged']:
                alert['acknowledged'] = True
                return True
        return False


# Global monitoring service instance
monitoring_service = MonitoringService()