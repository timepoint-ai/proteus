"""
Wallet-only authentication service for BASE-only architecture
Phase 2: Replace all database and session-based authentication with wallet signatures
"""

import logging
from functools import wraps
from flask import request, jsonify
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime, timedelta
import os

# Try to import jwt, but make it optional for phase 2 testing
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    # Simple fallback for testing - in production, JWT is required
    class jwt:
        @staticmethod
        def encode(payload, secret, algorithm):
            import json
            import base64
            # Convert datetime objects to strings for JSON serialization
            for key, value in payload.items():
                if hasattr(value, 'isoformat'):
                    payload[key] = value.isoformat()
            # Simple base64 encoding for testing only
            return base64.b64encode(json.dumps(payload).encode()).decode()
        
        @staticmethod
        def decode(token, secret, algorithms):
            import json
            import base64
            return json.loads(base64.b64decode(token).decode())
        
        class ExpiredSignatureError(Exception):
            pass
        
        class InvalidTokenError(Exception):
            pass

logger = logging.getLogger(__name__)

class WalletAuthService:
    """Wallet-based authentication service using signature verification"""
    
    def __init__(self):
        self.web3 = Web3()
        # JWT secret for temporary session tokens (not stored in DB)
        self.jwt_secret = os.environ.get('JWT_SECRET', 'dev-secret-change-in-production')
        self.token_expiry_hours = 24
        
    def verify_signature(self, message: str, signature: str, address: str) -> bool:
        """Verify that a message was signed by the given address"""
        try:
            # Encode the message
            message_encoded = encode_defunct(text=message)
            
            # Recover the address from the signature
            recovered_address = self.web3.eth.account.recover_message(
                message_encoded, 
                signature=signature
            )
            
            # Compare addresses (case-insensitive)
            return recovered_address.lower() == address.lower()
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
            
    def generate_auth_message(self, address: str, nonce: str) -> str:
        """Generate a message for the user to sign"""
        return f"Sign this message to authenticate with Clockchain.\n\nWallet: {address}\nNonce: {nonce}\nTimestamp: {datetime.utcnow().isoformat()}"
        
    def create_jwt_token(self, address: str) -> str:
        """Create a JWT token for the authenticated wallet"""
        payload = {
            'address': address.lower(),
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
    def verify_jwt_token(self, token: str) -> dict:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            return None
            
    def authenticate_wallet(self, address: str, signature: str, message: str) -> dict:
        """Authenticate a wallet using signature verification"""
        try:
            # Verify the signature
            if not self.verify_signature(message, signature, address):
                return {
                    'success': False,
                    'error': 'Invalid signature'
                }
                
            # Generate JWT token
            token = self.create_jwt_token(address)
            
            return {
                'success': True,
                'token': token,
                'address': address.lower(),
                'expires_in': self.token_expiry_hours * 3600
            }
            
        except Exception as e:
            logger.error(f"Error authenticating wallet: {e}")
            return {
                'success': False,
                'error': 'Authentication failed'
            }

# Singleton instance
wallet_auth_service = WalletAuthService()

def require_wallet_auth(f):
    """Decorator to require wallet authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authentication token provided'}), 401
            
        token = auth_header.split(' ')[1]
        
        # Verify the token
        payload = wallet_auth_service.verify_jwt_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Add wallet address to request context
        request.wallet_address = payload['address']
        
        return f(*args, **kwargs)
        
    return decorated_function

def optional_wallet_auth(f):
    """Decorator for optional wallet authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for JWT token in Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            # Verify the token
            payload = wallet_auth_service.verify_jwt_token(token)
            
            if payload:
                # Add wallet address to request context
                request.wallet_address = payload['address']
            else:
                request.wallet_address = None
        else:
            request.wallet_address = None
            
        return f(*args, **kwargs)
        
    return decorated_function