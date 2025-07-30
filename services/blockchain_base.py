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
            'PayoutManager': None
        }
        
        # Load ABIs
        self.abis = self._load_abis()
        
        # Platform fee percentage
        self.platform_fee_percentage = Decimal(os.environ.get('PLATFORM_FEE', '7')) / Decimal('100')
        
    def _load_abis(self) -> Dict[str, Any]:
        """Load contract ABIs from compiled artifacts"""
        abis = {}
        try:
            # Load from Hardhat artifacts
            artifacts_dir = 'artifacts/contracts/src'
            for contract_name in ['PredictionMarket', 'ClockchainOracle', 'NodeRegistry', 'PayoutManager']:
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
                for contract_name, address in deployment['contracts'].items():
                    if contract_name in self.abis:
                        self.contracts[contract_name] = self.w3.eth.contract(
                            address=Web3.toChecksumAddress(address),
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
            
    def create_market(self, question: str, duration: int, actor_handle: str, 
                     xcom_only: bool, initial_stake: Decimal, from_address: str) -> Dict[str, Any]:
        """Create a prediction market on-chain"""
        try:
            if not self.contracts['PredictionMarket']:
                raise ValueError("PredictionMarket contract not loaded")
                
            contract = self.contracts['PredictionMarket']
            
            # Calculate platform fee
            platform_fee = initial_stake * self.platform_fee_percentage
            total_value = initial_stake + platform_fee
            
            # Build transaction
            function = contract.functions.createMarket(
                question,
                duration,
                actor_handle,
                xcom_only
            )
            
            tx_params = {
                'from': from_address,
                'value': Web3.to_wei(total_value, 'ether'),
                'gas': function.estimate_gas({
                    'from': from_address,
                    'value': Web3.to_wei(total_value, 'ether')
                }),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params,
                'platform_fee': platform_fee,
                'total_value': total_value
            }
            
        except Exception as e:
            logger.error(f"Error creating market: {e}")
            raise
            
    def create_submission(self, market_id: int, predicted_text: str, 
                         screenshot_ipfs: str, stake: Decimal, from_address: str) -> Dict[str, Any]:
        """Create a submission for a market"""
        try:
            if not self.contracts['PredictionMarket']:
                raise ValueError("PredictionMarket contract not loaded")
                
            contract = self.contracts['PredictionMarket']
            
            # Build transaction
            function = contract.functions.createSubmission(
                market_id,
                predicted_text,
                screenshot_ipfs
            )
            
            tx_params = {
                'from': from_address,
                'value': Web3.to_wei(stake, 'ether'),
                'gas': function.estimate_gas({
                    'from': from_address,
                    'value': Web3.to_wei(stake, 'ether')
                }),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params,
                'stake': stake
            }
            
        except Exception as e:
            logger.error(f"Error creating submission: {e}")
            raise
            
    def place_bet(self, submission_id: int, amount: Decimal, from_address: str) -> Dict[str, Any]:
        """Place a bet on a submission"""
        try:
            if not self.contracts['PredictionMarket']:
                raise ValueError("PredictionMarket contract not loaded")
                
            contract = self.contracts['PredictionMarket']
            
            # Build transaction
            function = contract.functions.placeBet(submission_id)
            
            tx_params = {
                'from': from_address,
                'value': Web3.to_wei(amount, 'ether'),
                'gas': function.estimate_gas({
                    'from': from_address,
                    'value': Web3.to_wei(amount, 'ether')
                }),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params,
                'amount': amount
            }
            
        except Exception as e:
            logger.error(f"Error placing bet: {e}")
            raise
            
    def submit_oracle_data(self, market_id: int, actual_text: str, tweet_id: str,
                          screenshot_base64: str, from_address: str) -> Dict[str, Any]:
        """Submit oracle data for market resolution"""
        try:
            if not self.contracts['ClockchainOracle']:
                raise ValueError("ClockchainOracle contract not loaded")
                
            contract = self.contracts['ClockchainOracle']
            
            # Build transaction
            function = contract.functions.submitOracleData(
                market_id,
                actual_text,
                tweet_id,
                screenshot_base64
            )
            
            tx_params = {
                'from': from_address,
                'gas': function.estimate_gas({'from': from_address}),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params
            }
            
        except Exception as e:
            logger.error(f"Error submitting oracle data: {e}")
            raise
            
    def register_node(self, endpoint: str, stake: Decimal, from_address: str) -> Dict[str, Any]:
        """Register as a node operator"""
        try:
            if not self.contracts['NodeRegistry']:
                raise ValueError("NodeRegistry contract not loaded")
                
            contract = self.contracts['NodeRegistry']
            
            # Minimum stake is 100 BASE
            if stake < Decimal('100'):
                raise ValueError("Minimum stake is 100 BASE")
                
            # Build transaction
            function = contract.functions.registerNode(endpoint)
            
            tx_params = {
                'from': from_address,
                'value': Web3.to_wei(stake, 'ether'),
                'gas': function.estimate_gas({
                    'from': from_address,
                    'value': Web3.to_wei(stake, 'ether')
                }),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params,
                'stake': stake
            }
            
        except Exception as e:
            logger.error(f"Error registering node: {e}")
            raise
            
    def claim_payout(self, market_id: int, from_address: str) -> Dict[str, Any]:
        """Claim payout for a resolved market"""
        try:
            if not self.contracts['PayoutManager']:
                raise ValueError("PayoutManager contract not loaded")
                
            contract = self.contracts['PayoutManager']
            
            # Build transaction
            function = contract.functions.claimPayout(market_id)
            
            tx_params = {
                'from': from_address,
                'gas': function.estimate_gas({'from': from_address}),
                'gasPrice': self.estimate_gas_price()['standard']
            }
            
            return {
                'function': function,
                'params': tx_params
            }
            
        except Exception as e:
            logger.error(f"Error claiming payout: {e}")
            raise
            
    def send_transaction(self, function, params: Dict[str, Any], private_key: str) -> Optional[str]:
        """Send a transaction to the blockchain"""
        try:
            account = Account.from_key(private_key)
            params['nonce'] = self.w3.eth.get_transaction_count(account.address)
            
            # Build transaction
            transaction = function.build_transaction(params)
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"Error sending transaction: {e}")
            return None
            
    def wait_for_transaction(self, tx_hash: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Wait for transaction confirmation"""
        try:
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            if receipt['status'] == 1:
                logger.info(f"Transaction {tx_hash} confirmed in block {receipt['blockNumber']}")
                return {
                    'status': 'confirmed',
                    'block_number': receipt['blockNumber'],
                    'gas_used': receipt['gasUsed'],
                    'logs': receipt['logs']
                }
            else:
                logger.error(f"Transaction {tx_hash} failed")
                return {'status': 'failed'}
                
        except Exception as e:
            logger.error(f"Error waiting for transaction: {e}")
            return None
            
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