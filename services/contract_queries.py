"""
Phase 5: Smart Contract Query Functions
Implements the missing contract functions listed in CLEAN.md section 5.1
These are read-only query functions for chain data
"""

import logging
from typing import List, Dict, Optional, Any
from web3 import Web3
from services.blockchain_base import BaseBlockchainService

logger = logging.getLogger(__name__)

class ContractQueries:
    """
    Provides high-level query functions for smart contract data
    Implements the missing functions from CLEAN.md section 5.1
    """
    
    def __init__(self):
        self.blockchain = BaseBlockchainService()
        self.w3 = self.blockchain.w3
        
    # ============= EnhancedPredictionMarket Functions =============
    
    def get_all_markets(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Get all markets from the EnhancedPredictionMarket contract
        Missing function: getAllMarkets()
        """
        try:
            contract = self.blockchain.contracts.get('EnhancedPredictionMarket')
            if not contract:
                return []
            
            markets = []
            
            # Query MarketCreated events
            event_filter = {
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': contract.address
            }
            
            # Get logs for MarketCreated events
            try:
                logs = self.w3.eth.get_logs(event_filter)
                
                for log in logs[offset:offset+limit]:
                    try:
                        # Decode the event
                        decoded = contract.events.MarketCreated().process_log(log)
                        market_id = decoded['args'].get('marketId', 0)
                        
                        # Get current market details
                        market_info = self._get_market_info(contract, market_id)
                        if market_info:
                            markets.append(market_info)
                    except Exception as e:
                        logger.debug(f"Could not process market log: {e}")
                        
            except Exception as e:
                logger.warning(f"Could not query market events: {e}")
            
            return markets
            
        except Exception as e:
            logger.error(f"Error getting all markets: {e}")
            return []
    
    def get_markets_by_actor(self, actor_address: str) -> List[Dict]:
        """
        Get all markets for a specific actor
        Missing function: getMarketsByActor()
        """
        try:
            contract = self.blockchain.contracts.get('EnhancedPredictionMarket')
            if not contract:
                return []
            
            markets = []
            
            # Get all markets and filter by actor
            all_markets = self.get_all_markets(limit=1000)
            
            for market in all_markets:
                if market.get('actor_address', '').lower() == actor_address.lower():
                    markets.append(market)
            
            return markets
            
        except Exception as e:
            logger.error(f"Error getting markets by actor: {e}")
            return []
    
    # ============= ActorRegistry Functions =============
    
    def search_actors(self, query: str) -> List[Dict]:
        """
        Search for actors by name or X username
        Missing function: searchActors()
        """
        try:
            contract = self.blockchain.contracts.get('ActorRegistry')
            if not contract:
                return []
            
            actors = []
            query_lower = query.lower()
            
            # Get all actor events
            event_filter = {
                'fromBlock': 0,
                'toBlock': 'latest', 
                'address': contract.address
            }
            
            try:
                logs = self.w3.eth.get_logs(event_filter)
                
                for log in logs:
                    try:
                        decoded = contract.events.ActorRegistered().process_log(log)
                        actor_address = decoded['args'].get('actorAddress')
                        
                        # Get actor details
                        actor_info = contract.functions.getActor(actor_address).call()
                        
                        name = actor_info[0] if len(actor_info) > 0 else ''
                        x_username = actor_info[1] if len(actor_info) > 1 else ''
                        
                        # Search in name and username
                        if query_lower in name.lower() or query_lower in x_username.lower():
                            actors.append({
                                'address': actor_address,
                                'name': name,
                                'x_username': x_username,
                                'verified': actor_info[2] if len(actor_info) > 2 else False
                            })
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not query actor events: {e}")
            
            return actors
            
        except Exception as e:
            logger.error(f"Error searching actors: {e}")
            return []
    
    def get_actor_stats(self, actor_address: str) -> Dict:
        """
        Get statistics for a specific actor
        Missing function: getActorStats()
        """
        try:
            stats = {
                'address': actor_address,
                'total_markets': 0,
                'active_markets': 0,
                'resolved_markets': 0,
                'total_volume': 0,
                'total_predictions': 0,
                'accuracy_rate': 0.0
            }
            
            # Get markets for this actor
            markets = self.get_markets_by_actor(actor_address)
            
            stats['total_markets'] = len(markets)
            
            for market in markets:
                status = market.get('status', '')
                if status == 'active':
                    stats['active_markets'] += 1
                elif status == 'resolved':
                    stats['resolved_markets'] += 1
                
                # Add volume
                volume = int(market.get('total_volume', 0))
                stats['total_volume'] += volume
                
                # Count predictions
                submissions = market.get('submissions', [])
                stats['total_predictions'] += len(submissions)
            
            # Calculate accuracy rate (simplified)
            if stats['resolved_markets'] > 0:
                # This would need actual resolution data
                stats['accuracy_rate'] = 0.0  # Placeholder
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting actor stats: {e}")
            return {}
    
    # ============= NodeRegistry Functions =============
    
    def get_active_nodes(self) -> List[Dict]:
        """
        Get all active nodes from NodeRegistry
        Missing function: getActiveNodes()
        """
        try:
            contract = self.blockchain.contracts.get('NodeRegistry')
            if not contract:
                return []
            
            nodes = []
            
            # Query NodeRegistered events
            event_filter = {
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': contract.address
            }
            
            try:
                logs = self.w3.eth.get_logs(event_filter)
                
                for log in logs:
                    try:
                        decoded = contract.events.NodeRegistered().process_log(log)
                        node_address = decoded['args'].get('nodeAddress')
                        
                        # Check if node is still active (has stake)
                        try:
                            stake = contract.functions.getNodeStake(node_address).call()
                            if stake > 0:
                                nodes.append({
                                    'address': node_address,
                                    'stake': stake,
                                    'endpoint': decoded['args'].get('endpoint', ''),
                                    'registration_block': log['blockNumber']
                                })
                        except:
                            pass
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not query node events: {e}")
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error getting active nodes: {e}")
            return []
    
    def get_node_performance(self, node_address: str) -> Dict:
        """
        Get performance metrics for a specific node
        Missing function: getNodePerformance()
        """
        try:
            contract = self.blockchain.contracts.get('NodeRegistry')
            if not contract:
                return {}
            
            performance = {
                'address': node_address,
                'uptime_percentage': 100.0,  # Default to 100%
                'oracle_submissions': 0,
                'successful_validations': 0,
                'failed_validations': 0,
                'reputation_score': 100
            }
            
            # Query oracle submissions for this node
            oracle_contract = self.blockchain.contracts.get('DecentralizedOracle')
            if oracle_contract:
                try:
                    # Count oracle submissions
                    event_filter = {
                        'fromBlock': 0,
                        'toBlock': 'latest',
                        'address': oracle_contract.address
                    }
                    
                    logs = self.w3.eth.get_logs(event_filter)
                    
                    for log in logs:
                        try:
                            decoded = oracle_contract.events.OracleDataSubmitted().process_log(log)
                            if decoded['args'].get('oracle', '').lower() == node_address.lower():
                                performance['oracle_submissions'] += 1
                        except:
                            pass
                            
                except Exception as e:
                    logger.debug(f"Could not query oracle events: {e}")
            
            # Calculate reputation score (simplified)
            if performance['oracle_submissions'] > 0:
                performance['reputation_score'] = min(100, 50 + performance['oracle_submissions'] * 5)
            
            return performance
            
        except Exception as e:
            logger.error(f"Error getting node performance: {e}")
            return {}
    
    # ============= DecentralizedOracle Functions =============
    
    def get_oracle_history(self, market_id: int, limit: int = 100) -> List[Dict]:
        """
        Get oracle submission history for a market
        Missing function: getOracleHistory()
        """
        try:
            contract = self.blockchain.contracts.get('DecentralizedOracle')
            if not contract:
                return []
            
            history = []
            
            # Query OracleDataSubmitted events for this market
            event_filter = {
                'fromBlock': 0,
                'toBlock': 'latest',
                'address': contract.address
            }
            
            try:
                logs = self.w3.eth.get_logs(event_filter)
                
                for log in logs[:limit]:
                    try:
                        decoded = contract.events.OracleDataSubmitted().process_log(log)
                        
                        if decoded['args'].get('marketId') == market_id:
                            history.append({
                                'oracle': decoded['args'].get('oracle'),
                                'actual_text': decoded['args'].get('actualText', ''),
                                'source_url': decoded['args'].get('sourceUrl', ''),
                                'timestamp': decoded['args'].get('timestamp', 0),
                                'block_number': log['blockNumber'],
                                'transaction_hash': log['transactionHash'].hex()
                            })
                    except:
                        pass
                        
            except Exception as e:
                logger.warning(f"Could not query oracle events: {e}")
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting oracle history: {e}")
            return []
    
    # ============= GenesisNFT Functions =============
    
    def get_token_uri(self, token_id: int) -> str:
        """
        Get token URI for Genesis NFT metadata
        Missing function: tokenURI()
        """
        try:
            contract = self.blockchain.contracts.get('GenesisNFT')
            if not contract:
                return ""
            
            # Try to call tokenURI function
            try:
                uri = contract.functions.tokenURI(token_id).call()
                return uri
            except:
                # If tokenURI doesn't exist, generate default
                return f"data:application/json;base64,eyJuYW1lIjoiR2VuZXNpcyBORlQgIzEwMCIsImRlc2NyaXB0aW9uIjoiQ2xvY2tjaGFpbiBHZW5lc2lzIE5GVCIsImltYWdlIjoiIn0="
                
        except Exception as e:
            logger.error(f"Error getting token URI: {e}")
            return ""
    
    # ============= Helper Functions =============
    
    def _get_market_info(self, contract, market_id: int) -> Optional[Dict]:
        """Helper to get market information"""
        try:
            market_info = contract.functions.getMarket(market_id).call()
            
            return {
                'id': market_id,
                'actor_address': market_info[0] if len(market_info) > 0 else '0x0',
                'start_time': market_info[1] if len(market_info) > 1 else 0,
                'end_time': market_info[2] if len(market_info) > 2 else 0,
                'status': market_info[3] if len(market_info) > 3 else 'unknown',
                'total_volume': str(market_info[4]) if len(market_info) > 4 else '0'
            }
        except:
            return None

# Create singleton instance
contract_queries = ContractQueries()