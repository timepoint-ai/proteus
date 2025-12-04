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
            'PredictionMarketV2': None,  # New V2 with resolution mechanism
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
                'PredictionMarket', 'PredictionMarketV2', 'ClockchainOracle', 'NodeRegistry',
                'PayoutManager', 'ActorRegistry', 'EnhancedPredictionMarket', 'DecentralizedOracle',
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

    # ====================================================================
    # SIMPLE PREDICTION MARKET METHODS (PredictionMarket contract)
    # ====================================================================
    # These methods work with the simple PredictionMarket contract that
    # has no governance requirements. Use these for testing.
    # ====================================================================

    def get_simple_market_count(self) -> int:
        """Get total number of markets from simple PredictionMarket"""
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                logger.warning("PredictionMarket contract not loaded")
                return 0
            return contract.functions.marketCount().call()
        except Exception as e:
            logger.error(f"Error getting market count: {e}")
            return 0

    def get_simple_market(self, market_id: int) -> Optional[Dict[str, Any]]:
        """Get market from simple PredictionMarket contract

        Market struct layout:
        0: string question
        1: address creator
        2: uint256 startTime
        3: uint256 endTime
        4: bool resolved
        5: uint256 winningSubmissionId
        6: uint256 totalVolume
        7: string actorTwitterHandle
        8: string targetTweetId
        9: bool xcomOnly
        10: uint256 platformFeeCollected
        """
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                logger.error("PredictionMarket contract not loaded")
                return None

            market = contract.functions.markets(market_id).call()
            return {
                'id': market_id,
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
            logger.error(f"Error getting simple market {market_id}: {e}")
            return None

    def get_simple_submission_count(self) -> int:
        """Get total number of submissions from simple PredictionMarket"""
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                return 0
            return contract.functions.submissionCount().call()
        except Exception as e:
            logger.error(f"Error getting submission count: {e}")
            return 0

    def get_simple_submission(self, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get submission from simple PredictionMarket contract

        Submission struct layout:
        0: uint256 marketId
        1: address creator
        2: string predictedText
        3: uint256 stake
        4: uint256 totalBets
        5: uint256 levenshteinDistance
        6: bool isWinner
        7: string screenshotIpfsHash
        8: bytes32 screenshotBase64Hash
        """
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                logger.error("PredictionMarket contract not loaded")
                return None

            sub = contract.functions.submissions(submission_id).call()
            return {
                'id': submission_id,
                'market_id': sub[0],
                'creator': sub[1],
                'predicted_text': sub[2],
                'stake': Web3.from_wei(sub[3], 'ether'),
                'total_bets': Web3.from_wei(sub[4], 'ether'),
                'levenshtein_distance': sub[5],
                'is_winner': sub[6],
                'screenshot_ipfs_hash': sub[7]
            }
        except Exception as e:
            logger.error(f"Error getting simple submission {submission_id}: {e}")
            return None

    def get_simple_market_submissions(self, market_id: int) -> List[int]:
        """Get list of submission IDs for a market"""
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                return []
            return contract.functions.getMarketSubmissions(market_id).call()
        except Exception as e:
            logger.error(f"Error getting market submissions: {e}")
            return []

    def get_simple_bet_count(self) -> int:
        """Get total number of bets from simple PredictionMarket"""
        try:
            contract = self.contracts.get('PredictionMarket')
            if not contract:
                return 0
            return contract.functions.betCount().call()
        except Exception as e:
            logger.error(f"Error getting bet count: {e}")
            return 0

    # ====================================================================
    # PREDICTION MARKET V2 METHODS (with full resolution mechanism)
    # ====================================================================
    # PredictionMarketV2 includes:
    # - On-chain Levenshtein distance for winner determination
    # - resolveMarket() for determining winners
    # - claimPayout() for winners
    # - Pull-based fee collection
    # ====================================================================

    def get_v2_market_count(self) -> int:
        """Get total number of markets from PredictionMarketV2"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                logger.warning("PredictionMarketV2 contract not loaded")
                return 0
            return contract.functions.marketCount().call()
        except Exception as e:
            logger.error(f"Error getting V2 market count: {e}")
            return 0

    def get_v2_market(self, market_id: int) -> Optional[Dict[str, Any]]:
        """Get market from PredictionMarketV2 contract

        Market struct layout (from getMarketDetails):
        - actorHandle: string
        - endTime: uint256
        - totalPool: uint256
        - resolved: bool
        - winningSubmissionId: uint256
        - creator: address
        - submissionIds: uint256[]
        """
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                logger.error("PredictionMarketV2 contract not loaded")
                return None

            # Use getMarketDetails for comprehensive data
            result = contract.functions.getMarketDetails(market_id).call()
            return {
                'id': market_id,
                'actor_handle': result[0],
                'end_time': result[1],
                'total_pool': Web3.from_wei(result[2], 'ether'),
                'resolved': result[3],
                'winning_submission_id': result[4],
                'creator': result[5],
                'submission_ids': list(result[6]),
                # Computed fields for backward compatibility
                'status': 'resolved' if result[3] else 'active'
            }
        except Exception as e:
            logger.error(f"Error getting V2 market {market_id}: {e}")
            return None

    def get_v2_submission_count(self) -> int:
        """Get total number of submissions from PredictionMarketV2"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                return 0
            return contract.functions.submissionCount().call()
        except Exception as e:
            logger.error(f"Error getting V2 submission count: {e}")
            return 0

    def get_v2_submission(self, submission_id: int) -> Optional[Dict[str, Any]]:
        """Get submission from PredictionMarketV2 contract

        Submission struct layout (from getSubmissionDetails):
        - marketId: uint256
        - submitter: address
        - predictedText: string
        - amount: uint256
        - claimed: bool
        """
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                logger.error("PredictionMarketV2 contract not loaded")
                return None

            result = contract.functions.getSubmissionDetails(submission_id).call()
            return {
                'id': submission_id,
                'market_id': result[0],
                'submitter': result[1],
                'predicted_text': result[2],
                'amount': Web3.from_wei(result[3], 'ether'),
                'claimed': result[4]
            }
        except Exception as e:
            logger.error(f"Error getting V2 submission {submission_id}: {e}")
            return None

    def get_v2_market_submissions(self, market_id: int) -> List[int]:
        """Get list of submission IDs for a V2 market"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                return []
            return list(contract.functions.getMarketSubmissions(market_id).call())
        except Exception as e:
            logger.error(f"Error getting V2 market submissions: {e}")
            return []

    def get_v2_user_submissions(self, user_address: str) -> List[int]:
        """Get list of submission IDs for a user from V2 contract"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                return []
            return list(contract.functions.getUserSubmissions(
                Web3.to_checksum_address(user_address)
            ).call())
        except Exception as e:
            logger.error(f"Error getting V2 user submissions: {e}")
            return []

    def get_v2_pending_fees(self, address: str) -> Decimal:
        """Get pending fees for an address from V2 contract"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                return Decimal(0)
            fees_wei = contract.functions.pendingFees(
                Web3.to_checksum_address(address)
            ).call()
            return Decimal(Web3.from_wei(fees_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error getting V2 pending fees: {e}")
            return Decimal(0)

    def get_v2_constants(self) -> Dict[str, Any]:
        """Get V2 contract constants"""
        try:
            contract = self.contracts.get('PredictionMarketV2')
            if not contract:
                return {}
            return {
                'platform_fee_bps': contract.functions.PLATFORM_FEE_BPS().call(),
                'min_bet': Web3.from_wei(contract.functions.MIN_BET().call(), 'ether'),
                'betting_cutoff': contract.functions.BETTING_CUTOFF().call(),
                'min_submissions': contract.functions.MIN_SUBMISSIONS().call(),
                'max_text_length': contract.functions.MAX_TEXT_LENGTH().call()
            }
        except Exception as e:
            logger.error(f"Error getting V2 constants: {e}")
            return {}

    # ====================================================================
    # ENHANCED PREDICTION MARKET METHODS (requires governance)
    # ====================================================================

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