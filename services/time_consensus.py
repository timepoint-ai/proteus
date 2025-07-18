import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app import db, redis_client
from models import NodeOperator, SyntheticTimeEntry
from utils.crypto import CryptoUtils
from config import Config
import json
import time
import pytz

logger = logging.getLogger(__name__)

class TimeConsensusService:
    """Service for maintaining time consensus across distributed nodes"""
    
    def __init__(self):
        self.crypto_utils = CryptoUtils()
        self.node_id = Config.NODE_OPERATOR_ID
        self.pacific_tz = pytz.timezone(Config.PACIFIC_TIMEZONE)
        # Time tolerance for consensus (in seconds)
        self.time_tolerance = 30
        
    def get_synchronized_time(self) -> datetime:
        """Get synchronized UTC time across nodes"""
        try:
            # For now, use system time but in production would use NTP
            return datetime.utcnow()
        except Exception as e:
            logger.error(f"Error getting synchronized time: {e}")
            return datetime.utcnow()
            
    def get_pacific_time(self) -> datetime:
        """Get current Pacific Time"""
        try:
            utc_time = self.get_synchronized_time()
            return utc_time.replace(tzinfo=pytz.UTC).astimezone(self.pacific_tz)
        except Exception as e:
            logger.error(f"Error converting to Pacific time: {e}")
            return datetime.now(self.pacific_tz)
            
    def validate_time_window(self, start_time: datetime, end_time: datetime, current_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Validate that a time window is valid and has passed"""
        try:
            if not current_time:
                current_time = self.get_synchronized_time()
                
            # Ensure times are timezone-aware
            if not start_time.tzinfo:
                start_time = start_time.replace(tzinfo=pytz.UTC)
            if not end_time.tzinfo:
                end_time = end_time.replace(tzinfo=pytz.UTC)
            if not current_time.tzinfo:
                current_time = current_time.replace(tzinfo=pytz.UTC)
                
            # Validate time window
            if start_time >= end_time:
                return {
                    'valid': False,
                    'error': 'Start time must be before end time'
                }
                
            # Check if window has started
            has_started = current_time >= start_time
            
            # Check if window has ended
            has_ended = current_time >= end_time
            
            # Calculate time until end
            time_until_end = (end_time - current_time).total_seconds() if not has_ended else 0
            
            return {
                'valid': True,
                'has_started': has_started,
                'has_ended': has_ended,
                'time_until_end': time_until_end,
                'current_time': current_time.isoformat(),
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating time window: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
            
    def can_submit_oracle(self, bet_end_time: datetime) -> bool:
        """Check if oracle submission is allowed for a bet"""
        try:
            current_time = self.get_synchronized_time()
            
            # Ensure timezone awareness
            if not bet_end_time.tzinfo:
                bet_end_time = bet_end_time.replace(tzinfo=pytz.UTC)
            if not current_time.tzinfo:
                current_time = current_time.replace(tzinfo=pytz.UTC)
                
            # Oracle submissions only allowed after end time
            return current_time >= bet_end_time
            
        except Exception as e:
            logger.error(f"Error checking oracle submission eligibility: {e}")
            return False
            
    def broadcast_time_sync(self) -> bool:
        """Broadcast time sync message to network"""
        try:
            current_time = self.get_synchronized_time()
            
            # Create time sync message
            sync_message = {
                'type': 'time_sync',
                'node_id': self.node_id,
                'timestamp': current_time.isoformat(),
                'timestamp_ms': int(current_time.timestamp() * 1000),
                'pacific_time': self.get_pacific_time().isoformat()
            }
            
            # Sign message
            message_data = json.dumps(sync_message, sort_keys=True)
            signature = self.crypto_utils.sign_message(message_data)
            sync_message['signature'] = signature
            
            # Store in Redis for other nodes
            redis_key = f"time_sync:{self.node_id}"
            redis_client.setex(redis_key, 60, json.dumps(sync_message))
            
            logger.debug(f"Broadcast time sync: {current_time.isoformat()}")
            return True
            
        except Exception as e:
            logger.error(f"Error broadcasting time sync: {e}")
            return False
            
    def get_network_time_consensus(self) -> Dict[str, Any]:
        """Get time consensus from all active nodes"""
        try:
            # Get all active nodes
            active_nodes = NodeOperator.query.filter_by(status='active').all()
            
            time_reports = []
            current_time = self.get_synchronized_time()
            
            # Collect time reports from all nodes
            for node in active_nodes:
                redis_key = f"time_sync:{node.operator_id}"
                sync_data = redis_client.get(redis_key)
                
                if sync_data:
                    try:
                        sync_info = json.loads(sync_data)
                        # Verify signature
                        signature = sync_info.pop('signature', None)
                        message_data = json.dumps(sync_info, sort_keys=True)
                        
                        if signature and self.crypto_utils.verify_signature(message_data, signature, node.public_key):
                            reported_time = datetime.fromisoformat(sync_info['timestamp'])
                            time_diff = abs((current_time - reported_time).total_seconds())
                            
                            time_reports.append({
                                'node_id': node.operator_id,
                                'reported_time': reported_time,
                                'time_diff': time_diff,
                                'within_tolerance': time_diff <= self.time_tolerance
                            })
                    except Exception as e:
                        logger.error(f"Error processing time sync from {node.operator_id}: {e}")
                        
            # Calculate consensus
            if not time_reports:
                return {
                    'consensus': False,
                    'reason': 'No time reports available',
                    'current_time': current_time.isoformat()
                }
                
            # Check if majority of nodes are within tolerance
            nodes_in_sync = sum(1 for r in time_reports if r['within_tolerance'])
            consensus_ratio = nodes_in_sync / len(time_reports)
            
            # Calculate average time difference
            avg_time_diff = sum(r['time_diff'] for r in time_reports) / len(time_reports)
            
            return {
                'consensus': consensus_ratio >= Config.CONSENSUS_THRESHOLD,
                'consensus_ratio': consensus_ratio,
                'nodes_reporting': len(time_reports),
                'nodes_in_sync': nodes_in_sync,
                'average_time_diff': avg_time_diff,
                'time_tolerance': self.time_tolerance,
                'current_time': current_time.isoformat(),
                'time_reports': time_reports
            }
            
        except Exception as e:
            logger.error(f"Error getting network time consensus: {e}")
            return {
                'consensus': False,
                'error': str(e)
            }
            
    def validate_historical_time(self, claimed_time: datetime, event_type: str) -> bool:
        """Validate that a claimed historical time is reasonable"""
        try:
            current_time = self.get_synchronized_time()
            
            # Ensure timezone awareness
            if not claimed_time.tzinfo:
                claimed_time = claimed_time.replace(tzinfo=pytz.UTC)
            if not current_time.tzinfo:
                current_time = current_time.replace(tzinfo=pytz.UTC)
                
            # Cannot claim future times
            if claimed_time > current_time:
                logger.warning(f"Rejected future time claim for {event_type}: {claimed_time}")
                return False
                
            # Check if time is too far in the past (e.g., more than 24 hours)
            max_past_delta = timedelta(hours=24)
            if current_time - claimed_time > max_past_delta:
                logger.warning(f"Rejected old time claim for {event_type}: {claimed_time}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating historical time: {e}")
            return False
            
    def create_time_checkpoint(self) -> Optional[str]:
        """Create a time checkpoint in the ledger"""
        try:
            current_time = self.get_synchronized_time()
            pacific_time = self.get_pacific_time()
            
            # Get network consensus
            consensus = self.get_network_time_consensus()
            
            if not consensus['consensus']:
                logger.warning("Cannot create time checkpoint without consensus")
                return None
                
            # Create checkpoint entry
            checkpoint_data = {
                'utc_time': current_time.isoformat(),
                'pacific_time': pacific_time.isoformat(),
                'timestamp_ms': int(current_time.timestamp() * 1000),
                'consensus_ratio': consensus['consensus_ratio'],
                'nodes_in_sync': consensus['nodes_in_sync']
            }
            
            # Create synthetic time entry
            checkpoint_entry = SyntheticTimeEntry(
                timestamp_ms=int(current_time.timestamp() * 1000),
                entry_type='time_checkpoint',
                entry_data=json.dumps(checkpoint_data),
                node_id=self.node_id,
                signature=self.crypto_utils.sign_message(json.dumps(checkpoint_data)),
                reconciled=True  # Checkpoints are immediately reconciled
            )
            
            db.session.add(checkpoint_entry)
            db.session.commit()
            
            logger.info(f"Created time checkpoint: {checkpoint_entry.id}")
            return str(checkpoint_entry.id)
            
        except Exception as e:
            logger.error(f"Error creating time checkpoint: {e}")
            db.session.rollback()
            return None