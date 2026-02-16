"""Contract event monitoring service for BASE blockchain (Chain-only, no database)"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from web3 import Web3
from web3.exceptions import BlockNotFound
from services.blockchain_base import BaseBlockchainService
import time
from collections import deque

logger = logging.getLogger(__name__)


class ContractMonitoringService:
    """Monitors on-chain events from deployed smart contracts"""
    
    def __init__(self):
        self.blockchain_service = BaseBlockchainService()
        self.w3 = self.blockchain_service.w3
        self.last_processed_block = None
        self.event_filters = {}
        # In-memory cache for recent events (no database)
        self.event_cache = deque(maxlen=1000)  # Keep last 1000 events
        self.metrics_cache = {
            'total_events': 0,
            'events_by_type': {},
            'gas_spike_count': 0,
            'consensus_failure_count': 0
        }
        self._init_contract_filters()
        
    def _init_contract_filters(self):
        """Initialize event filters for all deployed contracts"""
        try:
            # PredictionMarket events
            market_contract = self.blockchain_service.get_contract('PredictionMarket')
            if market_contract:
                # Use build_filter() instead of create_filter() for proper web3.py usage
                self.event_filters['MarketCreated'] = market_contract.events.MarketCreated.build_filter()
                self.event_filters['BetPlaced'] = market_contract.events.BetPlaced.build_filter()
                self.event_filters['MarketResolved'] = market_contract.events.MarketResolved.build_filter()
                logger.info("PredictionMarket event filters initialized")
            
            # ClockchainOracle events (legacy contract name — deployed on-chain as ClockchainOracle)
            oracle_contract = self.blockchain_service.get_contract('ClockchainOracle')
            if oracle_contract:
                self.event_filters['OracleDataSubmitted'] = oracle_contract.events.OracleDataSubmitted.build_filter()
                self.event_filters['ConsensusReached'] = oracle_contract.events.ConsensusReached.build_filter()
                logger.info("ClockchainOracle event filters initialized")
                
            # NodeRegistry events
            node_contract = self.blockchain_service.get_contract('NodeRegistry')
            if node_contract:
                self.event_filters['NodeRegistered'] = node_contract.events.NodeRegistered.build_filter()
                self.event_filters['NodeStaked'] = node_contract.events.NodeStaked.build_filter()
                self.event_filters['NodeSlashed'] = node_contract.events.NodeSlashed.build_filter()
                logger.info("NodeRegistry event filters initialized")
                
            # PayoutManager events
            payout_contract = self.blockchain_service.get_contract('PayoutManager')
            if payout_contract:
                self.event_filters['PayoutDistributed'] = payout_contract.events.PayoutDistributed.build_filter()
                logger.info("PayoutManager event filters initialized")
                
        except Exception as e:
            logger.error(f"Error initializing contract filters: {e}")
            
    def process_events(self) -> Dict[str, Any]:
        """Process new events from all contracts (chain-only, no database)"""
        results = {
            'events_processed': 0,
            'errors': [],
            'gas_spike_alerts': [],
            'consensus_failures': []
        }
        
        try:
            # Get current block
            current_block = self.w3.eth.block_number
            
            # Determine block range to scan
            if self.last_processed_block is None:
                # Start from 100 blocks ago on first run
                from_block = max(0, current_block - 100)
            else:
                from_block = self.last_processed_block + 1
                
            # Don't process if we're already up to date
            if from_block > current_block:
                return results
                
            # Get events using getLogs for each contract
            for event_name in self.event_filters.keys():
                try:
                    events = self._get_events_in_range(event_name, from_block, current_block)
                    for event in events:
                        self._process_single_event(event_name, event, results)
                        results['events_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing {event_name} events: {e}")
                    results['errors'].append(f"{event_name}: {str(e)}")
                    
            # Check for gas price spikes
            self._check_gas_price_alerts(results)
            
            # Check for consensus failures (chain-only)
            self._check_consensus_failures(results)
            
            # Update last processed block
            self.last_processed_block = current_block
            
        except Exception as e:
            logger.error(f"Error in event processing: {e}")
            results['errors'].append(str(e))
            
        return results
        
    def _get_events_in_range(self, event_name: str, from_block: int, to_block: int) -> List[Dict]:
        """Get events in a specific block range"""
        events = []
        try:
            # Get the appropriate contract and event
            contract = None
            event = None
            
            if event_name in ['MarketCreated', 'BetPlaced', 'MarketResolved']:
                contract = self.blockchain_service.get_contract('PredictionMarket')
                if contract:
                    event = getattr(contract.events, event_name, None)
            elif event_name in ['OracleDataSubmitted', 'ConsensusReached']:
                contract = self.blockchain_service.get_contract('ClockchainOracle')  # Legacy contract name
                if contract:
                    event = getattr(contract.events, event_name, None)
            elif event_name in ['NodeRegistered', 'NodeStaked', 'NodeSlashed']:
                contract = self.blockchain_service.get_contract('NodeRegistry')
                if contract:
                    event = getattr(contract.events, event_name, None)
            elif event_name == 'PayoutDistributed':
                contract = self.blockchain_service.get_contract('PayoutManager')
                if contract:
                    event = getattr(contract.events, event_name, None)
                    
            if event:
                # Use get_logs with correct parameter names for web3.py
                event_logs = event.get_logs(from_block=from_block, to_block=to_block)
                events.extend(event_logs)
                
        except Exception as e:
            logger.error(f"Error getting {event_name} events: {e}")
            
        return events
    
    def _process_single_event(self, event_name: str, event: Dict, results: Dict):
        """Process a single contract event (chain-only, no database)"""
        try:
            # Extract common event data
            event_data = {
                'event_name': event_name,
                'transaction_hash': event['transactionHash'].hex() if 'transactionHash' in event else None,
                'block_number': event['blockNumber'],
                'address': event['address'],
                'args': dict(event['args']) if 'args' in event else {},
                'timestamp': datetime.now(timezone.utc)
            }
            
            # Add to in-memory cache instead of database
            self.event_cache.append(event_data)
            
            # Update metrics cache
            self.metrics_cache['total_events'] += 1
            if event_name not in self.metrics_cache['events_by_type']:
                self.metrics_cache['events_by_type'][event_name] = 0
            self.metrics_cache['events_by_type'][event_name] += 1
            
            # Special handling for specific events
            if event_name == 'MarketCreated':
                self._handle_market_created(event_data)
            elif event_name == 'ConsensusReached':
                self._handle_consensus_reached(event_data, results)
            elif event_name == 'NodeSlashed':
                self._handle_node_slashed(event_data)
                
            # Log significant events
            logger.debug(f"Processed {event_name} event at block {event_data['block_number']}")
            
        except Exception as e:
            logger.error(f"Error processing event {event_name}: {e}")
            
    def _handle_market_created(self, event_data: Dict):
        """Handle MarketCreated event"""
        logger.info(f"New market created: {event_data['args'].get('marketId')}")
        
    def _handle_consensus_reached(self, event_data: Dict, results: Dict):
        """Handle ConsensusReached event"""
        consensus_percentage = event_data['args'].get('consensusPercentage', 0)
        if consensus_percentage < 66:
            logger.warning(f"Low consensus reached: {consensus_percentage}%")
            # Add to results for monitoring
            results['consensus_failures'].append({
                'market_id': event_data['args'].get('marketId'),
                'consensus_percentage': consensus_percentage,
                'timestamp': event_data['timestamp'].isoformat()
            })
            self.metrics_cache['consensus_failure_count'] += 1
            
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
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                results['gas_spike_alerts'].append(alert)
                logger.warning(f"Gas price spike detected: {gas_price_gwei} gwei")
                
        except Exception as e:
            logger.error(f"Error checking gas prices: {e}")
            
    def _check_consensus_failures(self, results: Dict):
        """Check for oracle consensus failures (chain-only)"""
        try:
            # Check recent events in cache for consensus failures
            recent_time = datetime.now(timezone.utc) - timedelta(hours=1)
            
            # Look through cached events for recent consensus failures
            recent_failures = []
            for event in self.event_cache:
                if (event.get('event_name') == 'ConsensusReached' and 
                    event.get('timestamp') and event['timestamp'] >= recent_time):
                    consensus_pct = event.get('args', {}).get('consensusPercentage', 100)
                    if consensus_pct < 66:
                        recent_failures.append(event)
                        
            if recent_failures:
                logger.warning(f"Found {len(recent_failures)} consensus failures in recent events")
                
            # Note: Consensus failures are already added to results in _handle_consensus_reached
                
        except Exception as e:
            logger.error(f"Error checking consensus failures: {e}")
            
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about contract events (chain-only, from cache)"""
        try:
            # Get recent events from cache (last 10)
            recent_events = list(self.event_cache)[-10:] if self.event_cache else []
            
            return {
                'event_counts': dict(self.metrics_cache['events_by_type']),
                'recent_events': [
                    {
                        'type': event.get('event_name'),
                        'tx_hash': event.get('transaction_hash', '')[:10] + '...' if event.get('transaction_hash') else None,
                        'block': event.get('block_number'),
                        'timestamp': event.get('timestamp').isoformat() if event.get('timestamp') else None
                    }
                    for event in recent_events
                ],
                'last_processed_block': self.last_processed_block,
                'total_events_processed': self.metrics_cache['total_events'],
                'gas_spike_count': self.metrics_cache['gas_spike_count'],
                'consensus_failure_count': self.metrics_cache['consensus_failure_count']
            }
            
        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}
            
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a complete monitoring cycle"""
        logger.debug("Running contract monitoring cycle")
        
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'events': self.process_events(),
            'statistics': self.get_event_statistics()
        }
        
        # Log any alerts
        if results['events']['gas_spike_alerts']:
            logger.warning(f"Gas spike alerts: {results['events']['gas_spike_alerts']}")
            
        if results['events']['consensus_failures']:
            logger.warning(f"Consensus failures: {results['events']['consensus_failures']}")
            
        return results