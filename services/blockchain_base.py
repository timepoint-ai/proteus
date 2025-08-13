import logging
import json
from web3 import Web3
from web3.exceptions import Web3Exception
from eth_account import Account
from decimal import Decimal
from typing import Dict, Any, Optional, List
import os
from config import Config

logger = logging.getLogger(__name__)

class BaseBlockchainService:
    """BASE blockchain service for interacting with smart contracts"""
    
    def __init__(self):
        # Initialize BASE Web3 provider
        network = os.environ.get('NETWORK', 'testnet')
        if network == 'mainnet':
            self.rpc_url = os.environ.get('BASE_RPC_URL', 'https://mainnet.base.org')
            self.chain_id = 8453
            self.is_testnet = False
        else:
            self.rpc_url = os.environ.get('BASE_SEPOLIA_RPC_URL', 'https://sepolia.base.org')
            self.chain_id = 84532
            self.is_testnet = True
            
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Contract addresses (to be loaded from deployment files)
        self.contracts = {
            'PredictionMarket': None,
            'ClockchainOracle': None,
            'NodeRegistry': None,
            'PayoutManager': None,
            'ActorRegistry': None,
            'EnhancedPredictionMarket': None,
            'DecentralizedOracle': None,
            'AdvancedMarkets': None,
            'SecurityAudit': None
        }
        
        # Load ABIs
        self.abis = self._load_abis()
        
        # Platform fee percentage
        self.platform_fee_percentage = Decimal(os.environ.get('PLATFORM_FEE', '7')) / Decimal('100')
        
        # Auto-load deployment configuration
        deployment_file = 'deployment-base-sepolia.json' if self.is_testnet else 'deployment-base-mainnet.json'
        if os.path.exists(deployment_file):
            self.load_contracts(deployment_file)
            logger.info(f"Loaded contracts from {deployment_file}")
        
    def _load_abis(self) -> Dict[str, Any]:
        """Load contract ABIs from compiled artifacts"""
        abis = {}
        try:
            # Load from Hardhat artifacts
            artifacts_dir = 'artifacts/contracts/src'
            contract_names = [
                'PredictionMarket', 'ClockchainOracle', 'NodeRegistry', 'PayoutManager',
                'ActorRegistry', 'EnhancedPredictionMarket', 'DecentralizedOracle',
                'AdvancedMarkets', 'SecurityAudit'
            ]
            for contract_name in contract_names:
                abi_path = f"{artifacts_dir}/{contract_name}.sol/{contract_name}.json"
                if os.path.exists(abi_path):
                    with open(abi_path, 'r') as f:
                        artifact = json.load(f)
                        abis[contract_name] = artifact['abi']
                        logger.info(f"Loaded ABI for {contract_name}")
                else:
                    logger.warning(f"ABI file not found for {contract_name} at {abi_path}")
        except Exception as e:
            logger.error(f"Error loading ABIs: {e}")
        return abis
        
    def load_contracts(self, deployment_file: str):
        """Load contract addresses from deployment file"""
        try:
            with open(deployment_file, 'r') as f:
                deployment = json.load(f)
                
                # Handle deployment file format
                if 'contracts' in deployment:
                    for contract_name, contract_info in deployment['contracts'].items():
                        if contract_name in self.abis:
                            # Handle both string addresses and dict format
                            if isinstance(contract_info, str):
                                address = contract_info
                            elif isinstance(contract_info, dict) and 'address' in contract_info:
                                address = contract_info['address']
                            else:
                                continue
                                
                            self.contracts[contract_name] = self.w3.eth.contract(
                                address=Web3.to_checksum_address(address),
                                abi=self.abis[contract_name]
                            )
                            logger.info(f"Loaded {contract_name} at {address}")
        except Exception as e:
            logger.error(f"Error loading contracts: {e}")
    
    def get_contract(self, contract_name: str, address: str = None):
        """Get a contract instance by name or address"""
        try:
            if address:
                # Create contract instance with provided address
                if contract_name in self.abis:
                    return self.w3.eth.contract(
                        address=Web3.to_checksum_address(address),
                        abi=self.abis[contract_name]
                    )
            else:
                # Return already loaded contract
                return self.contracts.get(contract_name)
        except Exception as e:
            logger.error(f"Error getting contract {contract_name}: {e}")
            return None
            
    def validate_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Validate a BASE transaction"""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:  # Success
                return {
                    'hash': tx_hash,
                    'from': tx['from'],
                    'to': tx['to'],
                    'value': Web3.from_wei(tx['value'], 'ether'),
                    'block_number': receipt['blockNumber'],
                    'status': 'confirmed',
                    'gas_used': receipt['gasUsed'],
                    'gas_price': Web3.from_wei(tx.get('gasPrice', 0), 'gwei')
                }
            else:
                logger.error(f"BASE transaction {tx_hash} failed")
                return None
                
        except Web3Exception as e:
            logger.error(f"Error validating BASE transaction {tx_hash}: {e}")
            return None
            
    def get_balance(self, address: str) -> Decimal:
        """Get BASE (ETH) balance for an address"""
        try:
            balance_wei = self.w3.eth.get_balance(address)
            return Decimal(Web3.from_wei(balance_wei, 'ether'))
        except Web3Exception as e:
            logger.error(f"Error getting BASE balance for {address}: {e}")
            return Decimal(0)
            
    def estimate_gas_price(self) -> Dict[str, int]:
        """Estimate current gas prices on BASE"""
        try:
            gas_price = self.w3.eth.gas_price
            return {
                'standard': gas_price,
                'fast': int(gas_price * 1.2),
                'slow': int(gas_price * 0.8)
            }
        except Web3Exception as e:
            logger.error(f"Error estimating gas price: {e}")
            # BASE typical gas prices are very low
            return {
                'standard': 1000000000,  # 1 gwei
                'fast': 1200000000,      # 1.2 gwei
                'slow': 800000000        # 0.8 gwei
            }
            
    # READ-ONLY BLOCKCHAIN METHODS (Phase 1B Implementation)
    
    def get_actor(self, actor_address: str) -> Optional[Dict[str, Any]]:
        """Get actor details from ActorRegistry contract"""
        try:
            contract = self.contracts.get('ActorRegistry')
            if not contract:
                logger.error("ActorRegistry contract not loaded")
                return None
                
            # Call getActor function
            result = contract.functions.getActor(Web3.to_checksum_address(actor_address)).call()
            if result[0]:  # isRegistered
                return {
                    'address': actor_address,
                    'username': result[1],
                    'is_registered': result[0],
                    'registration_time': result[2],
                    'reputation': result[3]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting actor {actor_address}: {e}")
            return None
            
    def get_market(self, market_id: int) -> Optional[Dict[str, Any]]:
        """Get market details from EnhancedPredictionMarket contract"""
        try:
            contract = self.contracts.get('EnhancedPredictionMarket')
            if not contract:
                logger.error("EnhancedPredictionMarket contract not loaded")
                return None
                
            # Call getMarket function
            result = contract.functions.getMarket(market_id).call()
            return {
                'id': market_id,
                'question': result[0],
                'actor_username': result[1],
                'creator': result[2],
                'start_time': result[3],
                'end_time': result[4],
                'resolved': result[5],
                'winning_submission_id': result[6],
                'total_volume': result[7],
                'platform_fee_collected': result[8]
            }
        except Exception as e:
            logger.error(f"Error getting market {market_id}: {e}")
            return None
            
    def get_submission(self, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get submission details from EnhancedPredictionMarket contract"""
        try:
            contract = self.contracts.get('EnhancedPredictionMarket')
            if not contract:
                logger.error("EnhancedPredictionMarket contract not loaded")
                return None
                
            # Call getSubmission function
            result = contract.functions.getSubmission(submission_id).call()
            return {
                'id': submission_id,
                'market_id': result[0],
                'creator': result[1],
                'predicted_text': result[2],
                'stake': result[3],
                'total_bets': result[4],
                'bet_count': result[5],
                'levenshtein_distance': result[6],
                'is_winner': result[7]
            }
        except Exception as e:
            logger.error(f"Error getting submission {submission_id}: {e}")
            return None
            
    def get_oracle_submission(self, market_id: int, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get oracle submission from DecentralizedOracle contract"""
        try:
            contract = self.contracts.get('DecentralizedOracle')
            if not contract:
                logger.error("DecentralizedOracle contract not loaded")
                return None
                
            # Call getOracleData function
            result = contract.functions.getOracleData(
                Web3.keccak(text=str(market_id)),
                Web3.keccak(text=str(submission_id))
            ).call()
            
            return {
                'actual_text': result[0],
                'screenshot_ipfs': result[1],
                'text_hash': result[2].hex(),
                'levenshtein_distance': result[3],
                'validators': result[4],
                'consensus_reached': result[5]
            }
        except Exception as e:
            logger.error(f"Error getting oracle submission: {e}")
            return None
            
    # ====================================================================
    # WRITE OPERATIONS REMOVED (Phase 1 Cleanup - BASE-Only Architecture)
    # ====================================================================
    # All write operations should be handled directly from the frontend
    # using Web3.js or ethers.js to interact with contracts directly.
    # This service now only provides READ-ONLY blockchain access.
    # 
    # Removed operations:
    # - create_submission()
    # - place_bet()
    # - submit_oracle_data()
    # - register_node()
    # - claim_payout()
    # - send_transaction()
    # - wait_for_transaction()
    # ====================================================================
            
    def get_market_details(self, market_id: int) -> Optional[Dict[str, Any]]:
        """Get market details from contract"""
        try:
            if not self.contracts['PredictionMarket']:
                raise ValueError("PredictionMarket contract not loaded")
                
            contract = self.contracts['PredictionMarket']
            market = contract.functions.markets(market_id).call()
            
            return {
                'question': market[0],
                'creator': market[1],
                'start_time': market[2],
                'end_time': market[3],
                'resolved': market[4],
                'winning_submission_id': market[5],
                'total_volume': Web3.from_wei(market[6], 'ether'),
                'actor_twitter_handle': market[7],
                'target_tweet_id': market[8],
                'xcom_only': market[9],
                'platform_fee_collected': Web3.from_wei(market[10], 'ether')
            }
            
        except Exception as e:
            logger.error(f"Error getting market details: {e}")
            return None
            
    def calculate_platform_fee(self, amount: Decimal) -> Decimal:
        """Calculate platform fee for a given amount"""
        return amount * self.platform_fee_percentage