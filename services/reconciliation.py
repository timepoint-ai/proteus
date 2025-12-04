# from models import Transaction, SyntheticTimeEntry, NodeOperator, Bet, Stake  # Phase 7: Models removed
from services.blockchain import BlockchainService
from services.time_ledger import TimeLedgerService
from services.network import NetworkService
# from app import db, redis_client  # Phase 7: Database removed
from config import Config
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import hashlib

class ReconciliationService:
    """Service for reconciling distributed ledger data across nodes"""
    
    @staticmethod
    def reconcile_full(node_id=None):
        """Perform full reconciliation of all data"""
        try:
            if not node_id:
                node_id = Config.NODE_ID
            
            logging.info(f"Starting full reconciliation for node: {node_id}")
            
            # Reconcile in order of importance
            time_result = ReconciliationService.reconcile_time_ledger(node_id)
            tx_result = ReconciliationService.reconcile_transactions(node_id)
            bet_result = ReconciliationService.reconcile_bets(node_id)
            
            # Update last reconciliation time
            redis_client.set(f'node:{node_id}:last_reconcile', datetime.now(timezone.utc).isoformat())
            
            result = {
                'time_ledger': time_result,
                'transactions': tx_result,
                'bets': bet_result,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            logging.info(f"Full reconciliation completed for node: {node_id}")
            return result
            
        except Exception as e:
            logging.error(f"Error in full reconciliation: {e}")
            return {'error': str(e)}
    
    @staticmethod
    def reconcile_time_ledger(node_id=None):
        """Reconcile synthetic time ledger entries"""
        try:
            if not node_id:
                node_id = Config.NODE_ID
            
            logging.info(f"Starting time ledger reconciliation for node: {node_id}")
            
            # Get network nodes
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                logging.warning("No network nodes configured")
                return {'status': 'no_network'}
            
            # Get our latest entry
    # latest_local = SyntheticTimeEntry.query.order_by(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms.desc()
    # ).first()  # Phase 7: Database removed
            
            since_timestamp = latest_local.timestamp_ms if latest_local else 0
            
            reconciled_entries = 0
            conflicts = []
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
                        # Get entries from other node
                        entries = ReconciliationService._fetch_time_entries_from_node(
                            node_url, since_timestamp
                        )
                        
                        # Process each entry
                        for entry_data in entries:
                            result = ReconciliationService._reconcile_time_entry(
                                entry_data, node_url
                            )
                            
                            if result['status'] == 'reconciled':
                                reconciled_entries += 1
                            elif result['status'] == 'conflict':
                                conflicts.append(result)
                                
                    except Exception as e:
                        logging.error(f"Error reconciling with node {node_url}: {e}")
            
            # Validate time chain integrity
            chain_valid = TimeLedgerService.validate_time_chain()
            
            result = {
                'status': 'completed',
                'reconciled_entries': reconciled_entries,
                'conflicts': len(conflicts),
                'chain_valid': chain_valid,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            logging.info(f"Time ledger reconciliation completed: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error reconciling time ledger: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def reconcile_transactions(node_id=None):
        """Reconcile transaction data across nodes"""
        try:
            if not node_id:
                node_id = Config.NODE_ID
            
            logging.info(f"Starting transaction reconciliation for node: {node_id}")
            
            # Get network nodes
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                return {'status': 'no_network'}
            
            # Get our latest transaction
    # latest_local = Transaction.query.order_by(  # Phase 7: Database removed
                Transaction.created_at.desc()
    # ).first()  # Phase 7: Database removed
            
            since_time = latest_local.created_at if latest_local else datetime.now(timezone.utc) - timedelta(days=1)
            
            reconciled_transactions = 0
            conflicts = []
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
                        # Get transactions from other node
                        transactions = ReconciliationService._fetch_transactions_from_node(
                            node_url, since_time
                        )
                        
                        # Process each transaction
                        for tx_data in transactions:
                            result = ReconciliationService._reconcile_transaction(
                                tx_data, node_url
                            )
                            
                            if result['status'] == 'reconciled':
                                reconciled_transactions += 1
                            elif result['status'] == 'conflict':
                                conflicts.append(result)
                                
                    except Exception as e:
                        logging.error(f"Error reconciling transactions with node {node_url}: {e}")
            
            # Validate transaction integrity
            integrity_result = ReconciliationService._validate_transaction_integrity()
            
            result = {
                'status': 'completed',
                'reconciled_transactions': reconciled_transactions,
                'conflicts': len(conflicts),
                'integrity_valid': integrity_result,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            logging.info(f"Transaction reconciliation completed: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error reconciling transactions: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def reconcile_bets(node_id=None):
        """Reconcile betting data across nodes"""
        try:
            if not node_id:
                node_id = Config.NODE_ID
            
            logging.info(f"Starting bet reconciliation for node: {node_id}")
            
            # Get network nodes
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                return {'status': 'no_network'}
            
            reconciled_bets = 0
            reconciled_stakes = 0
            conflicts = []
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
                        # Get bets from other node
                        bets = ReconciliationService._fetch_bets_from_node(node_url)
                        
                        # Process each bet
                        for bet_data in bets:
                            result = ReconciliationService._reconcile_bet(bet_data, node_url)
                            
                            if result['status'] == 'reconciled':
                                reconciled_bets += 1
                            elif result['status'] == 'conflict':
                                conflicts.append(result)
                        
                        # Get stakes from other node
                        stakes = ReconciliationService._fetch_stakes_from_node(node_url)
                        
                        # Process each stake
                        for stake_data in stakes:
                            result = ReconciliationService._reconcile_stake(stake_data, node_url)
                            
                            if result['status'] == 'reconciled':
                                reconciled_stakes += 1
                            elif result['status'] == 'conflict':
                                conflicts.append(result)
                                
                    except Exception as e:
                        logging.error(f"Error reconciling bets with node {node_url}: {e}")
            
            result = {
                'status': 'completed',
                'reconciled_bets': reconciled_bets,
                'reconciled_stakes': reconciled_stakes,
                'conflicts': len(conflicts),
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
            logging.info(f"Bet reconciliation completed: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Error reconciling bets: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _fetch_time_entries_from_node(node_url, since_timestamp):
        """Fetch time entries from a specific node"""
        try:
            import requests
            
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/api/sync/time",
                params={'since': since_timestamp},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # return data.get('entries', [])  # Phase 7: Database removed
            else:
                logging.error(f"Failed to fetch time entries from {node_url}: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching time entries from {node_url}: {e}")
            return []
    
    @staticmethod
    def _fetch_transactions_from_node(node_url, since_time):
        """Fetch transactions from a specific node"""
        try:
            import requests
            
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/api/sync/transactions",
                params={'since': since_time.isoformat()},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # return data.get('transactions', [])  # Phase 7: Database removed
            else:
                logging.error(f"Failed to fetch transactions from {node_url}: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching transactions from {node_url}: {e}")
            return []
    
    @staticmethod
    def _fetch_bets_from_node(node_url):
        """Fetch bets from a specific node"""
        try:
            import requests
            
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/api/sync/bets",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # return data.get('bets', [])  # Phase 7: Database removed
            else:
                logging.error(f"Failed to fetch bets from {node_url}: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching bets from {node_url}: {e}")
            return []
    
    @staticmethod
    def _fetch_stakes_from_node(node_url):
        """Fetch stakes from a specific node"""
        try:
            import requests
            
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/api/sync/stakes",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # return data.get('stakes', [])  # Phase 7: Database removed
            else:
                logging.error(f"Failed to fetch stakes from {node_url}: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Error fetching stakes from {node_url}: {e}")
            return []
    
    @staticmethod
    def _reconcile_time_entry(entry_data, source_node):
        """Reconcile a single time entry"""
        try:
            # Check if entry already exists
    # existing = SyntheticTimeEntry.query.filter_by(  # Phase 7: Database removed
                timestamp_ms=entry_data['timestamp_ms'],
                node_id=entry_data['node_id'],
                hash_chain=entry_data['hash_chain']
    # ).first()  # Phase 7: Database removed
            
            if existing:
                return {'status': 'exists', 'entry_id': existing.id}
            
            # Validate entry hash
            if not TimeLedgerService._validate_entry_hash(entry_data):
                return {'status': 'conflict', 'reason': 'invalid_hash', 'entry_data': entry_data}
            
            # Create new entry
            entry = SyntheticTimeEntry(
                timestamp_ms=entry_data['timestamp_ms'],
                entry_type=entry_data['entry_type'],
                entry_data=entry_data['entry_data'],
                node_id=entry_data['node_id'],
                hash_chain=entry_data['hash_chain']
            )
            
    # db.session.add(entry)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            return {'status': 'reconciled', 'entry_id': entry.id}
            
        except Exception as e:
            logging.error(f"Error reconciling time entry: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _reconcile_transaction(tx_data, source_node):
        """Reconcile a single transaction"""
        try:
            # Check if transaction already exists
    # existing = Transaction.query.filter_by(tx_hash=tx_data['tx_hash']).first()  # Phase 7: Database removed
            
            if existing:
                # Check for conflicts
                if (existing.amount != Decimal(tx_data['amount']) or
                    existing.currency != tx_data['currency']):
                    return {'status': 'conflict', 'reason': 'data_mismatch', 'tx_data': tx_data}
                
                return {'status': 'exists', 'tx_id': existing.id}
            
            # Validate transaction on blockchain
            if not BlockchainService.validate_transaction(
                tx_data['tx_hash'],
                tx_data['currency'],
                tx_data['amount']
            ):
                return {'status': 'conflict', 'reason': 'blockchain_validation_failed', 'tx_data': tx_data}
            
            # Create new transaction
            transaction = Transaction(
                tx_hash=tx_data['tx_hash'],
                from_address=tx_data['from_address'],
                to_address=tx_data['to_address'],
                amount=Decimal(tx_data['amount']),
                currency=tx_data['currency'],
    # block_number=tx_data.get('block_number'),  # Phase 7: Database removed
    # status=tx_data.get('status', 'confirmed'),  # Phase 7: Database removed
                platform_fee=BlockchainService.calculate_platform_fee(tx_data['amount']),
                created_at=datetime.fromisoformat(tx_data['created_at'])
            )
            
    # db.session.add(transaction)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            return {'status': 'reconciled', 'tx_id': transaction.id}
            
        except Exception as e:
            logging.error(f"Error reconciling transaction: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _reconcile_bet(bet_data, source_node):
        """Reconcile a single bet"""
        try:
            # Check if bet already exists
    # existing = Bet.query.get(bet_data['id'])  # Phase 7: Database removed
            
            if existing:
                # Check for conflicts
                if (existing.predicted_text != bet_data['predicted_text'] or
                    existing.stake_amount != Decimal(bet_data['stake_amount'])):
                    return {'status': 'conflict', 'reason': 'data_mismatch', 'bet_data': bet_data}
                
                return {'status': 'exists', 'bet_id': existing.id}
            
            # Validate bet transaction
            if not BlockchainService.validate_transaction(
                bet_data['tx_hash'],
                bet_data['stake_currency'],
                bet_data['stake_amount']
            ):
                return {'status': 'conflict', 'reason': 'blockchain_validation_failed', 'bet_data': bet_data}
            
            # Create new bet
            bet = Bet(
                id=bet_data['id'],
                creator_wallet=bet_data['creator_wallet'],
                actor_id=bet_data['actor_id'],
                oracle_id=bet_data['oracle_id'],
                start_time=datetime.fromisoformat(bet_data['start_time']),
                end_time=datetime.fromisoformat(bet_data['end_time']),
                predicted_text=bet_data['predicted_text'],
                stake_amount=Decimal(bet_data['stake_amount']),
                stake_currency=bet_data['stake_currency'],
                tx_hash=bet_data['tx_hash'],
    # status=bet_data.get('status', 'active'),  # Phase 7: Database removed
                created_at=datetime.fromisoformat(bet_data['created_at'])
            )
            
    # db.session.add(bet)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            return {'status': 'reconciled', 'bet_id': bet.id}
            
        except Exception as e:
            logging.error(f"Error reconciling bet: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _reconcile_stake(stake_data, source_node):
        """Reconcile a single stake"""
        try:
            # Check if stake already exists
    # existing = Stake.query.get(stake_data['id'])  # Phase 7: Database removed
            
            if existing:
                # Check for conflicts
                if (existing.amount != Decimal(stake_data['amount']) or
                    existing.position != stake_data['position']):
                    return {'status': 'conflict', 'reason': 'data_mismatch', 'stake_data': stake_data}
                
                return {'status': 'exists', 'stake_id': existing.id}
            
            # Validate stake transaction
            if not BlockchainService.validate_transaction(
                stake_data['tx_hash'],
                stake_data['currency'],
                stake_data['amount']
            ):
                return {'status': 'conflict', 'reason': 'blockchain_validation_failed', 'stake_data': stake_data}
            
            # Create new stake
            stake = Stake(
                id=stake_data['id'],
                bet_id=stake_data['bet_id'],
                staker_wallet=stake_data['staker_wallet'],
                amount=Decimal(stake_data['amount']),
                currency=stake_data['currency'],
                position=stake_data['position'],
                tx_hash=stake_data['tx_hash'],
                created_at=datetime.fromisoformat(stake_data['created_at'])
            )
            
    # db.session.add(stake)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
            
            return {'status': 'reconciled', 'stake_id': stake.id}
            
        except Exception as e:
            logging.error(f"Error reconciling stake: {e}")
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _validate_transaction_integrity():
        """Validate transaction integrity"""
        try:
            # Check for duplicate transactions
    # duplicates = db.session.query(Transaction.tx_hash).group_by(Transaction.tx_hash).having(db.func.count(Transaction.id) > 1).all()  # Phase 7: Database removed
            
            if duplicates:
                logging.error(f"Found {len(duplicates)} duplicate transactions")
                return False
            
            # Check transaction amounts
    # invalid_amounts = Transaction.query.filter(Transaction.amount <= 0).count()  # Phase 7: Database removed
            
            if invalid_amounts > 0:
                logging.error(f"Found {invalid_amounts} transactions with invalid amounts")
                return False
            
            # Check platform fees
    # for tx in Transaction.query.filter(Transaction.platform_fee.is_(None)).all():  # Phase 7: Database removed
                expected_fee = BlockchainService.calculate_platform_fee(tx.amount)
                tx.platform_fee = expected_fee
            
    # db.session.commit()  # Phase 7: Database removed
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating transaction integrity: {e}")
            return False
    
    @staticmethod
    def sync_transaction(tx_data, source_node):
        """Synchronize a transaction from another node"""
        try:
            result = ReconciliationService._reconcile_transaction(tx_data, source_node)
            
            if result['status'] == 'reconciled':
                logging.info(f"Transaction synchronized from {source_node}: {tx_data['tx_hash']}")
                return True
            elif result['status'] == 'conflict':
                logging.warning(f"Transaction conflict from {source_node}: {result}")
                return False
            else:
                return True  # Already exists
                
        except Exception as e:
            logging.error(f"Error synchronizing transaction: {e}")
            return False
    
    @staticmethod
    def get_reconciliation_status():
        """Get current reconciliation status"""
        try:
            current_node = Config.NODE_ID
            
            # Get last reconciliation times
    # last_full = redis_client.get(f'node:{current_node}:last_reconcile')  # Phase 7: Database removed
    # last_time = redis_client.get(f'node:{current_node}:last_time_reconcile')  # Phase 7: Database removed
    # last_tx = redis_client.get(f'node:{current_node}:last_tx_reconcile')  # Phase 7: Database removed
            
            # Get network status
            network_status = NetworkService.get_network_status()
            
            # Get conflict count
    # conflict_count = redis_client.get(f'node:{current_node}:conflict_count') or 0  # Phase 7: Database removed
            
            return {
                'node_id': current_node,
                'last_full_reconcile': last_full,
                'last_time_reconcile': last_time,
                'last_transaction_reconcile': last_tx,
                'network_status': network_status,
                'conflict_count': int(conflict_count),
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
            
        except Exception as e:
            logging.error(f"Error getting reconciliation status: {e}")
            return {'error': str(e)}
