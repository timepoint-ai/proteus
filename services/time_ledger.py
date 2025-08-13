# from models import SyntheticTimeEntry, NodeOperator  # Phase 7: Models removed
# from app import db, redis_client  # Phase 7: Database removed
from config import Config
import logging
from datetime import datetime, timezone
import pytz
import time
import hashlib
import json

class TimeLedgerService:
    """Service for managing the Synthetic Time Ledger with millisecond precision"""
    
    @staticmethod
    def get_current_time():
        """Get current Pacific time without DST adjustments"""
        # Use Pacific Standard Time (no DST adjustments)
        pst = pytz.timezone('America/Los_Angeles')
        utc_now = datetime.now(timezone.utc)
        
        # Convert to PST (ignoring DST)
        pst_time = utc_now.astimezone(pst)
        
        # If it's PDT (daylight saving), subtract 1 hour to get PST
        if pst_time.dst():
            pst_time = pst_time.replace(tzinfo=None) - pst_time.dst()
            pst_time = pst.localize(pst_time)
        
        return pst_time.replace(tzinfo=None)
    
    @staticmethod
    def get_current_time_ms():
        """Get current time in milliseconds since epoch (Pacific Time)"""
        current_time = TimeLedgerService.get_current_time()
        return int(current_time.timestamp() * 1000)
    
    @staticmethod
    def record_entry(entry_type, entry_data, node_id=None):
        """Record an entry in the Synthetic Time Ledger"""
        try:
            if not node_id:
                node_id = Config.NODE_ID
            
            if not node_id:
                logging.error("No node ID available for time ledger entry")
                return False
            
            # Get current timestamp in milliseconds
            timestamp_ms = TimeLedgerService.get_current_time_ms()
            
            # Create hash chain entry
    # previous_entry = SyntheticTimeEntry.query.order_by(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms.desc()
    # ).first()  # Phase 7: Database removed
            
            # Create hash chain
            if previous_entry:
                previous_hash = previous_entry.hash_chain
            else:
                previous_hash = "0" * 64  # Genesis hash
            
            # Create current hash
            hash_data = {
                'timestamp_ms': timestamp_ms,
                'entry_type': entry_type,
                'entry_data': entry_data,
                'node_id': node_id,
                'previous_hash': previous_hash
            }
            
            hash_string = json.dumps(hash_data, sort_keys=True)
            current_hash = hashlib.sha256(hash_string.encode()).hexdigest()
            
            # Create entry
            entry = SyntheticTimeEntry(
                timestamp_ms=timestamp_ms,
                entry_type=entry_type,
                entry_data=entry_data,
                node_id=node_id,
                hash_chain=current_hash
            )
            
    # db.session.add(entry)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            # Cache in Redis for fast access
            redis_client.zadd(
                'time_ledger_entries',
                {entry.id: timestamp_ms}
            )
            
            logging.info(f"Time ledger entry recorded: {entry.id} at {timestamp_ms}")
            return True
            
        except Exception as e:
            logging.error(f"Error recording time ledger entry: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return False
    
    @staticmethod
    def get_entries_in_range(start_time_ms, end_time_ms, entry_type=None):
        """Get time ledger entries within a time range"""
        try:
    # query = SyntheticTimeEntry.query.filter(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms >= start_time_ms,
                SyntheticTimeEntry.timestamp_ms <= end_time_ms
            )
            
            if entry_type:
    # query = query.filter(SyntheticTimeEntry.entry_type == entry_type)  # Phase 7: Database removed
            
    # entries = query.order_by(SyntheticTimeEntry.timestamp_ms.asc()).all()  # Phase 7: Database removed
            
            return entries
            
        except Exception as e:
            logging.error(f"Error getting time ledger entries: {e}")
            return []
    
    @staticmethod
    def validate_time_chain():
        """Validate the integrity of the time chain"""
        try:
    # entries = SyntheticTimeEntry.query.order_by(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms.asc()
    # ).all()  # Phase 7: Database removed
            
            if not entries:
                return True
            
            previous_hash = "0" * 64
            
            for entry in entries:
                # Recreate hash
                hash_data = {
                    'timestamp_ms': entry.timestamp_ms,
                    'entry_type': entry.entry_type,
                    'entry_data': entry.entry_data,
                    'node_id': entry.node_id,
                    'previous_hash': previous_hash
                }
                
                hash_string = json.dumps(hash_data, sort_keys=True)
                expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
                
                if entry.hash_chain != expected_hash:
                    logging.error(f"Hash chain validation failed at entry: {entry.id}")
                    return False
                
                previous_hash = entry.hash_chain
            
            logging.info("Time chain validation successful")
            return True
            
        except Exception as e:
            logging.error(f"Error validating time chain: {e}")
            return False
    
    @staticmethod
    def sync_entry(entry_data, source_node_id):
        """Synchronize a time ledger entry from another node"""
        try:
            # Validate entry data
            required_fields = ['timestamp_ms', 'entry_type', 'entry_data', 'node_id', 'hash_chain']
            for field in required_fields:
                if field not in entry_data:
                    logging.error(f"Missing field in sync entry: {field}")
                    return False
            
            # Check if entry already exists
    # existing = SyntheticTimeEntry.query.filter_by(  # Phase 7: Database removed
                timestamp_ms=entry_data['timestamp_ms'],
                node_id=entry_data['node_id'],
                hash_chain=entry_data['hash_chain']
    # ).first()  # Phase 7: Database removed
            
            if existing:
                logging.debug(f"Entry already exists: {entry_data['hash_chain']}")
                return True
            
            # Validate hash chain
            if not TimeLedgerService._validate_entry_hash(entry_data):
                logging.error("Invalid hash chain in sync entry")
                return False
            
            # Create entry
            entry = SyntheticTimeEntry(
                timestamp_ms=entry_data['timestamp_ms'],
                entry_type=entry_data['entry_type'],
                entry_data=entry_data['entry_data'],
                node_id=entry_data['node_id'],
                hash_chain=entry_data['hash_chain']
            )
            
    # db.session.add(entry)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            logging.info(f"Synchronized time ledger entry from node: {source_node_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error synchronizing time ledger entry: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return False
    
    @staticmethod
    def _validate_entry_hash(entry_data):
        """Validate the hash of a time ledger entry"""
        try:
            # Find previous entry
    # previous_entry = SyntheticTimeEntry.query.filter(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms < entry_data['timestamp_ms']
    # ).order_by(SyntheticTimeEntry.timestamp_ms.desc()).first()  # Phase 7: Database removed
            
            if previous_entry:
                previous_hash = previous_entry.hash_chain
            else:
                previous_hash = "0" * 64
            
            # Recreate hash
            hash_data = {
                'timestamp_ms': entry_data['timestamp_ms'],
                'entry_type': entry_data['entry_type'],
                'entry_data': entry_data['entry_data'],
                'node_id': entry_data['node_id'],
                'previous_hash': previous_hash
            }
            
            hash_string = json.dumps(hash_data, sort_keys=True)
            expected_hash = hashlib.sha256(hash_string.encode()).hexdigest()
            
            return entry_data['hash_chain'] == expected_hash
            
        except Exception as e:
            logging.error(f"Error validating entry hash: {e}")
            return False
    
    @staticmethod
    def get_ledger_statistics():
        """Get time ledger statistics"""
        try:
    # total_entries = SyntheticTimeEntry.query.count()  # Phase 7: Database removed
            
            # Get entries by type
    # entry_types = db.session.query(  # Phase 7: Database removed
                SyntheticTimeEntry.entry_type,
                db.func.count(SyntheticTimeEntry.id)
    # ).group_by(SyntheticTimeEntry.entry_type).all()  # Phase 7: Database removed
            
            # Get entries by node
    # node_counts = db.session.query(  # Phase 7: Database removed
                SyntheticTimeEntry.node_id,
                db.func.count(SyntheticTimeEntry.id)
    # ).group_by(SyntheticTimeEntry.node_id).all()  # Phase 7: Database removed
            
            # Get latest timestamp
    # latest_entry = SyntheticTimeEntry.query.order_by(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms.desc()
    # ).first()  # Phase 7: Database removed
            
            return {
                'total_entries': total_entries,
                'entry_types': dict(entry_types),
                'node_counts': dict(node_counts),
                'latest_timestamp': latest_entry.timestamp_ms if latest_entry else None,
                'current_timestamp': TimeLedgerService.get_current_time_ms()
            }
            
        except Exception as e:
            logging.error(f"Error getting ledger statistics: {e}")
            return {}
    
    @staticmethod
    def cleanup_old_entries(days_to_keep=30):
        """Clean up old time ledger entries"""
        try:
            cutoff_time = TimeLedgerService.get_current_time_ms() - (days_to_keep * 24 * 60 * 60 * 1000)
            
            # Delete old entries
    # deleted_count = SyntheticTimeEntry.query.filter(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms < cutoff_time
            ).delete()
            
    # db.session.commit()  # Phase 7: Database removed
            
            logging.info(f"Cleaned up {deleted_count} old time ledger entries")
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error cleaning up old entries: {e}")
    # db.session.rollback()  # Phase 7: Database removed
            return 0
