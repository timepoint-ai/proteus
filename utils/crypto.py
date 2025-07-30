import logging
import hashlib
import hmac
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import InvalidSignature
from config import Config

logger = logging.getLogger(__name__)

class CryptoUtils:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self._load_keys()
    
    def _load_keys(self):
        """Load private and public keys from configuration"""
        try:
            # In a real implementation, these would be proper RSA keys
            # For demo purposes, we'll use the configured keys
            self.private_key_data = Config.NODE_PRIVATE_KEY
            self.public_key_data = Config.NODE_PUBLIC_KEY
            
            logger.info("Crypto keys loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading crypto keys: {e}")
            # Generate temporary keys for demo
            self._generate_temp_keys()
    
    def _generate_temp_keys(self):
        """Generate temporary RSA keys for demo purposes"""
        try:
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            self.private_key = private_key
            self.public_key = public_key
            self.private_key_data = private_pem.decode('utf-8')
            self.public_key_data = public_pem.decode('utf-8')
            
            logger.info("Generated temporary RSA keys")
            
        except Exception as e:
            logger.error(f"Error generating temporary keys: {e}")
            # Fallback to simple string keys
            self.private_key_data = "temp-private-key"
            self.public_key_data = "temp-public-key"
    
    def sign_message(self, message: str) -> str:
        """Sign a message with the private key"""
        try:
            # For demo purposes, use HMAC with private key as secret
            # In production, use proper RSA signing
            signature = hmac.new(
                self.private_key_data.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            return hashlib.sha256(message.encode('utf-8')).hexdigest()
    
    def verify_signature(self, message: str, signature: str, public_key: str) -> bool:
        """Verify a message signature"""
        try:
            # For demo purposes, use HMAC verification
            # In production, use proper RSA verification
            expected_signature = hmac.new(
                public_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def verify_message(self, message: str, signature: str) -> bool:
        """Verify a message signature using our own public key"""
        try:
            # For demo purposes, use HMAC verification with our private key
            # This simulates verifying a message we signed ourselves
            expected_signature = hmac.new(
                self.private_key_data.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying message: {e}")
            return False
    
    def hash_data(self, data: str) -> str:
        """Hash data using SHA-256"""
        try:
            return hashlib.sha256(data.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing data: {e}")
            return ""
    
    def generate_node_id(self) -> str:
        """Generate a unique node ID"""
        try:
            # Generate based on public key and timestamp
            import time
            data = f"{self.public_key_data}:{time.time()}"
            return self.hash_data(data)[:16]  # First 16 chars of hash
            
        except Exception as e:
            logger.error(f"Error generating node ID: {e}")
            return Config.NODE_OPERATOR_ID
    
    def encrypt_data(self, data: str, public_key: str = None) -> Optional[str]:
        """Encrypt data using public key"""
        try:
            # For demo purposes, use base64 encoding
            # In production, use proper RSA encryption
            if public_key is None:
                public_key = self.public_key_data
            
            # Simple base64 encoding for demo
            encrypted = base64.b64encode(data.encode('utf-8')).decode('utf-8')
            return encrypted
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str, private_key: str = None) -> Optional[str]:
        """Decrypt data using private key"""
        try:
            # For demo purposes, use base64 decoding
            # In production, use proper RSA decryption
            if private_key is None:
                private_key = self.private_key_data
            
            # Simple base64 decoding for demo
            decrypted = base64.b64decode(encrypted_data.encode('utf-8')).decode('utf-8')
            return decrypted
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def generate_random_bytes(self, length: int = 32) -> bytes:
        """Generate random bytes"""
        try:
            import os
            return os.urandom(length)
        except Exception as e:
            logger.error(f"Error generating random bytes: {e}")
            return b"0" * length
    
    def generate_random_string(self, length: int = 32) -> str:
        """Generate random string"""
        try:
            random_bytes = self.generate_random_bytes(length)
            return base64.b64encode(random_bytes).decode('utf-8')[:length]
        except Exception as e:
            logger.error(f"Error generating random string: {e}")
            return "0" * length
    
    def validate_signature_format(self, signature: str) -> bool:
        """Validate signature format"""
        try:
            # Check if signature is valid hex
            int(signature, 16)
            return len(signature) == 64  # SHA-256 hex length
        except ValueError:
            return False
    
    def validate_public_key_format(self, public_key: str) -> bool:
        """Validate public key format"""
        try:
            # For demo purposes, just check if it's a non-empty string
            return isinstance(public_key, str) and len(public_key) > 0
        except Exception as e:
            logger.error(f"Error validating public key format: {e}")
            return False
    
    def generate_wallet_address(self, public_key: str) -> str:
        """Generate wallet address from public key"""
        try:
            # For demo purposes, use hash of public key
            address_hash = self.hash_data(public_key)
            return f"0x{address_hash[:40]}"  # Ethereum-style address
        except Exception as e:
            logger.error(f"Error generating wallet address: {e}")
            return "0x0000000000000000000000000000000000000000"
    
    def validate_wallet_address(self, address: str) -> bool:
        """Validate wallet address format"""
        try:
            # Check Ethereum address format
            if address.startswith('0x') and len(address) == 42:
                # Check if hex
                int(address[2:], 16)
                return True
            
            # Check Bitcoin address format (simplified)
            if len(address) >= 26 and len(address) <= 35:
                return True
            
            return False
            
        except ValueError:
            return False
        except Exception as e:
            logger.error(f"Error validating wallet address: {e}")
            return False
    
    def create_merkle_root(self, data_list: list) -> str:
        """Create Merkle root from list of data"""
        try:
            if not data_list:
                return self.hash_data("")
            
            # Hash each data item
            hashes = [self.hash_data(str(item)) for item in data_list]
            
            # Build Merkle tree
            while len(hashes) > 1:
                next_level = []
                for i in range(0, len(hashes), 2):
                    if i + 1 < len(hashes):
                        combined = hashes[i] + hashes[i + 1]
                    else:
                        combined = hashes[i] + hashes[i]  # Duplicate last hash
                    next_level.append(self.hash_data(combined))
                hashes = next_level
            
            return hashes[0]
            
        except Exception as e:
            logger.error(f"Error creating Merkle root: {e}")
            return self.hash_data("error")
    
    def verify_merkle_proof(self, data: str, proof: list, root: str) -> bool:
        """Verify Merkle proof"""
        try:
            current_hash = self.hash_data(data)
            
            for proof_item in proof:
                if proof_item['position'] == 'left':
                    current_hash = self.hash_data(proof_item['hash'] + current_hash)
                else:
                    current_hash = self.hash_data(current_hash + proof_item['hash'])
            
            return current_hash == root
            
        except Exception as e:
            logger.error(f"Error verifying Merkle proof: {e}")
            return False
    
    def generate_transaction_id(self, transaction_data: Dict[str, Any]) -> str:
        """Generate unique transaction ID"""
        try:
            # Create deterministic transaction ID from transaction data
            data_string = "|".join([
                str(transaction_data.get('from', '')),
                str(transaction_data.get('to', '')),
                str(transaction_data.get('amount', '')),
                str(transaction_data.get('timestamp', '')),
                str(transaction_data.get('nonce', ''))
            ])
            
            return self.hash_data(data_string)
            
        except Exception as e:
            logger.error(f"Error generating transaction ID: {e}")
            return self.hash_data(str(transaction_data))
    
    def validate_transaction_signature(self, transaction: Dict[str, Any]) -> bool:
        """Validate transaction signature"""
        try:
            # Extract signature and public key
            signature = transaction.get('signature')
            public_key = transaction.get('public_key')
            
            if not signature or not public_key:
                return False
            
            # Create message from transaction data
            message_data = {k: v for k, v in transaction.items() if k not in ['signature', 'public_key']}
            message = "|".join([f"{k}:{v}" for k, v in sorted(message_data.items())])
            
            # Verify signature
            return self.verify_signature(message, signature, public_key)
            
        except Exception as e:
            logger.error(f"Error validating transaction signature: {e}")
            return False
    
    def get_public_key(self) -> str:
        """Get this node's public key"""
        return self.public_key_data
    
    def get_node_fingerprint(self) -> str:
        """Get this node's fingerprint"""
        return self.hash_data(self.public_key_data)[:16]
