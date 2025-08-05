"""
Advanced Markets Service (Phase 13)
Handles multi-choice, conditional, and range prediction markets
"""

import logging
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from web3 import Web3
from eth_account import Account

logger = logging.getLogger(__name__)

class AdvancedMarketsService:
    """Service for advanced market types and features"""
    
    def __init__(self, blockchain_service, distributed_storage):
        self.blockchain = blockchain_service
        self.storage = distributed_storage
        self.w3 = blockchain_service.w3
        
        # Load contract
        self.contract = None
        self._load_contract()
        
        # Cache for market metadata
        self.market_cache = {}
        
    def _load_contract(self):
        """Load AdvancedMarkets contract"""
        try:
            with open('deployments/base-sepolia.json', 'r') as f:
                deployments = json.load(f)
                
            if 'AdvancedMarkets' in deployments:
                address = deployments['AdvancedMarkets']['address']
                
                # Load ABI
                with open('artifacts/contracts/src/AdvancedMarkets.sol/AdvancedMarkets.json', 'r') as f:
                    artifact = json.load(f)
                    abi = artifact['abi']
                    
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(address),
                    abi=abi
                )
                logger.info("AdvancedMarkets contract loaded")
        except Exception as e:
            logger.warning(f"Could not load AdvancedMarkets contract: {e}")
            
    def create_multi_choice_market(
        self,
        market_id: str,
        actor_address: str,
        question: str,
        options: List[str],
        start_time: int,
        end_time: int,
        oracle_fee: int,
        private_key: str
    ) -> Optional[Dict]:
        """Create a multi-choice prediction market"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Build transaction
            tx = self.contract.functions.createMultiChoiceMarket(
                Web3.to_bytes(hexstr=market_id),  # type: ignore
                options,
                end_time
            ).build_transaction({
                'from': account.address,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Store metadata in IPFS
            metadata = {
                'market_id': market_id,
                'type': 'multi_choice',
                'actor_address': actor_address,
                'question': question,
                'options': options,
                'start_time': start_time,
                'end_time': end_time,
                'created_at': datetime.utcnow().isoformat(),
                'tx_hash': tx_hash.hex()
            }
            
            ipfs_hash = self.storage.store_market_data(market_id, metadata)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'market_id': market_id,
                'ipfs_hash': ipfs_hash,
                'gas_used': receipt['gasUsed']
            }
            
        except Exception as e:
            logger.error(f"Error creating multi-choice market: {e}")
            return {'success': False, 'error': str(e)}
            
    def create_conditional_market(
        self,
        market_id: str,
        depends_on_market_id: str,
        condition_description: str,
        end_time: int,
        private_key: str
    ) -> Optional[Dict]:
        """Create a conditional market that depends on another market's outcome"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Build transaction
            tx = self.contract.functions.createConditionalMarket(
                Web3.to_bytes(hexstr=market_id),  # type: ignore
                Web3.to_bytes(hexstr=depends_on_market_id),  # type: ignore
                end_time
            ).build_transaction({
                'from': account.address,
                'gas': 400000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Store metadata
            metadata = {
                'market_id': market_id,
                'type': 'conditional',
                'depends_on': depends_on_market_id,
                'condition': condition_description,
                'end_time': end_time,
                'created_at': datetime.utcnow().isoformat(),
                'tx_hash': tx_hash.hex()
            }
            
            ipfs_hash = self.storage.store_market_data(market_id, metadata)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'market_id': market_id,
                'ipfs_hash': ipfs_hash,
                'gas_used': receipt['gasUsed']
            }
            
        except Exception as e:
            logger.error(f"Error creating conditional market: {e}")
            return {'success': False, 'error': str(e)}
            
    def create_range_market(
        self,
        market_id: str,
        actor_address: str,
        metric_description: str,
        min_value: int,
        max_value: int,
        end_time: int,
        private_key: str
    ) -> Optional[Dict]:
        """Create a numeric range prediction market"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Build transaction
            tx = self.contract.functions.createRangeMarket(
                Web3.to_bytes(hexstr=market_id),  # type: ignore
                min_value,
                max_value,
                end_time
            ).build_transaction({
                'from': account.address,
                'gas': 400000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Store metadata
            metadata = {
                'market_id': market_id,
                'type': 'range',
                'actor_address': actor_address,
                'metric': metric_description,
                'min_value': min_value,
                'max_value': max_value,
                'end_time': end_time,
                'created_at': datetime.utcnow().isoformat(),
                'tx_hash': tx_hash.hex()
            }
            
            ipfs_hash = self.storage.store_market_data(market_id, metadata)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'market_id': market_id,
                'ipfs_hash': ipfs_hash,
                'gas_used': receipt['gasUsed']
            }
            
        except Exception as e:
            logger.error(f"Error creating range market: {e}")
            return {'success': False, 'error': str(e)}
            
    def bet_on_option(
        self,
        market_id: str,
        option_id: str,
        amount_wei: int,
        private_key: str
    ) -> Optional[Dict]:
        """Place a bet on a multi-choice option"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Build transaction
            tx = self.contract.functions.betOnOption(
                Web3.to_bytes(hexstr=market_id),  # type: ignore
                Web3.to_bytes(hexstr=option_id)  # type: ignore
            ).build_transaction({
                'from': account.address,
                'value': amount_wei,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed']
            }
            
        except Exception as e:
            logger.error(f"Error betting on option: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_user_reputation(self, user_address: str) -> int:
        """Get user's reputation score"""
        if not self.contract:
            return 0
            
        try:
            reputation = self.contract.functions.calculateReputation(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return reputation
            
        except Exception as e:
            logger.error(f"Error getting user reputation: {e}")
            return 0
            
    def get_market_details(self, market_id: str) -> Optional[Dict]:
        """Get detailed information about an advanced market"""
        if not self.contract:
            return None
            
        try:
            # Get on-chain data
            result = self.contract.functions.getAdvancedMarket(
                Web3.to_bytes(hexstr=market_id)  # type: ignore
            ).call()
            
            market_type, option_count, depends_on, min_value, max_value = result
            
            # Get metadata from IPFS if available
            metadata = None
            if market_id in self.market_cache:
                ipfs_hash = self.market_cache[market_id]
                metadata = self.storage.retrieve_market_data(ipfs_hash)
                
            return {
                'market_id': market_id,
                'market_type': market_type,
                'option_count': option_count,
                'depends_on': depends_on.hex() if depends_on else None,
                'min_value': min_value,
                'max_value': max_value,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting market details: {e}")
            return None
            
    def generate_analytics_report(self) -> Dict:
        """Generate analytics report for advanced markets"""
        analytics = {
            'timestamp': datetime.utcnow().isoformat(),
            'multi_choice_markets': 0,
            'conditional_markets': 0,
            'range_markets': 0,
            'total_reputation_points': 0,
            'active_users': 0
        }
        
        # Store in IPFS
        ipfs_hash = self.storage.store_analytics_report('advanced_markets', analytics)
        analytics['ipfs_hash'] = ipfs_hash
        
        return analytics