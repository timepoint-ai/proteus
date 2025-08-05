"""
Security Audit Service (Phase 14)
Production readiness, security monitoring, and emergency controls
"""

import logging
import json
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from web3 import Web3
from eth_account import Account
from collections import defaultdict

logger = logging.getLogger(__name__)

class SecurityAuditService:
    """Service for security monitoring and emergency controls"""
    
    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
        self.w3 = blockchain_service.w3
        
        # Load contract
        self.contract = None
        self._load_contract()
        
        # Security monitoring
        self.alerts = []
        self.suspicious_activities = defaultdict(list)
        self.security_metrics = {
            'high_value_transactions': 0,
            'rate_limit_violations': 0,
            'blacklisted_users': 0,
            'emergency_activations': 0
        }
        
    def _load_contract(self):
        """Load SecurityAudit contract"""
        try:
            with open('deployments/base-sepolia.json', 'r') as f:
                deployments = json.load(f)
                
            if 'SecurityAudit' in deployments:
                address = deployments['SecurityAudit']['address']
                
                # Load ABI
                with open('artifacts/contracts/src/SecurityAudit.sol/SecurityAudit.json', 'r') as f:
                    artifact = json.load(f)
                    abi = artifact['abi']
                    
                self.contract = self.w3.eth.contract(
                    address=Web3.to_checksum_address(address),
                    abi=abi
                )
                logger.info("SecurityAudit contract loaded")
        except Exception as e:
            logger.warning(f"Could not load SecurityAudit contract: {e}")
            
    def check_transaction_security(
        self,
        user_address: str,
        value_wei: int
    ) -> Dict:
        """Check if transaction passes security checks"""
        if not self.contract:
            return {'allowed': True, 'reason': 'No security contract'}
            
        try:
            user_address = Web3.to_checksum_address(user_address)
            
            # Check on-chain security
            allowed = self.contract.functions.checkTransactionSecurity(
                user_address,
                value_wei
            ).call()
            
            # Local additional checks
            value_ether = self.w3.from_wei(value_wei, 'ether')
            
            # Check for suspicious patterns
            if self._detect_suspicious_pattern(user_address, value_ether):
                self.record_suspicious_activity(
                    user_address,
                    'suspicious_pattern',
                    {'value': value_ether}
                )
                return {
                    'allowed': False,
                    'reason': 'Suspicious activity pattern detected'
                }
                
            return {
                'allowed': allowed,
                'reason': 'Passed security checks' if allowed else 'Failed on-chain checks'
            }
            
        except Exception as e:
            logger.error(f"Error checking transaction security: {e}")
            return {'allowed': False, 'reason': str(e)}
            
    def _detect_suspicious_pattern(self, user_address: str, value: float) -> bool:
        """Detect suspicious activity patterns"""
        # Get recent activities
        recent = self.suspicious_activities[user_address]
        now = datetime.utcnow()
        
        # Check for rapid transactions
        recent_count = sum(
            1 for activity in recent
            if now - activity['timestamp'] < timedelta(minutes=5)
        )
        
        if recent_count > 10:
            return True
            
        # Check for unusual value patterns
        if value > 50:  # 50 BASE threshold
            recent_high_value = sum(
                1 for activity in recent
                if activity.get('value', 0) > 50 and
                now - activity['timestamp'] < timedelta(hours=1)
            )
            if recent_high_value > 3:
                return True
                
        return False
        
    def record_suspicious_activity(
        self,
        user_address: str,
        activity_type: str,
        details: Dict
    ):
        """Record suspicious activity"""
        activity = {
            'timestamp': datetime.utcnow(),
            'type': activity_type,
            'user': user_address,
            'details': details
        }
        
        self.suspicious_activities[user_address].append(activity)
        self.alerts.append(activity)
        
        # Keep only recent activities (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(days=1)
        self.suspicious_activities[user_address] = [
            a for a in self.suspicious_activities[user_address]
            if a['timestamp'] > cutoff
        ]
        
        logger.warning(f"Suspicious activity recorded: {activity}")
        
    def activate_emergency_mode(self, reason: str, private_key: str) -> Optional[Dict]:
        """Activate emergency mode"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Build transaction
            tx = self.contract.functions.activateEmergencyMode(
                reason
            ).build_transaction({
                'from': account.address,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.security_metrics['emergency_activations'] += 1
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'reason': reason,
                'activated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error activating emergency mode: {e}")
            return {'success': False, 'error': str(e)}
            
    def blacklist_user(
        self,
        user_address: str,
        reason: str,
        private_key: str
    ) -> Optional[Dict]:
        """Blacklist a user"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            user_address = Web3.to_checksum_address(user_address)
            
            # Build transaction
            tx = self.contract.functions.blacklistUser(
                user_address,
                reason
            ).build_transaction({
                'from': account.address,
                'gas': 150000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(account.address)
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            self.security_metrics['blacklisted_users'] += 1
            
            return {
                'success': True,
                'tx_hash': tx_hash.hex(),
                'user': user_address,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Error blacklisting user: {e}")
            return {'success': False, 'error': str(e)}
            
    def get_user_security_status(self, user_address: str) -> Dict:
        """Get comprehensive security status for a user"""
        if not self.contract:
            return {'status': 'unknown'}
            
        try:
            user_address = Web3.to_checksum_address(user_address)
            
            # Get on-chain status
            result = self.contract.functions.getUserSecurityStatus(
                user_address
            ).call()
            
            is_blacklisted, daily_withdrawn, tx_count, last_action = result
            
            # Get local suspicious activities
            suspicious = self.suspicious_activities.get(user_address, [])
            recent_suspicious = [
                a for a in suspicious
                if datetime.utcnow() - a['timestamp'] < timedelta(hours=24)
            ]
            
            return {
                'user': user_address,
                'blacklisted': is_blacklisted,
                'daily_withdrawn_wei': daily_withdrawn,
                'transaction_count': tx_count,
                'last_action_timestamp': last_action,
                'suspicious_activities': len(recent_suspicious),
                'risk_level': self._calculate_risk_level(
                    is_blacklisted,
                    tx_count,
                    len(recent_suspicious)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting user security status: {e}")
            return {'status': 'error', 'error': str(e)}
            
    def _calculate_risk_level(
        self,
        is_blacklisted: bool,
        tx_count: int,
        suspicious_count: int
    ) -> str:
        """Calculate user risk level"""
        if is_blacklisted:
            return 'BLOCKED'
        elif suspicious_count > 5 or tx_count > 40:
            return 'HIGH'
        elif suspicious_count > 2 or tx_count > 20:
            return 'MEDIUM'
        elif suspicious_count > 0 or tx_count > 10:
            return 'LOW'
        else:
            return 'NORMAL'
            
    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'alerts': self.alerts[-100:],  # Last 100 alerts
            'metrics': self.security_metrics,
            'high_risk_users': [],
            'contract_status': {}
        }
        
        # Get high risk users
        for user, activities in self.suspicious_activities.items():
            if len(activities) > 5:
                report['high_risk_users'].append({
                    'user': user,
                    'activity_count': len(activities),
                    'latest_activity': max(
                        a['timestamp'] for a in activities
                    ).isoformat()
                })
                
        # Get contract status if available
        if self.contract:
            try:
                report['contract_status'] = {
                    'emergency_mode': self.contract.functions.emergencyMode().call(),
                    'paused': self.contract.functions.paused().call(),
                    'max_transaction_value': self.contract.functions.maxTransactionValue().call(),
                    'daily_withdraw_limit': self.contract.functions.dailyWithdrawLimit().call()
                }
            except:
                pass
                
        return report
        
    def update_security_thresholds(
        self,
        threshold_type: str,
        new_value: int,
        private_key: str
    ) -> Optional[Dict]:
        """Update security thresholds"""
        if not self.contract:
            return None
            
        try:
            account = Account.from_key(private_key)
            
            # Select the appropriate function
            if threshold_type == 'max_transaction':
                func = self.contract.functions.updateMaxTransactionValue(new_value)
            elif threshold_type == 'daily_limit':
                func = self.contract.functions.updateDailyWithdrawLimit(new_value)
            elif threshold_type == 'suspicious_threshold':
                func = self.contract.functions.updateSuspiciousActivityThreshold(new_value)
            else:
                return {'success': False, 'error': 'Invalid threshold type'}
                
            # Build transaction
            tx = func.build_transaction({
                'from': account.address,
                'gas': 100000,
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
                'threshold_type': threshold_type,
                'new_value': new_value
            }
            
        except Exception as e:
            logger.error(f"Error updating security threshold: {e}")
            return {'success': False, 'error': str(e)}