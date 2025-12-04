"""
Coinbase Embedded Wallet Service
Handles wallet creation, authentication, and policy management
"""

import os
import json
import time
import hashlib
import secrets
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from web3 import Web3
try:
    import jwt
except ImportError:
    # Use a simple base64 encoding as fallback
    import base64
    import json as json_lib
    jwt = None
from eth_account import Account
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class EmbeddedWalletService:
    """
    Service for managing embedded wallets with TEE-secured storage
    Provides email/SMS authentication without seed phrases
    """
    
    def __init__(self):
        self.secret_key = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
        self.w3 = Web3(Web3.HTTPProvider(os.environ.get('BASE_RPC_URL', 'https://sepolia.base.org')))
        
        # Policy configuration
        self.default_policies = {
            'daily_limit_usd': 1000,
            'per_tx_limit_usd': 500,
            'require_2fa_above_usd': 500,
            'cooling_period_seconds': 3600,
            'allowed_contracts': self._get_allowed_contracts(),
            'blocked_addresses': []
        }
        
    def _get_allowed_contracts(self) -> list:
        """Get list of allowed contract addresses"""
        return [
            os.environ.get('PREDICTION_MARKET_ADDRESS', '0x6b67cb0daaf78f63bd11195df0fd9ffe4361b93c'),
            os.environ.get('GENESIS_NFT_ADDRESS', '0xE9eE183b76A8BDfDa8EA926b2f44137Aa65379B5'),
            os.environ.get('USDC_ADDRESS', '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')
        ]
    
    def create_wallet(self, identifier: str, auth_method: str = 'email') -> Dict:
        """
        Create a new embedded wallet for a user
        
        Args:
            identifier: Email or phone number
            auth_method: 'email', 'sms', or 'oauth'
            
        Returns:
            Wallet details including address and JWT token
        """
        try:
            # Generate deterministic seed from identifier (TEE-secured in production)
            seed = self._generate_seed(identifier)
            
            # Create account from seed
            account = Account.from_key(seed)
            
            # Store wallet metadata (in production, this would be in secure storage)
            wallet_data = {
                'address': account.address,
                'identifier': identifier,
                'auth_method': auth_method,
                'created_at': datetime.now(timezone.utc).isoformat(),
                'policies': self.default_policies
            }
            
            # Generate JWT for session
            token = self._generate_jwt(wallet_data)
            
            logger.info(f"Created embedded wallet for {identifier}: {account.address}")
            
            return {
                'success': True,
                'wallet_address': account.address,
                'token': token,
                'auth_method': auth_method
            }
            
        except Exception as e:
            logger.error(f"Failed to create wallet: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def authenticate_wallet(self, identifier: str, verification_code: Optional[str] = None) -> Dict:
        """
        Authenticate user and return wallet access
        
        Args:
            identifier: Email or phone number
            verification_code: OTP code for verification
            
        Returns:
            Authentication result with JWT token
        """
        try:
            # In production, verify OTP code here
            if verification_code and not self._verify_otp(identifier, verification_code):
                return {
                    'success': False,
                    'error': 'Invalid verification code'
                }
            
            # Generate seed and recover wallet
            seed = self._generate_seed(identifier)
            account = Account.from_key(seed)
            
            wallet_data = {
                'address': account.address,
                'identifier': identifier,
                'authenticated_at': datetime.now(timezone.utc).isoformat()
            }
            
            token = self._generate_jwt(wallet_data)
            
            return {
                'success': True,
                'wallet_address': account.address,
                'token': token
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_wallet_ownership(self, identifier: str, wallet_address: str) -> bool:
        """
        Verify that a user owns a specific wallet address
        
        Args:
            identifier: User's email or phone
            wallet_address: Wallet address to verify
            
        Returns:
            True if user owns the wallet
        """
        try:
            seed = self._generate_seed(identifier)
            account = Account.from_key(seed)
            return account.address.lower() == wallet_address.lower()
        except:
            return False
    
    def get_wallet_policy(self, wallet_address: str) -> Dict:
        """
        Get transaction policies for a wallet
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Policy configuration dict
        """
        # In production, fetch from secure storage
        return self.default_policies
    
    def update_wallet_policy(self, wallet_address: str, policy_updates: Dict) -> bool:
        """
        Update wallet policies
        
        Args:
            wallet_address: Wallet address
            policy_updates: Dict of policy updates
            
        Returns:
            Success status
        """
        try:
            # Validate policy updates
            for key, value in policy_updates.items():
                if key not in self.default_policies:
                    raise ValueError(f"Invalid policy key: {key}")
            
            # In production, update secure storage
            logger.info(f"Updated policies for {wallet_address}: {policy_updates}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update policies: {str(e)}")
            return False
    
    def check_transaction_compliance(self, wallet_address: str, tx_data: Dict) -> Dict:
        """
        Check if a transaction complies with wallet policies
        
        Args:
            wallet_address: Wallet address
            tx_data: Transaction data to check
            
        Returns:
            Compliance check result
        """
        try:
            policies = self.get_wallet_policy(wallet_address)
            
            # Check contract whitelist
            to_address = tx_data.get('to', '').lower()
            if to_address and to_address not in [addr.lower() for addr in policies['allowed_contracts']]:
                return {
                    'allowed': False,
                    'reason': 'Contract not whitelisted',
                    'requires_2fa': False
                }
            
            # Check amount limits (assuming value in USD)
            amount_usd = float(tx_data.get('value_usd', 0))
            
            if amount_usd > policies['per_tx_limit_usd']:
                return {
                    'allowed': False,
                    'reason': f"Transaction exceeds limit of ${policies['per_tx_limit_usd']}",
                    'requires_2fa': False
                }
            
            # Check if 2FA required
            requires_2fa = amount_usd >= policies['require_2fa_above_usd']
            
            return {
                'allowed': True,
                'reason': 'Transaction approved',
                'requires_2fa': requires_2fa
            }
            
        except Exception as e:
            logger.error(f"Compliance check failed: {str(e)}")
            return {
                'allowed': False,
                'reason': str(e),
                'requires_2fa': False
            }
    
    def sign_transaction(self, identifier: str, tx_data: Dict) -> Dict:
        """
        Sign a transaction with embedded wallet
        
        Args:
            identifier: User identifier
            tx_data: Transaction data
            
        Returns:
            Signed transaction
        """
        try:
            # Check compliance
            seed = self._generate_seed(identifier)
            account = Account.from_key(seed)
            
            compliance = self.check_transaction_compliance(account.address, tx_data)
            if not compliance['allowed']:
                return {
                    'success': False,
                    'error': compliance['reason']
                }
            
            # Build transaction
            transaction = {
                'from': account.address,
                'to': tx_data['to'],
                'value': tx_data.get('value', 0),
                'gas': tx_data.get('gas', 200000),
                'gasPrice': self.w3.to_wei(1, 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'chainId': 84532  # BASE Sepolia
            }
            
            if 'data' in tx_data:
                transaction['data'] = tx_data['data']
            
            # Sign transaction
            signed = account.sign_transaction(transaction)
            
            return {
                'success': True,
                'signed_tx': signed.rawTransaction.hex(),
                'tx_hash': signed.hash.hex()
            }
            
        except Exception as e:
            logger.error(f"Transaction signing failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_seed(self, identifier: str) -> bytes:
        """
        Generate deterministic seed from identifier
        In production, this would use TEE-secured key derivation
        """
        master_secret = os.environ.get('MASTER_WALLET_SECRET', 'default-secret-change-in-production')
        combined = f"{master_secret}:{identifier}"
        return hashlib.pbkdf2_hmac('sha256', combined.encode(), b'clockchain', 100000)
    
    def _generate_jwt(self, wallet_data: Dict) -> str:
        """Generate JWT token for wallet session"""
        payload = {
            **wallet_data,
            'exp': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            'iat': datetime.now(timezone.utc).isoformat()
        }
        
        if jwt:
            # Use PyJWT if available
            exp_timestamp = int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp())
            iat_timestamp = int(datetime.now(timezone.utc).timestamp())
            payload['exp'] = exp_timestamp
            payload['iat'] = iat_timestamp
            return jwt.encode(payload, self.secret_key, algorithm='HS256')
        else:
            # Fallback to simple base64 encoding
            import base64
            import json as json_lib
            token_data = json_lib.dumps(payload)
            return base64.b64encode(token_data.encode()).decode()
    
    def _verify_otp(self, identifier: str, code: str) -> bool:
        """
        Verify OTP code
        In production, this would check against sent OTP
        """
        # For testing, accept any 6-digit code
        return len(code) == 6 and code.isdigit()
    
    def get_wallet_balance(self, wallet_address: str) -> Dict:
        """
        Get wallet balance in USDC
        
        Args:
            wallet_address: Wallet address
            
        Returns:
            Balance information
        """
        try:
            # Get USDC contract
            usdc_address = os.environ.get('USDC_ADDRESS', '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913')
            
            # For now, return mock balance for testing
            # In production, query USDC contract
            balance_wei = self.w3.eth.get_balance(self.w3.to_checksum_address(wallet_address))
            
            return {
                'success': True,
                'balance_eth': float(self.w3.from_wei(balance_wei, 'ether')),
                'balance_usdc': 100.0,  # Mock for testing
                'balance_usd': 100.0
            }
            
        except Exception as e:
            logger.error(f"Failed to get balance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }