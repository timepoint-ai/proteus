import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal, InvalidOperation
import json
# from models import Actor, Bet, NodeOperator  # Phase 7: Models removed
# from app import db  # Phase 7: Database removed
from config import Config

logger = logging.getLogger(__name__)

class ValidationUtils:
    def __init__(self):
        self.eth_address_pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        self.btc_address_pattern = re.compile(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-z0-9]{39,59}$')
        self.tx_hash_pattern = re.compile(r'^0x[a-fA-F0-9]{64}$')
        self.btc_tx_hash_pattern = re.compile(r'^[a-fA-F0-9]{64}$')
    
    def validate_wallet_address(self, address: str, currency: str = None) -> Dict[str, Any]:
        """Validate wallet address format"""
        try:
            if not address or not isinstance(address, str):
                return {
                    'valid': False,
                    'error': 'Address must be a non-empty string'
                }
            
            # ETH address validation
            if currency == 'ETH' or (currency is None and address.startswith('0x')):
                if self.eth_address_pattern.match(address):
                    return {'valid': True, 'currency': 'ETH'}
                else:
                    return {
                        'valid': False,
                        'error': 'Invalid Ethereum address format'
                    }
            
            # BTC address validation
            if currency == 'BTC' or (currency is None and not address.startswith('0x')):
                if self.btc_address_pattern.match(address):
                    return {'valid': True, 'currency': 'BTC'}
                else:
                    return {
                        'valid': False,
                        'error': 'Invalid Bitcoin address format'
                    }
            
            return {
                'valid': False,
                'error': 'Unknown address format'
            }
            
        except Exception as e:
            logger.error(f"Error validating wallet address: {e}")
            return {
                'valid': False,
                'error': f'Address validation error: {str(e)}'
            }
    
    def validate_transaction_hash(self, tx_hash: str, currency: str) -> Dict[str, Any]:
        """Validate transaction hash format"""
        try:
            if not tx_hash or not isinstance(tx_hash, str):
                return {
                    'valid': False,
                    'error': 'Transaction hash must be a non-empty string'
                }
            
            if currency == 'ETH':
                if self.tx_hash_pattern.match(tx_hash):
                    return {'valid': True}
                else:
                    return {
                        'valid': False,
                        'error': 'Invalid Ethereum transaction hash format'
                    }
            
            elif currency == 'BTC':
                if self.btc_tx_hash_pattern.match(tx_hash):
                    return {'valid': True}
                else:
                    return {
                        'valid': False,
                        'error': 'Invalid Bitcoin transaction hash format'
                    }
            
            else:
                return {
                    'valid': False,
                    'error': 'Unsupported currency'
                }
                
        except Exception as e:
            logger.error(f"Error validating transaction hash: {e}")
            return {
                'valid': False,
                'error': f'Transaction hash validation error: {str(e)}'
            }
    
    def validate_amount(self, amount: str, currency: str) -> Dict[str, Any]:
        """Validate amount format and range"""
        try:
            if not amount:
                return {
                    'valid': False,
                    'error': 'Amount is required'
                }
            
            # Convert to Decimal
            try:
                decimal_amount = Decimal(str(amount))
            except (InvalidOperation, ValueError):
                return {
                    'valid': False,
                    'error': 'Invalid amount format'
                }
            
            # Check if positive
            if decimal_amount <= 0:
                return {
                    'valid': False,
                    'error': 'Amount must be positive'
                }
            
            # Check currency-specific limits
            if currency == 'ETH':
                if decimal_amount > Decimal('1000'):  # 1000 ETH max
                    return {
                        'valid': False,
                        'error': 'Amount exceeds maximum limit (1000 ETH)'
                    }
                if decimal_amount < Decimal('0.001'):  # 0.001 ETH min
                    return {
                        'valid': False,
                        'error': 'Amount below minimum limit (0.001 ETH)'
                    }
            
            elif currency == 'BTC':
                if decimal_amount > Decimal('10'):  # 10 BTC max
                    return {
                        'valid': False,
                        'error': 'Amount exceeds maximum limit (10 BTC)'
                    }
                if decimal_amount < Decimal('0.00001'):  # 0.00001 BTC min
                    return {
                        'valid': False,
                        'error': 'Amount below minimum limit (0.00001 BTC)'
                    }
            
            return {
                'valid': True,
                'decimal_amount': decimal_amount
            }
            
        except Exception as e:
            logger.error(f"Error validating amount: {e}")
            return {
                'valid': False,
                'error': f'Amount validation error: {str(e)}'
            }
    
    def validate_datetime(self, datetime_str: str, field_name: str = 'datetime') -> Dict[str, Any]:
        """Validate datetime format"""
        try:
            if not datetime_str:
                return {
                    'valid': False,
                    'error': f'{field_name} is required'
                }
            
            # Try to parse ISO format
            try:
                parsed_datetime = datetime.fromisoformat(datetime_str)
            except ValueError:
                return {
                    'valid': False,
                    'error': f'Invalid {field_name} format. Use ISO format: YYYY-MM-DDTHH:MM:SS'
                }
            
            # Check if not in the past (with 1 minute tolerance)
            if field_name in ['start_time', 'end_time']:
                if parsed_datetime < datetime.utcnow() - timedelta(minutes=1):
                    return {
                        'valid': False,
                        'error': f'{field_name} cannot be in the past'
                    }
            
            return {
                'valid': True,
                'datetime': parsed_datetime
            }
            
        except Exception as e:
            logger.error(f"Error validating datetime: {e}")
            return {
                'valid': False,
                'error': f'Datetime validation error: {str(e)}'
            }
    
    def validate_time_range(self, start_time: str, end_time: str) -> Dict[str, Any]:
        """Validate time range"""
        try:
            # Validate individual times
            start_validation = self.validate_datetime(start_time, 'start_time')
            if not start_validation['valid']:
                return start_validation
            
            end_validation = self.validate_datetime(end_time, 'end_time')
            if not end_validation['valid']:
                return end_validation
            
            start_dt = start_validation['datetime']
            end_dt = end_validation['datetime']
            
            # Check if end time is after start time
            if end_dt <= start_dt:
                return {
                    'valid': False,
                    'error': 'End time must be after start time'
                }
            
            # Check if time range is reasonable (between 1 minute and 24 hours)
            time_diff = end_dt - start_dt
            if time_diff < timedelta(minutes=1):
                return {
                    'valid': False,
                    'error': 'Time range must be at least 1 minute'
                }
            
            if time_diff > timedelta(hours=24):
                return {
                    'valid': False,
                    'error': 'Time range cannot exceed 24 hours'
                }
            
            return {
                'valid': True,
                'start_time': start_dt,
                'end_time': end_dt,
                'duration': time_diff
            }
            
        except Exception as e:
            logger.error(f"Error validating time range: {e}")
            return {
                'valid': False,
                'error': f'Time range validation error: {str(e)}'
            }
    
    def validate_oracle_wallets(self, oracle_wallets: List[str]) -> Dict[str, Any]:
        """Validate oracle wallets list"""
        try:
            if not oracle_wallets:
                return {
                    'valid': False,
                    'error': 'At least one oracle wallet is required'
                }
            
            if not isinstance(oracle_wallets, list):
                return {
                    'valid': False,
                    'error': 'Oracle wallets must be a list'
                }
            
            if len(oracle_wallets) > 10:
                return {
                    'valid': False,
                    'error': 'Cannot have more than 10 oracle wallets'
                }
            
            # Validate each wallet address
            for i, wallet in enumerate(oracle_wallets):
                wallet_validation = self.validate_wallet_address(wallet)
                if not wallet_validation['valid']:
                    return {
                        'valid': False,
                        'error': f'Invalid oracle wallet {i+1}: {wallet_validation["error"]}'
                    }
            
            # Check for duplicates
            if len(oracle_wallets) != len(set(oracle_wallets)):
                return {
                    'valid': False,
                    'error': 'Duplicate oracle wallets are not allowed'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating oracle wallets: {e}")
            return {
                'valid': False,
                'error': f'Oracle wallets validation error: {str(e)}'
            }
    
    def validate_text_content(self, text: str, field_name: str = 'text') -> Dict[str, Any]:
        """Validate text content"""
        try:
            if not text:
                return {
                    'valid': False,
                    'error': f'{field_name} is required'
                }
            
            if not isinstance(text, str):
                return {
                    'valid': False,
                    'error': f'{field_name} must be a string'
                }
            
            # Check length
            if len(text.strip()) < 3:
                return {
                    'valid': False,
                    'error': f'{field_name} must be at least 3 characters long'
                }
            
            if len(text) > 1000:
                return {
                    'valid': False,
                    'error': f'{field_name} cannot exceed 1000 characters'
                }
            
            # Check for reasonable content (not just whitespace or special chars)
            if not re.search(r'[a-zA-Z0-9]', text):
                return {
                    'valid': False,
                    'error': f'{field_name} must contain alphanumeric characters'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating text content: {e}")
            return {
                'valid': False,
                'error': f'Text validation error: {str(e)}'
            }
    
    def validate_signature(self, signature: str) -> Dict[str, Any]:
        """Validate signature format"""
        try:
            if not signature:
                return {
                    'valid': False,
                    'error': 'Signature is required'
                }
            
            if not isinstance(signature, str):
                return {
                    'valid': False,
                    'error': 'Signature must be a string'
                }
            
            # Check if valid hex
            try:
                int(signature, 16)
            except ValueError:
                return {
                    'valid': False,
                    'error': 'Signature must be valid hexadecimal'
                }
            
            # Check length (SHA-256 signature)
            if len(signature) != 64:
                return {
                    'valid': False,
                    'error': 'Signature must be 64 characters long'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating signature: {e}")
            return {
                'valid': False,
                'error': f'Signature validation error: {str(e)}'
            }
    
    def validate_bet_creation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bet creation data"""
        try:
            required_fields = [
                'creator_wallet', 'actor_id', 'predicted_text', 'start_time',
                'end_time', 'oracle_wallets', 'initial_stake_amount', 'currency',
                'transaction_hash'
            ]
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate creator wallet
            wallet_validation = self.validate_wallet_address(data['creator_wallet'], data['currency'])
            if not wallet_validation['valid']:
                return {
                    'valid': False,
                    'error': f'Invalid creator wallet: {wallet_validation["error"]}'
                }
            
            # Validate actor exists
            actor = Actor.query.get(data['actor_id'])
            if not actor:
                return {
                    'valid': False,
                    'error': 'Actor not found'
                }
            
            if actor.status != 'approved':
                return {
                    'valid': False,
                    'error': 'Actor is not approved'
                }
            
            # Validate predicted text
            text_validation = self.validate_text_content(data['predicted_text'], 'predicted_text')
            if not text_validation['valid']:
                return text_validation
            
            # Validate time range
            time_validation = self.validate_time_range(data['start_time'], data['end_time'])
            if not time_validation['valid']:
                return time_validation
            
            # Validate oracle wallets
            oracle_validation = self.validate_oracle_wallets(data['oracle_wallets'])
            if not oracle_validation['valid']:
                return oracle_validation
            
            # Validate amount
            amount_validation = self.validate_amount(data['initial_stake_amount'], data['currency'])
            if not amount_validation['valid']:
                return amount_validation
            
            # Validate currency
            if data['currency'] not in ['ETH', 'BTC']:
                return {
                    'valid': False,
                    'error': 'Currency must be ETH or BTC'
                }
            
            # Validate transaction hash
            tx_validation = self.validate_transaction_hash(data['transaction_hash'], data['currency'])
            if not tx_validation['valid']:
                return tx_validation
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating bet creation: {e}")
            return {
                'valid': False,
                'error': f'Bet creation validation error: {str(e)}'
            }
    
    def validate_stake_placement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate stake placement data"""
        try:
            required_fields = [
                'staker_wallet', 'amount', 'currency', 'transaction_hash', 'position'
            ]
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate staker wallet
            wallet_validation = self.validate_wallet_address(data['staker_wallet'], data['currency'])
            if not wallet_validation['valid']:
                return {
                    'valid': False,
                    'error': f'Invalid staker wallet: {wallet_validation["error"]}'
                }
            
            # Validate amount
            amount_validation = self.validate_amount(data['amount'], data['currency'])
            if not amount_validation['valid']:
                return amount_validation
            
            # Validate currency
            if data['currency'] not in ['ETH', 'BTC']:
                return {
                    'valid': False,
                    'error': 'Currency must be ETH or BTC'
                }
            
            # Validate transaction hash
            tx_validation = self.validate_transaction_hash(data['transaction_hash'], data['currency'])
            if not tx_validation['valid']:
                return tx_validation
            
            # Validate position
            if data['position'] not in ['for', 'against']:
                return {
                    'valid': False,
                    'error': 'Position must be "for" or "against"'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating stake placement: {e}")
            return {
                'valid': False,
                'error': f'Stake placement validation error: {str(e)}'
            }
    
    def validate_oracle_submission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate oracle submission data"""
        try:
            required_fields = ['bet_id', 'oracle_wallet', 'submitted_text', 'signature']
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate bet exists
            bet = Bet.query.get(data['bet_id'])
            if not bet:
                return {
                    'valid': False,
                    'error': 'Bet not found'
                }
            
            # Validate oracle wallet
            wallet_validation = self.validate_wallet_address(data['oracle_wallet'])
            if not wallet_validation['valid']:
                return {
                    'valid': False,
                    'error': f'Invalid oracle wallet: {wallet_validation["error"]}'
                }
            
            # Validate submitted text
            text_validation = self.validate_text_content(data['submitted_text'], 'submitted_text')
            if not text_validation['valid']:
                return text_validation
            
            # Validate signature
            signature_validation = self.validate_signature(data['signature'])
            if not signature_validation['valid']:
                return signature_validation
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating oracle submission: {e}")
            return {
                'valid': False,
                'error': f'Oracle submission validation error: {str(e)}'
            }
    
    def validate_oracle_vote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate oracle vote data"""
        try:
            required_fields = ['submission_id', 'voter_wallet', 'vote', 'signature']
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate voter wallet
            wallet_validation = self.validate_wallet_address(data['voter_wallet'])
            if not wallet_validation['valid']:
                return {
                    'valid': False,
                    'error': f'Invalid voter wallet: {wallet_validation["error"]}'
                }
            
            # Validate vote
            if data['vote'] not in ['for', 'against']:
                return {
                    'valid': False,
                    'error': 'Vote must be "for" or "against"'
                }
            
            # Validate signature
            signature_validation = self.validate_signature(data['signature'])
            if not signature_validation['valid']:
                return signature_validation
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating oracle vote: {e}")
            return {
                'valid': False,
                'error': f'Oracle vote validation error: {str(e)}'
            }
    
    def validate_actor_proposal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate actor proposal data"""
        try:
            required_fields = ['name']
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate name
            if not data['name'] or len(data['name'].strip()) < 2:
                return {
                    'valid': False,
                    'error': 'Actor name must be at least 2 characters long'
                }
            
            if len(data['name']) > 100:
                return {
                    'valid': False,
                    'error': 'Actor name cannot exceed 100 characters'
                }
            
            # Validate description if provided
            if 'description' in data and data['description']:
                if len(data['description']) > 500:
                    return {
                        'valid': False,
                        'error': 'Actor description cannot exceed 500 characters'
                    }
            
            # Validate wallet address if provided
            if 'wallet_address' in data and data['wallet_address']:
                wallet_validation = self.validate_wallet_address(data['wallet_address'])
                if not wallet_validation['valid']:
                    return {
                        'valid': False,
                        'error': f'Invalid wallet address: {wallet_validation["error"]}'
                    }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating actor proposal: {e}")
            return {
                'valid': False,
                'error': f'Actor proposal validation error: {str(e)}'
            }
    
    def validate_actor_vote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate actor vote data"""
        try:
            required_fields = ['vote', 'signature']
            
            # Check required fields
            for field in required_fields:
                if field not in data:
                    return {
                        'valid': False,
                        'error': f'Missing required field: {field}'
                    }
            
            # Validate vote
            if data['vote'] not in ['approve', 'reject']:
                return {
                    'valid': False,
                    'error': 'Vote must be "approve" or "reject"'
                }
            
            # Validate signature
            signature_validation = self.validate_signature(data['signature'])
            if not signature_validation['valid']:
                return signature_validation
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating actor vote: {e}")
            return {
                'valid': False,
                'error': f'Actor vote validation error: {str(e)}'
            }
