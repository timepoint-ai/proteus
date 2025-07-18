from celery import Celery
from app import app, celery, db
from models import Bet, Stake, Transaction, SyntheticTimeEntry, NodeOperator, Oracle
from services.reconciliation import ReconciliationService
from services.network import NetworkService
from services.time_ledger import TimeLedgerService
from services.oracle import OracleService
from services.blockchain import BlockchainService
from services.time_consensus import TimeConsensusService
from config import Config
import logging
from datetime import datetime, timedelta

# Background task definitions for Celery

@celery.task(bind=True)
def reconcile_network(self):
    """Periodic network reconciliation task"""
    try:
        with app.app_context():
            logging.info("Starting network reconciliation task")
            
            # Perform full reconciliation
            result = ReconciliationService.reconcile_full()
            
            if result.get('error'):
                logging.error(f"Network reconciliation failed: {result['error']}")
                raise Exception(result['error'])
            
            logging.info(f"Network reconciliation completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Error in network reconciliation task: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

@celery.task(bind=True)
def sync_time_ledger(self):
    """Periodic time ledger synchronization task"""
    try:
        with app.app_context():
            logging.info("Starting time ledger sync task")
            
            # Sync with network
            result = ReconciliationService.reconcile_time_ledger()
            
            if result.get('error'):
                logging.error(f"Time ledger sync failed: {result['error']}")
                raise Exception(result['error'])
            
            logging.info(f"Time ledger sync completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Error in time ledger sync task: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=5)

@celery.task(bind=True)
def process_pending_transactions(self):
    """Process pending blockchain transactions"""
    try:
        with app.app_context():
            logging.info("Starting pending transaction processing")
            
            # Get pending transactions
            pending_txs = Transaction.query.filter_by(status='pending').all()
            
            processed_count = 0
            
            for tx in pending_txs:
                try:
                    # Validate transaction on blockchain
                    is_valid = BlockchainService.validate_transaction(
                        tx.tx_hash,
                        tx.currency,
                        str(tx.amount)
                    )
                    
                    if is_valid:
                        tx.status = 'confirmed'
                        tx.confirmed_at = datetime.utcnow()
                        
                        # Get transaction details
                        details = BlockchainService.get_transaction_details(
                            tx.tx_hash,
                            tx.currency
                        )
                        
                        if details:
                            tx.block_number = details.get('block_number')
                            tx.confirmations = details.get('confirmations', 0)
                        
                        processed_count += 1
                        
                        # Record in time ledger
                        TimeLedgerService.record_entry('transaction_confirmed', {
                            'tx_hash': tx.tx_hash,
                            'amount': str(tx.amount),
                            'currency': tx.currency,
                            'confirmations': tx.confirmations
                        })
                        
                    else:
                        # Check if transaction is old enough to mark as failed
                        if tx.created_at < datetime.utcnow() - timedelta(hours=24):
                            tx.status = 'failed'
                            logging.warning(f"Transaction marked as failed: {tx.tx_hash}")
                    
                except Exception as e:
                    logging.error(f"Error processing transaction {tx.tx_hash}: {e}")
                    continue
            
            db.session.commit()
            
            logging.info(f"Processed {processed_count} pending transactions")
            return {'processed': processed_count, 'total_pending': len(pending_txs)}
            
    except Exception as e:
        logging.error(f"Error in pending transaction processing: {e}")
        raise self.retry(exc=e, countdown=120, max_retries=3)

@celery.task(bind=True)
def resolve_pending_bets(self):
    """Resolve bets that have passed their end time"""
    try:
        with app.app_context():
            logging.info("Starting pending bet resolution")
            
            # Get pending resolutions
            pending_bets = OracleService.get_pending_resolutions()
            
            resolved_count = 0
            
            for bet in pending_bets:
                try:
                    # Check if oracle statements exist
                    from models import OracleStatement
                    statements = OracleStatement.query.filter_by(
                        bet_id=bet.id,
                        approved=True
                    ).all()
                    
                    if statements:
                        # Use the first approved statement
                        statement = statements[0]
                        
                        # Resolve the bet
                        success = OracleService.resolve_bet(bet.id, statement.statement)
                        
                        if success:
                            resolved_count += 1
                            logging.info(f"Bet resolved: {bet.id}")
                        else:
                            logging.error(f"Failed to resolve bet: {bet.id}")
                    else:
                        logging.debug(f"No approved oracle statements for bet: {bet.id}")
                    
                except Exception as e:
                    logging.error(f"Error resolving bet {bet.id}: {e}")
                    continue
            
            logging.info(f"Resolved {resolved_count} pending bets")
            return {'resolved': resolved_count, 'total_pending': len(pending_bets)}
            
    except Exception as e:
        logging.error(f"Error in pending bet resolution: {e}")
        raise self.retry(exc=e, countdown=180, max_retries=3)

@celery.task(bind=True)
def update_oracle_reputations(self):
    """Update oracle reputation scores"""
    try:
        with app.app_context():
            logging.info("Starting oracle reputation update")
            
            # Get all oracles
            oracles = Oracle.query.filter_by(active=True).all()
            
            updated_count = 0
            
            for oracle in oracles:
                try:
                    # Calculate reputation
                    reputation = OracleService.get_oracle_reputation(oracle.id)
                    
                    if reputation != oracle.reputation_score:
                        oracle.reputation_score = reputation
                        updated_count += 1
                        
                        logging.debug(f"Updated reputation for oracle {oracle.id}: {reputation}")
                    
                except Exception as e:
                    logging.error(f"Error updating reputation for oracle {oracle.id}: {e}")
                    continue
            
            db.session.commit()
            
            logging.info(f"Updated {updated_count} oracle reputations")
            return {'updated': updated_count, 'total_oracles': len(oracles)}
            
    except Exception as e:
        logging.error(f"Error in oracle reputation update: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=3)

@celery.task(bind=True)
def cleanup_old_data(self):
    """Clean up old data to prevent database bloat"""
    try:
        with app.app_context():
            logging.info("Starting data cleanup")
            
            # Clean up old time ledger entries
            time_entries_cleaned = TimeLedgerService.cleanup_old_entries(days_to_keep=30)
            
            # Clean up old failed transactions
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            failed_txs_cleaned = Transaction.query.filter(
                Transaction.status == 'failed',
                Transaction.created_at < cutoff_date
            ).delete()
            
            # Clean up old resolved bets (keep for 90 days)
            bet_cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_bets_cleaned = Bet.query.filter(
                Bet.status == 'resolved',
                Bet.resolution_time < bet_cutoff_date
            ).delete()
            
            db.session.commit()
            
            result = {
                'time_entries_cleaned': time_entries_cleaned,
                'failed_transactions_cleaned': failed_txs_cleaned,
                'old_bets_cleaned': old_bets_cleaned
            }
            
            logging.info(f"Data cleanup completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Error in data cleanup: {e}")
        raise self.retry(exc=e, countdown=600, max_retries=2)

@celery.task(bind=True)
def monitor_network_health(self):
    """Monitor network health and node status"""
    try:
        with app.app_context():
            logging.info("Starting network health monitoring")
            
            # Get network status
            network_status = NetworkService.get_network_status()
            
            # Check for unhealthy nodes
            unhealthy_nodes = []
            cutoff_time = datetime.utcnow() - timedelta(minutes=10)
            
            nodes = NodeOperator.query.filter_by(status='active').all()
            
            for node in nodes:
                if not node.last_heartbeat or node.last_heartbeat < cutoff_time:
                    unhealthy_nodes.append(node.operator_id)
                    logging.warning(f"Node appears unhealthy: {node.operator_id}")
            
            # Try to sync with network
            sync_result = NetworkService.sync_with_network()
            
            result = {
                'network_status': network_status,
                'unhealthy_nodes': unhealthy_nodes,
                'sync_successful': sync_result,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            logging.info(f"Network health monitoring completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Error in network health monitoring: {e}")
        raise self.retry(exc=e, countdown=180, max_retries=3)

@celery.task(bind=True)
def validate_data_integrity(self):
    """Validate data integrity across the system"""
    try:
        with app.app_context():
            logging.info("Starting data integrity validation")
            
            # Validate time chain
            time_chain_valid = TimeLedgerService.validate_time_chain()
            
            # Validate transaction integrity
            transaction_integrity = ReconciliationService._validate_transaction_integrity()
            
            # Check for orphaned stakes
            orphaned_stakes = Stake.query.filter(
                ~Stake.bet_id.in_(db.session.query(Bet.id))
            ).count()
            
            # Check for inconsistent bet statuses
            inconsistent_bets = Bet.query.filter(
                Bet.status == 'resolved',
                Bet.resolution_time.is_(None)
            ).count()
            
            # Check for unpaid winning stakes
            unpaid_winning_stakes = Stake.query.join(Bet).filter(
                Bet.status == 'resolved',
                Bet.won == True,
                Stake.position == 'for',
                Stake.paid_out == False
            ).count()
            
            result = {
                'time_chain_valid': time_chain_valid,
                'transaction_integrity': transaction_integrity,
                'orphaned_stakes': orphaned_stakes,
                'inconsistent_bets': inconsistent_bets,
                'unpaid_winning_stakes': unpaid_winning_stakes,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            # Log any issues
            if not time_chain_valid:
                logging.error("Time chain validation failed!")
            if not transaction_integrity:
                logging.error("Transaction integrity validation failed!")
            if orphaned_stakes > 0:
                logging.warning(f"Found {orphaned_stakes} orphaned stakes")
            if inconsistent_bets > 0:
                logging.warning(f"Found {inconsistent_bets} inconsistent bets")
            if unpaid_winning_stakes > 0:
                logging.warning(f"Found {unpaid_winning_stakes} unpaid winning stakes")
            
            logging.info(f"Data integrity validation completed: {result}")
            return result
            
    except Exception as e:
        logging.error(f"Error in data integrity validation: {e}")
        raise self.retry(exc=e, countdown=300, max_retries=2)

@celery.task(bind=True)
def synchronize_time_consensus(self):
    """Synchronize time consensus across nodes"""
    try:
        with app.app_context():
            logging.info("Starting time consensus synchronization")
            
            time_consensus_service = TimeConsensusService()
            
            # Broadcast time sync to network
            time_consensus_service.broadcast_time_sync()
            
            # Get network time consensus
            consensus = time_consensus_service.get_network_time_consensus()
            
            if consensus['consensus']:
                logging.info(f"Time consensus achieved: {consensus['consensus_ratio']:.2%} nodes in sync")
                
                # Create time checkpoint if consensus is strong
                if consensus['consensus_ratio'] >= 0.8:
                    checkpoint_id = time_consensus_service.create_time_checkpoint()
                    if checkpoint_id:
                        logging.info(f"Created time checkpoint: {checkpoint_id}")
                        
            else:
                logging.warning(f"Time consensus not achieved: {consensus}")
                
            # Schedule next sync
            synchronize_time_consensus.apply_async(countdown=30)
            
            return {
                'consensus': consensus['consensus'],
                'consensus_ratio': consensus.get('consensus_ratio', 0),
                'nodes_in_sync': consensus.get('nodes_in_sync', 0),
                'average_time_diff': consensus.get('average_time_diff', 0)
            }
            
    except Exception as e:
        logging.error(f"Error in time consensus synchronization: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

# Periodic task scheduler
@celery.task
def schedule_periodic_tasks():
    """Schedule all periodic tasks"""
    
    # Network reconciliation every 5 minutes
    reconcile_network.apply_async(countdown=300)
    
    # Time ledger sync every 1 minute
    sync_time_ledger.apply_async(countdown=60)
    
    # Process pending transactions every 2 minutes
    process_pending_transactions.apply_async(countdown=120)
    
    # Resolve pending bets every 3 minutes
    resolve_pending_bets.apply_async(countdown=180)
    
    # Update oracle reputations every 15 minutes
    update_oracle_reputations.apply_async(countdown=900)
    
    # Clean up old data every hour
    cleanup_old_data.apply_async(countdown=3600)
    
    # Monitor network health every 3 minutes
    monitor_network_health.apply_async(countdown=180)
    
    # Validate data integrity every 30 minutes
    validate_data_integrity.apply_async(countdown=1800)
    
    # Synchronize time consensus every 30 seconds
    synchronize_time_consensus.apply_async(countdown=30)

# Initialize periodic tasks on startup
with app.app_context():
    schedule_periodic_tasks.apply_async(countdown=10)
