"""Contract event monitoring service for BASE blockchain"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from web3 import Web3
from web3.exceptions import BlockNotFound
from models import db, ContractEvent, NetworkMetrics
from services.blockchain_base import BaseBlockchainService
import time

logger = logging.getLogger(__name__)


class ContractMonitoringService:
    """Monitors on-chain events from deployed smart contracts"""
    
    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.w3 = self.blockchain_service.w3
        self.last_processed_block = None
        self.event_filters = {}
        self._init_contract_filters()
        
    def _init_contract_filters(self):
        """Initialize event filters for all deployed contracts"""
        try:
            # PredictionMarket events
            market_contract = self.blockchain_service.get_contract('PredictionMarket')
            if market_contract:
                self.event_filters['MarketCreated'] = market_contract.events.MarketCreated.create_filter(fromBlock='latest')
                self.event_filters['BetPlaced'] = market_contract.events.BetPlaced.create_filter(fromBlock='latest')
                self.event_filters['MarketResolved'] = market_contract.events.MarketResolved.create_filter(fromBlock='latest')
                logger.info("PredictionMarket event filters initialized")
            
            # ClockchainOracle events
            oracle_contract = self.blockchain_service.get_contract('ClockchainOracle')
            if oracle_contract:
                self.event_filters['OracleDataSubmitted'] = oracle_contract.events.OracleDataSubmitted.create_filter(fromBlock='latest')
                self.event_filters['ConsensusReached'] = oracle_contract.events.ConsensusReached.create_filter(fromBlock='latest')
                logger.info("ClockchainOracle event filters initialized")
                
            # NodeRegistry events
            node_contract = self.blockchain_service.get_contract('NodeRegistry')
            if node_contract:
                self.event_filters['NodeRegistered'] = node_contract.events.NodeRegistered.create_filter(fromBlock='latest')
                self.event_filters['NodeStaked'] = node_contract.events.NodeStaked.create_filter(fromBlock='latest')
                self.event_filters['NodeSlashed'] = node_contract.events.NodeSlashed.create_filter(fromBlock='latest')
                logger.info("NodeRegistry event filters initialized")
                
            # PayoutManager events
            payout_contract = self.blockchain_service.get_contract('PayoutManager')
            if payout_contract:
                self.event_filters['PayoutDistributed'] = payout_contract.events.PayoutDistributed.create_filter(fromBlock='latest')
                logger.info("PayoutManager event filters initialized")
                
        except Exception as e:
            logger.error(f"Error initializing contract filters: {e}")
            
    def process_events(self) -> Dict[str, Any]:
        """Process new events from all contracts"""
        results = {
            'events_processed': 0,
            'errors': [],
            'gas_spike_alerts': [],
            'consensus_failures': []
        }
        
        try:
            # Get current block
            current_block = self.w3.eth.block_number
            
            # Process events from each filter
            for event_name, event_filter in self.event_filters.items():
                try:
                    new_events = event_filter.get_new_entries()
                    for event in new_events:
                        self._process_single_event(event_name, event, results)
                        results['events_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing {event_name} events: {e}")
                    results['errors'].append(f"{event_name}: {str(e)}")
                    
            # Check for gas price spikes
            self._check_gas_price_alerts(results)
            
            # Check for consensus failures
            self._check_consensus_failures(results)
            
            # Update last processed block
            self.last_processed_block = current_block
            
        except Exception as e:
            logger.error(f"Error in event processing: {e}")
            results['errors'].append(str(e))
            
        return results
        
    def _process_single_event(self, event_name: str, event: Dict, results: Dict):
        """Process a single contract event"""
        try:
            # Extract common event data
            event_data = {
                'event_name': event_name,
                'transaction_hash': event['transactionHash'].hex() if 'transactionHash' in event else None,
                'block_number': event['blockNumber'],
                'address': event['address'],
                'args': dict(event['args']) if 'args' in event else {},
                'timestamp': datetime.utcnow()
            }
            
            # Store event in database
            contract_event = ContractEvent()
            contract_event.event_type = event_name
            contract_event.contract_address = event_data['address']
            contract_event.transaction_hash = event_data['transaction_hash']
            contract_event.block_number = event_data['block_number']
            contract_event.event_data = event_data['args']
            contract_event.timestamp = event_data['timestamp']
            db.session.add(contract_event)
            
            # Special handling for specific events
            if event_name == 'MarketCreated':
                self._handle_market_created(event_data)
            elif event_name == 'ConsensusReached':
                self._handle_consensus_reached(event_data)
            elif event_name == 'NodeSlashed':
                self._handle_node_slashed(event_data)
                
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing event {event_name}: {e}")
            db.session.rollback()
            
    def _handle_market_created(self, event_data: Dict):
        """Handle MarketCreated event"""
        logger.info(f"New market created: {event_data['args'].get('marketId')}")
        
    def _handle_consensus_reached(self, event_data: Dict):
        """Handle ConsensusReached event"""
        consensus_percentage = event_data['args'].get('consensusPercentage', 0)
        if consensus_percentage < 66:
            logger.warning(f"Low consensus reached: {consensus_percentage}%")
            
    def _handle_node_slashed(self, event_data: Dict):
        """Handle NodeSlashed event"""
        node_address = event_data['args'].get('nodeAddress')
        slash_amount = event_data['args'].get('amount', 0)
        logger.warning(f"Node slashed: {node_address} for {slash_amount} BASE")
        
    def _check_gas_price_alerts(self, results: Dict):
        """Check for gas price spikes"""
        try:
            current_gas_price = self.w3.eth.gas_price
            gas_price_gwei = Web3.from_wei(current_gas_price, 'gwei')
            
            # Alert if gas price exceeds 50 gwei
            if gas_price_gwei > 50:
                alert = {
                    'type': 'gas_spike',
                    'severity': 'high' if gas_price_gwei > 100 else 'medium',
                    'gas_price_gwei': float(gas_price_gwei),
                    'timestamp': datetime.utcnow().isoformat()
                }
                results['gas_spike_alerts'].append(alert)
                logger.warning(f"Gas price spike detected: {gas_price_gwei} gwei")
                
        except Exception as e:
            logger.error(f"Error checking gas prices: {e}")
            
    def _check_consensus_failures(self, results: Dict):
        """Check for oracle consensus failures"""
        try:
            # Query recent oracle submissions with low consensus
            recent_time = datetime.utcnow() - timedelta(hours=1)
            from models import OracleSubmission
            
            recent_submissions = OracleSubmission.query.filter(
                OracleSubmission.created_at >= recent_time,
                OracleSubmission.consensus_percentage < 66
            ).all()
            
            for submission in recent_submissions:
                failure = {
                    'market_id': str(submission.market_id),
                    'consensus_percentage': submission.consensus_percentage,
                    'timestamp': submission.created_at.isoformat()
                }
                results['consensus_failures'].append(failure)
                
            if recent_submissions:
                logger.warning(f"Found {len(recent_submissions)} consensus failures in the last hour")
                
        except Exception as e:
            logger.error(f"Error checking consensus failures: {e}")
            
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about contract events"""
        try:
            # Get event counts by type
            event_counts = db.session.query(
                ContractEvent.event_type,
                db.func.count(ContractEvent.id)
            ).group_by(ContractEvent.event_type).all()
            
            # Get recent events
            recent_time = datetime.utcnow() - timedelta(hours=24)
            recent_events = ContractEvent.query.filter(
                ContractEvent.timestamp >= recent_time
            ).order_by(ContractEvent.timestamp.desc()).limit(10).all()
            
            return {
                'event_counts': dict(event_counts),
                'recent_events': [
                    {
                        'type': event.event_type,
                        'tx_hash': event.transaction_hash[:10] + '...' if event.transaction_hash else None,
                        'block': event.block_number,
                        'timestamp': event.timestamp.isoformat()
                    }
                    for event in recent_events
                ],
                'last_processed_block': self.last_processed_block
            }
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}
            
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle"""
        logger.debug("Running contract monitoring cycle")
        
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'events': self.process_events(),
            'statistics': self.get_event_statistics()
        }
        
        # Log any alerts
        if results['events']['gas_spike_alerts']:
            logger.warning(f"Gas spike alerts: {results['events']['gas_spike_alerts']}")
            
        if results['events']['consensus_failures']:
            logger.warning(f"Consensus failures: {results['events']['consensus_failures']}")
            
        return results