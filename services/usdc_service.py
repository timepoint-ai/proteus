"""
USDC Service for BASE blockchain
Handles USDC transactions and balance queries
"""

import os
import json
from web3 import Web3
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

# USDC ABI (simplified - only essential functions)
USDC_ABI = json.loads('''[
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "recipient", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

class USDCService:
    """Service for interacting with USDC on BASE"""
    
    def __init__(self):
        # Initialize Web3
        rpc_url = os.environ.get('BASE_RPC_URL', 'https://sepolia.base.org')
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # USDC contract addresses
        self.usdc_addresses = {
            'base_mainnet': '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
            'base_sepolia': '0x036CbD53842c5426634e7929541eC2318f3dCF7e'  # Test USDC
        }
        
        # Detect network and select appropriate USDC address
        chain_id = self.w3.eth.chain_id
        if chain_id == 8453:  # BASE mainnet
            self.usdc_address = self.usdc_addresses['base_mainnet']
            self.network = 'base_mainnet'
        else:  # BASE Sepolia or other testnet
            self.usdc_address = self.usdc_addresses['base_sepolia']
            self.network = 'base_sepolia'
        
        # Initialize USDC contract
        self.usdc_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.usdc_address),
            abi=USDC_ABI
        )
        
        # USDC has 6 decimals
        self.decimals = 6
        
        logger.info(f"USDC Service initialized on {self.network} with address {self.usdc_address}")
    
    def get_balance(self, wallet_address: str) -> dict:
        """
        Get USDC balance for a wallet
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Balance information dict
        """
        try:
            # Convert address to checksum format
            address = Web3.to_checksum_address(wallet_address)
            
            # Get USDC balance
            balance_wei = self.usdc_contract.functions.balanceOf(address).call()
            
            # Convert to human-readable format (USDC has 6 decimals)
            balance_usdc = Decimal(balance_wei) / Decimal(10 ** self.decimals)
            
            # Get ETH balance for gas
            eth_balance_wei = self.w3.eth.get_balance(address)
            eth_balance = self.w3.from_wei(eth_balance_wei, 'ether')
            
            return {
                'success': True,
                'usdc_balance': float(balance_usdc),
                'usdc_balance_raw': balance_wei,
                'eth_balance': float(eth_balance),
                'eth_balance_wei': eth_balance_wei,
                'formatted': f"${balance_usdc:.2f} USDC"
            }
            
        except Exception as e:
            logger.error(f"Failed to get USDC balance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'usdc_balance': 0,
                'eth_balance': 0
            }
    
    def build_transfer_transaction(self, from_address: str, to_address: str, amount_usdc: float) -> dict:
        """
        Build a USDC transfer transaction
        
        Args:
            from_address: Sender address
            to_address: Recipient address
            amount_usdc: Amount of USDC to send
            
        Returns:
            Transaction dict ready for signing
        """
        try:
            # Convert addresses to checksum format
            from_addr = Web3.to_checksum_address(from_address)
            to_addr = Web3.to_checksum_address(to_address)
            
            # Convert amount to wei (6 decimals for USDC)
            amount_wei = int(Decimal(amount_usdc) * Decimal(10 ** self.decimals))
            
            # Build transaction
            transaction = self.usdc_contract.functions.transfer(
                to_addr,
                amount_wei
            ).build_transaction({
                'from': from_addr,
                'gas': 100000,  # USDC transfers typically use ~65k gas
                'gasPrice': self.w3.to_wei(1, 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(from_addr),
                'chainId': self.w3.eth.chain_id
            })
            
            return {
                'success': True,
                'transaction': transaction,
                'amount_usdc': amount_usdc,
                'amount_wei': amount_wei
            }
            
        except Exception as e:
            logger.error(f"Failed to build transfer transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def build_approve_transaction(self, owner_address: str, spender_address: str, amount_usdc: float) -> dict:
        """
        Build an approval transaction for spending USDC
        
        Args:
            owner_address: Token owner address
            spender_address: Address to approve for spending
            amount_usdc: Amount to approve
            
        Returns:
            Transaction dict ready for signing
        """
        try:
            # Convert addresses to checksum format
            owner_addr = Web3.to_checksum_address(owner_address)
            spender_addr = Web3.to_checksum_address(spender_address)
            
            # Convert amount to wei
            amount_wei = int(Decimal(amount_usdc) * Decimal(10 ** self.decimals))
            
            # Build transaction
            transaction = self.usdc_contract.functions.approve(
                spender_addr,
                amount_wei
            ).build_transaction({
                'from': owner_addr,
                'gas': 50000,  # Approve typically uses ~45k gas
                'gasPrice': self.w3.to_wei(1, 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(owner_addr),
                'chainId': self.w3.eth.chain_id
            })
            
            return {
                'success': True,
                'transaction': transaction,
                'amount_usdc': amount_usdc,
                'amount_wei': amount_wei
            }
            
        except Exception as e:
            logger.error(f"Failed to build approve transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_allowance(self, owner_address: str, spender_address: str) -> dict:
        """
        Check USDC spending allowance
        
        Args:
            owner_address: Token owner address
            spender_address: Spender address
            
        Returns:
            Allowance information
        """
        try:
            # Convert addresses to checksum format
            owner_addr = Web3.to_checksum_address(owner_address)
            spender_addr = Web3.to_checksum_address(spender_address)
            
            # Get allowance
            allowance_wei = self.usdc_contract.functions.allowance(
                owner_addr,
                spender_addr
            ).call()
            
            # Convert to human-readable format
            allowance_usdc = Decimal(allowance_wei) / Decimal(10 ** self.decimals)
            
            return {
                'success': True,
                'allowance_usdc': float(allowance_usdc),
                'allowance_wei': allowance_wei,
                'formatted': f"${allowance_usdc:.2f} USDC"
            }
            
        except Exception as e:
            logger.error(f"Failed to check allowance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'allowance_usdc': 0
            }
    
    def format_usdc_amount(self, amount: float) -> str:
        """Format USDC amount for display"""
        return f"${amount:.2f}"
    
    def wei_to_usdc(self, wei_amount: int) -> float:
        """Convert wei amount to USDC"""
        return float(Decimal(wei_amount) / Decimal(10 ** self.decimals))
    
    def usdc_to_wei(self, usdc_amount: float) -> int:
        """Convert USDC amount to wei"""
        return int(Decimal(usdc_amount) * Decimal(10 ** self.decimals))
    
    def estimate_gas_cost(self, gas_limit: int = 100000) -> dict:
        """
        Estimate gas cost for a transaction
        
        Args:
            gas_limit: Gas limit for the transaction
            
        Returns:
            Gas cost estimation
        """
        try:
            gas_price = self.w3.eth.gas_price
            gas_cost_wei = gas_limit * gas_price
            gas_cost_eth = self.w3.from_wei(gas_cost_wei, 'ether')
            
            # Estimate USD cost (assuming ETH price, this would need oracle in production)
            eth_price_usd = 2000  # Placeholder
            gas_cost_usd = float(gas_cost_eth) * eth_price_usd
            
            return {
                'success': True,
                'gas_limit': gas_limit,
                'gas_price_gwei': self.w3.from_wei(gas_price, 'gwei'),
                'gas_cost_eth': float(gas_cost_eth),
                'gas_cost_usd': gas_cost_usd,
                'formatted': f"~${gas_cost_usd:.4f}"
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate gas: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }