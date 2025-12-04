"""
Blockchain-Only Data Service (Phase 12)
Eliminates PostgreSQL dependencies - blockchain as single source of truth
"""

import logging
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timezone
from web3 import Web3
from eth_account import Account
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)

class BlockchainOnlyDataService:
    """Service for blockchain-only data operations without PostgreSQL"""
    
    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
        self.w3 = blockchain_service.w3
        
        # Local cache for performance (rebuilt from blockchain events)
        self.cache = {
            'markets': {},
            'submissions': defaultdict(list),
            'bets': defaultdict(list),
            'actors': {},
            'nodes': {},
            'transactions': defaultdict(list)
        }
        
        # Load contracts
        self.contracts = {}
        self._load_contracts()
        
        # Initialize event filters
        self.event_filters = {}
        self._setup_event_filters()
        
    def _load_contracts(self):
        """Load all necessary contracts"""
        contract_names = [
            'EnhancedPredictionMarket',
            'ActorRegistry',
            'NodeRegistry',
            'DecentralizedOracle',
            'PayoutManager'
        ]
        
        for contract_name in contract_names:
            try:
                with open('deployments/base-sepolia.json', 'r') as f:
                    deployments = json.load(f)
                    
                if contract_name in deployments:
                    address = deployments[contract_name]['address']
                    
                    # Load ABI
                    with open(f'artifacts/contracts/src/{contract_name}.sol/{contract_name}.json', 'r') as f:
                        artifact = json.load(f)
                        abi = artifact['abi']
                        
                    self.contracts[contract_name] = self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=abi
                    )
                    logger.info(f"{contract_name} contract loaded")
            except Exception as e:
                logger.warning(f"Could not load {contract_name}: {e}")
                
    def _setup_event_filters(self):
        """Setup event filters for real-time updates"""
        try:
            if 'EnhancedPredictionMarket' in self.contracts:
                contract = self.contracts['EnhancedPredictionMarket']
                
                # Market events
                self.event_filters['MarketCreated'] = contract.events.MarketCreated.create_filter(
                    fromBlock='latest'
                )
                self.event_filters['SubmissionCreated'] = contract.events.SubmissionCreated.create_filter(
                    fromBlock='latest'
                )
                self.event_filters['BetPlaced'] = contract.events.BetPlaced.create_filter(
                    fromBlock='latest'
                )
                self.event_filters['MarketResolved'] = contract.events.MarketResolved.create_filter(
                    fromBlock='latest'
                )
                
            if 'ActorRegistry' in self.contracts:
                contract = self.contracts['ActorRegistry']
                
                # Actor events
                self.event_filters['ActorProposed'] = contract.events.ActorProposed.create_filter(
                    fromBlock='latest'
                )
                self.event_filters['ActorActivated'] = contract.events.ActorActivated.create_filter(
                    fromBlock='latest'
                )
                
            logger.info("Event filters setup successfully")
            
        except Exception as e:
            logger.error(f"Error setting up event filters: {e}")
            
    async def rebuild_cache_from_events(self, from_block: int = 0):
        """Rebuild local cache from blockchain events"""
        logger.info(f"Rebuilding cache from block {from_block}")
        
        try:
            if 'EnhancedPredictionMarket' in self.contracts:
                contract = self.contracts['EnhancedPredictionMarket']
                
                # Get all MarketCreated events
                market_events = contract.events.MarketCreated.get_logs(
                    fromBlock=from_block,
                    toBlock='latest'
                )
                
                for event in market_events:
                    market_id = event['args']['marketId']
                    self.cache['markets'][market_id] = {
                        'id': market_id,
                        'actor': event['args']['actor'],
                        'creator': event['args']['creator'],
                        'start_time': event['args']['startTime'],
                        'end_time': event['args']['endTime'],
                        'created_at': event['blockNumber'],
                        'resolved': False
                    }
                    
                # Get all SubmissionCreated events
                submission_events = contract.events.SubmissionCreated.get_logs(
                    fromBlock=from_block,
                    toBlock='latest'
                )
                
                for event in submission_events:
                    market_id = event['args']['marketId']
                    submission = {
                        'id': event['args']['submissionId'],
                        'market_id': market_id,
                        'submitter': event['args']['submitter'],
                        'predicted_text': event['args']['predictedText'],
                        'stake': event['args']['stake'],
                        'submission_type': event['args']['submissionType'],
                        'created_at': event['blockNumber']
                    }
                    self.cache['submissions'][market_id].append(submission)
                    
                # Get all BetPlaced events
                bet_events = contract.events.BetPlaced.get_logs(
                    fromBlock=from_block,
                    toBlock='latest'
                )
                
                for event in bet_events:
                    submission_id = event['args']['submissionId']
                    bet = {
                        'bettor': event['args']['bettor'],
                        'submission_id': submission_id,
                        'amount': event['args']['amount'],
                        'created_at': event['blockNumber']
                    }
                    self.cache['bets'][submission_id].append(bet)
                    
                logger.info(f"Cache rebuilt: {len(self.cache['markets'])} markets loaded")
                
        except Exception as e:
            logger.error(f"Error rebuilding cache: {e}")
            
    def get_active_markets(self) -> List[Dict]:
        """Get all active markets from blockchain"""
        active_markets = []
        current_time = int(datetime.now(timezone.utc).timestamp())
        
        for market_id, market in self.cache['markets'].items():
            if (market['start_time'] <= current_time <= market['end_time'] and 
                not market['resolved']):
                active_markets.append(market)
                
        return active_markets
        
    def get_expired_markets(self) -> List[Dict]:
        """Get all expired but unresolved markets"""
        expired_markets = []
        current_time = int(datetime.now(timezone.utc).timestamp())
        
        for market_id, market in self.cache['markets'].items():
            if market['end_time'] < current_time and not market['resolved']:
                expired_markets.append(market)
                
        return expired_markets
        
    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get detailed market information from blockchain"""
        if 'EnhancedPredictionMarket' not in self.contracts:
            return None
            
        try:
            contract = self.contracts['EnhancedPredictionMarket']
            market_id_bytes = Web3.to_bytes(hexstr=market_id)  # type: ignore
            
            # Get on-chain data
            result = contract.functions.getMarket(market_id_bytes).call()
            
            market_data = {
                'id': market_id,
                'actor': result[0],
                'start_time': result[1],
                'end_time': result[2],
                'resolved': result[3],
                'winning_submission_id': result[4].hex() if result[4] else None,
                'total_pool': result[5],
                'submissions': self.cache['submissions'].get(market_id, [])
            }
            
            # Get actor details
            if 'ActorRegistry' in self.contracts:
                actor_contract = self.contracts['ActorRegistry']
                actor_data = actor_contract.functions.getActor(result[0]).call()
                market_data['actor_details'] = {
                    'x_username': actor_data[0],
                    'display_name': actor_data[1],
                    'verified': actor_data[4],
                    'follower_count': actor_data[5]
                }
                
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market details: {e}")
            return None
            
    def get_user_activity(self, wallet_address: str) -> Dict:
        """Get all user activity from blockchain events"""
        wallet_address = Web3.to_checksum_address(wallet_address)
        
        activity = {
            'markets_created': [],
            'submissions': [],
            'bets': [],
            'winnings': 0
        }
        
        # Find markets created by user
        for market_id, market in self.cache['markets'].items():
            if market['creator'] == wallet_address:
                activity['markets_created'].append(market)
                
        # Find submissions by user
        for market_submissions in self.cache['submissions'].values():
            for submission in market_submissions:
                if submission['submitter'] == wallet_address:
                    activity['submissions'].append(submission)
                    
        # Find bets by user
        for submission_bets in self.cache['bets'].values():
            for bet in submission_bets:
                if bet['bettor'] == wallet_address:
                    activity['bets'].append(bet)
                    
        return activity
        
    def get_node_operators(self) -> List[Dict]:
        """Get all registered node operators from blockchain"""
        if 'NodeRegistry' not in self.contracts:
            return []
            
        try:
            contract = self.contracts['NodeRegistry']
            
            # Get node count
            node_count = contract.functions.getActiveNodeCount().call()
            
            nodes = []
            # Note: This assumes the contract has a way to enumerate nodes
            # In practice, you'd need to track NodeRegistered events
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error getting node operators: {e}")
            return []
            
    def subscribe_to_events(self, callback):
        """Subscribe to real-time blockchain events"""
        async def event_loop():
            while True:
                try:
                    for event_name, event_filter in self.event_filters.items():
                        for event in event_filter.get_new_entries():
                            # Update cache
                            self._process_event(event_name, event)
                            # Notify callback
                            callback(event_name, event)
                            
                    await asyncio.sleep(2)  # Poll every 2 seconds
                    
                except Exception as e:
                    logger.error(f"Error in event subscription: {e}")
                    await asyncio.sleep(5)
                    
        return event_loop()
        
    def _process_event(self, event_name: str, event):
        """Process blockchain event and update cache"""
        try:
            if event_name == 'MarketCreated':
                market_id = event['args']['marketId']
                self.cache['markets'][market_id] = {
                    'id': market_id,
                    'actor': event['args']['actor'],
                    'creator': event['args']['creator'],
                    'start_time': event['args']['startTime'],
                    'end_time': event['args']['endTime'],
                    'created_at': event['blockNumber'],
                    'resolved': False
                }
                
            elif event_name == 'SubmissionCreated':
                market_id = event['args']['marketId']
                submission = {
                    'id': event['args']['submissionId'],
                    'market_id': market_id,
                    'submitter': event['args']['submitter'],
                    'predicted_text': event['args']['predictedText'],
                    'stake': event['args']['stake'],
                    'submission_type': event['args']['submissionType'],
                    'created_at': event['blockNumber']
                }
                self.cache['submissions'][market_id].append(submission)
                
            elif event_name == 'BetPlaced':
                submission_id = event['args']['submissionId']
                bet = {
                    'bettor': event['args']['bettor'],
                    'submission_id': submission_id,
                    'amount': event['args']['amount'],
                    'created_at': event['blockNumber']
                }
                self.cache['bets'][submission_id].append(bet)
                
            elif event_name == 'MarketResolved':
                market_id = event['args']['marketId']
                if market_id in self.cache['markets']:
                    self.cache['markets'][market_id]['resolved'] = True
                    self.cache['markets'][market_id]['winning_submission_id'] = event['args']['winningSubmissionId']
                    
        except Exception as e:
            logger.error(f"Error processing event {event_name}: {e}")
            
    def get_market_statistics(self) -> Dict:
        """Get overall platform statistics from blockchain data"""
        stats = {
            'total_markets': len(self.cache['markets']),
            'active_markets': len(self.get_active_markets()),
            'resolved_markets': sum(1 for m in self.cache['markets'].values() if m['resolved']),
            'total_submissions': sum(len(subs) for subs in self.cache['submissions'].values()),
            'total_bets': sum(len(bets) for bets in self.cache['bets'].values()),
            'total_volume': 0  # Would need to sum from events
        }
        
        return stats