import logging
from web3 import Web3
from web3.exceptions import Web3Exception
import requests
from decimal import Decimal
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        self.eth_web3 = Web3(Web3.HTTPProvider(Config.ETH_RPC_URL))
        self.btc_api_url = Config.BTC_RPC_URL
        
    def validate_eth_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Validate an Ethereum transaction"""
        try:
            tx = self.eth_web3.eth.get_transaction(tx_hash)
            receipt = self.eth_web3.eth.get_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:  # Success
                return {
                    'hash': tx_hash,
                    'from': tx['from'],
                    'to': tx['to'],
                    'value': Web3.from_wei(tx['value'], 'ether'),
                    'block_number': receipt['blockNumber'],
                    'status': 'confirmed',
                    'gas_used': receipt['gasUsed']
                }
            else:
                logger.error(f"ETH transaction {tx_hash} failed")
                return None
                
        except Web3Exception as e:
            logger.error(f"Error validating ETH transaction {tx_hash}: {e}")
            return None
            
    def validate_btc_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Validate a Bitcoin transaction"""
        try:
            response = requests.get(f"{self.btc_api_url}/tx/{tx_hash}")
            response.raise_for_status()
            
            tx_data = response.json()
            
            if tx_data.get('status', {}).get('confirmed'):
                # Calculate total input and output values
                total_input = sum(vin['prevout']['value'] for vin in tx_data['vin'])
                total_output = sum(vout['value'] for vout in tx_data['vout'])
                
                return {
                    'hash': tx_hash,
                    'total_input': Decimal(total_input) / Decimal(100000000),  # Convert satoshis to BTC
                    'total_output': Decimal(total_output) / Decimal(100000000),
                    'block_height': tx_data['status']['block_height'],
                    'status': 'confirmed',
                    'fee': Decimal(total_input - total_output) / Decimal(100000000)
                }
            else:
                logger.info(f"BTC transaction {tx_hash} not yet confirmed")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error validating BTC transaction {tx_hash}: {e}")
            return None
            
    def get_eth_balance(self, address: str) -> Decimal:
        """Get ETH balance for an address"""
        try:
            balance_wei = self.eth_web3.eth.get_balance(address)
            return Decimal(Web3.from_wei(balance_wei, 'ether'))
        except Web3Exception as e:
            logger.error(f"Error getting ETH balance for {address}: {e}")
            return Decimal(0)
            
    def get_btc_balance(self, address: str) -> Decimal:
        """Get BTC balance for an address"""
        try:
            response = requests.get(f"{self.btc_api_url}/address/{address}")
            response.raise_for_status()
            
            address_data = response.json()
            balance_satoshis = address_data.get('chain_stats', {}).get('funded_txo_sum', 0)
            spent_satoshis = address_data.get('chain_stats', {}).get('spent_txo_sum', 0)
            
            return Decimal(balance_satoshis - spent_satoshis) / Decimal(100000000)
            
        except requests.RequestException as e:
            logger.error(f"Error getting BTC balance for {address}: {e}")
            return Decimal(0)
            
    def estimate_eth_gas_price(self) -> int:
        """Estimate current ETH gas price"""
        try:
            return self.eth_web3.eth.gas_price
        except Web3Exception as e:
            logger.error(f"Error estimating ETH gas price: {e}")
            return 20000000000  # 20 gwei fallback
            
    def send_eth_transaction(self, to_address: str, amount: Decimal, private_key: str) -> Optional[str]:
        """Send ETH transaction (for payouts)"""
        try:
            account = self.eth_web3.eth.account.from_key(private_key)
            nonce = self.eth_web3.eth.get_transaction_count(account.address)
            
            transaction = {
                'to': to_address,
                'value': Web3.to_wei(amount, 'ether'),
                'gas': 21000,
                'gasPrice': self.estimate_eth_gas_price(),
                'nonce': nonce,
            }
            
            signed_txn = self.eth_web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = self.eth_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            return tx_hash.hex()
            
        except Web3Exception as e:
            logger.error(f"Error sending ETH transaction: {e}")
            return None
            
    def calculate_platform_fee(self, amount: Decimal) -> Decimal:
        """Calculate platform fee (1%)"""
        return amount * Decimal(Config.PLATFORM_FEE_RATE)
