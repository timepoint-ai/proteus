import logging
from datetime import datetime, timedelta, timezone
from app import celery, db
from services.ledger import LedgerService
from services.time_sync import TimeSyncService
from services.node_communication import NodeCommunicationService
from models import SyntheticTimeEntry, NetworkMetrics
from config import Config

logger = logging.getLogger(__name__)

@celery.task(bind=True)
def reconcile_time_entries(self, start_time_ms=None, end_time_ms=None):
    """
    Reconcile time entries between nodes
    """
    try:
        ledger_service = LedgerService()
        time_sync_service = TimeSyncService()
        
        # If no time range specified, use last reconciliation interval
        if start_time_ms is None or end_time_ms is None:
            end_time_ms = time_sync_service.get_pacific_time_ms()
            start_time_ms = end_time_ms - (Config.RECONCILIATION_INTERVAL * 1000)
        
        logger.info(f"Starting reconciliation for range {start_time_ms} - {end_time_ms}")
        
        # Perform reconciliation
        success = ledger_service.reconcile_time_entries(start_time_ms, end_time_ms)
        
        if success:
            logger.info("Reconciliation completed successfully")
            return {
                'status': 'success',
                'start_time_ms': start_time_ms,
                'end_time_ms': end_time_ms,
                'reconciled_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error("Reconciliation failed")
            return {
                'status': 'failed',
                'start_time_ms': start_time_ms,
                'end_time_ms': end_time_ms,
                'error': 'Reconciliation process failed'
            }
            
    except Exception as e:
        logger.error(f"Error in reconciliation task: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'start_time_ms': start_time_ms,
            'end_time_ms': end_time_ms
        }

@celery.task(bind=True)
def broadcast_reconciliation_request(self, start_time_ms, end_time_ms):
    """
    Broadcast reconciliation request to other nodes
    """
    try:
        node_comm_service = NodeCommunicationService()
        
        # Broadcast reconciliation request
        message = {
            'type': 'reconciliation_request',
            'start_time_ms': start_time_ms,
            'end_time_ms': end_time_ms,
            'requesting_node': Config.NODE_OPERATOR_ID
        }
        
        node_comm_service.broadcast_message(message)
        
        logger.info(f"Broadcast reconciliation request for range {start_time_ms} - {end_time_ms}")
        
        return {
            'status': 'success',
            'message': 'Reconciliation request broadcasted',
            'start_time_ms': start_time_ms,
            'end_time_ms': end_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting reconciliation request: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def periodic_reconciliation(self):
    """
    Periodic reconciliation task (runs every reconciliation interval)
    """
    try:
        time_sync_service = TimeSyncService()
        
        # Calculate time range for reconciliation
        current_time_ms = time_sync_service.get_pacific_time_ms()
        start_time_ms = current_time_ms - (Config.RECONCILIATION_INTERVAL * 1000)
        
        # Trigger reconciliation
        reconcile_result = reconcile_time_entries.delay(start_time_ms, current_time_ms)
        
        # Broadcast reconciliation request
        broadcast_result = broadcast_reconciliation_request.delay(start_time_ms, current_time_ms)
        
        logger.info(f"Periodic reconciliation triggered: {reconcile_result.id}")
        
        return {
            'status': 'success',
            'reconcile_task_id': reconcile_result.id,
            'broadcast_task_id': broadcast_result.id,
            'start_time_ms': start_time_ms,
            'end_time_ms': current_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error in periodic reconciliation: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def cleanup_old_entries(self, days_old=30):
    """
    Clean up old reconciled time entries
    """
    try:
        time_sync_service = TimeSyncService()
        
        # Calculate cutoff time
        cutoff_time_ms = time_sync_service.get_pacific_time_ms() - (days_old * 24 * 3600 * 1000)
        
        # Delete old reconciled entries
        deleted_count = db.session.query(SyntheticTimeEntry).filter(
            SyntheticTimeEntry.timestamp_ms < cutoff_time_ms,
            SyntheticTimeEntry.reconciled == True
        ).delete()
        
        db.session.commit()
        
        logger.info(f"Cleaned up {deleted_count} old time entries")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_time_ms': cutoff_time_ms
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old entries: {e}")
        db.session.rollback()
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def validate_time_entries(self, start_time_ms, end_time_ms):
    """
    Validate time entries for consistency
    """
    try:
        # Get all entries in time range
        entries = SyntheticTimeEntry.query.filter(
            SyntheticTimeEntry.timestamp_ms >= start_time_ms,
            SyntheticTimeEntry.timestamp_ms <= end_time_ms
        ).all()
        
        if not entries:
            return {
                'status': 'success',
                'total_entries': 0,
                'valid_entries': 0,
                'invalid_entries': 0,
                'validation_errors': []
            }
        
        valid_entries = 0
        invalid_entries = 0
        validation_errors = []
        
        for entry in entries:
            try:
                # Validate entry data format
                import json
                entry_data = json.loads(entry.entry_data)
                
                # Check if entry has required fields
                if 'timestamp' not in entry_data and entry.timestamp_ms:
                    # Entry is valid
                    valid_entries += 1
                else:
                    # Entry might be invalid
                    invalid_entries += 1
                    validation_errors.append({
                        'entry_id': str(entry.id),
                        'error': 'Missing required fields'
                    })
                    
            except json.JSONDecodeError:
                invalid_entries += 1
                validation_errors.append({
                    'entry_id': str(entry.id),
                    'error': 'Invalid JSON in entry_data'
                })
            except Exception as e:
                invalid_entries += 1
                validation_errors.append({
                    'entry_id': str(entry.id),
                    'error': str(e)
                })
        
        logger.info(f"Validation complete: {valid_entries} valid, {invalid_entries} invalid")
        
        return {
            'status': 'success',
            'total_entries': len(entries),
            'valid_entries': valid_entries,
            'invalid_entries': invalid_entries,
            'validation_errors': validation_errors
        }
        
    except Exception as e:
        logger.error(f"Error validating time entries: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def update_network_metrics(self):
    """
    Update network metrics
    """
    try:
        ledger_service = LedgerService()
        
        # Update metrics
        success = ledger_service.update_network_metrics()
        
        if success:
            logger.info("Network metrics updated successfully")
            return {
                'status': 'success',
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
        else:
            logger.error("Failed to update network metrics")
            return {
                'status': 'failed',
                'error': 'Update process failed'
            }
            
    except Exception as e:
        logger.error(f"Error updating network metrics: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

@celery.task(bind=True)
def generate_reconciliation_report(self, start_time_ms, end_time_ms):
    """
    Generate reconciliation report for a time period
    """
    try:
        time_sync_service = TimeSyncService()
        
        # Get entries in time range
        entries = SyntheticTimeEntry.query.filter(
            SyntheticTimeEntry.timestamp_ms >= start_time_ms,
            SyntheticTimeEntry.timestamp_ms <= end_time_ms
        ).all()
        
        # Group entries by node
        node_entries = {}
        for entry in entries:
            node_id = str(entry.node_id)
            if node_id not in node_entries:
                node_entries[node_id] = []
            node_entries[node_id].append(entry)
        
        # Calculate statistics
        total_entries = len(entries)
        reconciled_entries = sum(1 for e in entries if e.reconciled)
        unreconciled_entries = total_entries - reconciled_entries
        
        # Group by entry type
        entry_types = {}
        for entry in entries:
            entry_type = entry.entry_type
            if entry_type not in entry_types:
                entry_types[entry_type] = 0
            entry_types[entry_type] += 1
        
        # Generate report
        report = {
            'status': 'success',
            'report_generated_at': datetime.now(timezone.utc).isoformat(),
            'time_range': {
                'start_time_ms': start_time_ms,
                'end_time_ms': end_time_ms,
                'start_time': time_sync_service.ms_to_pacific_time(start_time_ms).isoformat(),
                'end_time': time_sync_service.ms_to_pacific_time(end_time_ms).isoformat()
            },
            'summary': {
                'total_entries': total_entries,
                'reconciled_entries': reconciled_entries,
                'unreconciled_entries': unreconciled_entries,
                'reconciliation_rate': reconciled_entries / max(total_entries, 1),
                'participating_nodes': len(node_entries)
            },
            'entry_types': entry_types,
            'node_participation': {
                node_id: len(node_entries[node_id]) for node_id in node_entries
            }
        }
        
        logger.info(f"Reconciliation report generated for {total_entries} entries")
        
        return report
        
    except Exception as e:
        logger.error(f"Error generating reconciliation report: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

# Setup periodic tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic reconciliation tasks"""
    
    # Periodic reconciliation every reconciliation interval
    sender.add_periodic_task(
        Config.RECONCILIATION_INTERVAL,
        periodic_reconciliation.s(),
        name='periodic_reconciliation'
    )
    
    # Update network metrics every minute
    sender.add_periodic_task(
        60.0,
        update_network_metrics.s(),
        name='update_network_metrics'
    )
    
    # Clean up old entries daily
    sender.add_periodic_task(
        24 * 3600,  # 24 hours
        cleanup_old_entries.s(),
        name='cleanup_old_entries'
    )
