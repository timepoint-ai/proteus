# from models import NodeOperator, SyntheticTimeEntry, Transaction  # Phase 7: Models removed
# from app import db, redis_client  # Phase 7: Database removed
from config import Config
import logging
import requests
import json
import time
from datetime import datetime, timedelta, timezone
import threading

class NetworkService:
    """Service for handling network communication and synchronization"""
    
    @staticmethod
    def initialize_node():
        """Initialize current node in the network"""
        try:
            node_id = Config.NODE_ID
            if not node_id:
                logging.error("No NODE_ID configured")
                return False
            
            # Check if node exists
    # node = NodeOperator.query.filter_by(operator_id=node_id).first()  # Phase 7: Database removed
            
            if not node:
                # Create new node
                node = NodeOperator(
                    operator_id=node_id,
                    public_key=Config.NODE_PRIVATE_KEY,  # In production, derive public key
                    status='pending'
                )
    # db.session.add(node)  # Phase 7: Database removed
    # db.session.commit()  # Phase 7: Database removed
                
                logging.info(f"Node initialized: {node_id}")
            else:
                logging.info(f"Node already exists: {node_id}")
            
            # Start heartbeat
            NetworkService._start_heartbeat()
            
            return True
            
        except Exception as e:
            logging.error(f"Error initializing node: {e}")
            return False
    
    @staticmethod
    def _start_heartbeat():
        """Start heartbeat thread"""
        def heartbeat_worker():
            while True:
                try:
                    NetworkService._send_heartbeat()
                    time.sleep(60)  # Send heartbeat every minute
                except Exception as e:
                    logging.error(f"Heartbeat error: {e}")
                    time.sleep(60)
        
        heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        heartbeat_thread.start()
    
    @staticmethod
    def _send_heartbeat():
        """Send heartbeat to network nodes"""
        try:
            node_id = Config.NODE_ID
            if not node_id:
                return
            
            # Update local heartbeat
    # node = NodeOperator.query.filter_by(operator_id=node_id).first()  # Phase 7: Database removed
            if node:
                node.last_heartbeat = datetime.now(timezone.utc)
    # db.session.commit()  # Phase 7: Database removed
            
            # Send heartbeat to other nodes
            network_nodes = Config.NETWORK_NODES
            if network_nodes:
                for node_url in network_nodes:
                    if node_url.strip():
                        try:
                            response = requests.post(
                                f"{node_url}/node/heartbeat",
                                json={'node_id': node_id},
                                timeout=5
                            )
                            if response.status_code == 200:
                                logging.debug(f"Heartbeat sent to {node_url}")
                        except Exception as e:
                            logging.warning(f"Failed to send heartbeat to {node_url}: {e}")
            
        except Exception as e:
            logging.error(f"Error sending heartbeat: {e}")
    
    @staticmethod
    def broadcast_node_registration(node_id):
        """Broadcast node registration to network"""
        try:
    # node = NodeOperator.query.get(node_id)  # Phase 7: Database removed
            if not node:
                return False
            
            message = {
                'type': 'node_registration',
                'data': {
                    'node_id': node.id,
                    'operator_id': node.operator_id,
                    'public_key': node.public_key,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
            
            return NetworkService._broadcast_to_network(message)
            
        except Exception as e:
            logging.error(f"Error broadcasting node registration: {e}")
            return False
    
    @staticmethod
    def broadcast_message(message_type, message_data, sender_node_id):
        """Broadcast a message to the network"""
        try:
            message = {
                'type': message_type,
                'data': message_data,
                'sender': sender_node_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store in Redis for deduplication
            message_id = f"msg_{sender_node_id}_{int(time.time() * 1000)}"
            redis_client.setex(f"broadcast:{message_id}", 3600, json.dumps(message))
            
            return NetworkService._broadcast_to_network(message)
            
        except Exception as e:
            logging.error(f"Error broadcasting message: {e}")
            return None
    
    @staticmethod
    def _broadcast_to_network(message):
        """Send message to all network nodes"""
        try:
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                return True
            
            success_count = 0
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
                        response = requests.post(
                            f"{node_url}/node/broadcast",
                            json=message,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            success_count += 1
                            logging.debug(f"Message broadcast to {node_url}")
                        else:
                            logging.warning(f"Failed to broadcast to {node_url}: {response.status_code}")
                            
                    except Exception as e:
                        logging.warning(f"Failed to broadcast to {node_url}: {e}")
            
            logging.info(f"Broadcast successful to {success_count}/{len(network_nodes)} nodes")
            return success_count > 0
            
        except Exception as e:
            logging.error(f"Error broadcasting to network: {e}")
            return False
    
    @staticmethod
    def sync_with_network():
        """Synchronize data with network nodes"""
        try:
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                return True
            
            current_node_id = Config.NODE_ID
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
                        # Sync time ledger
                        NetworkService._sync_time_ledger_with_node(node_url, current_node_id)
                        
                        # Sync transactions
                        NetworkService._sync_transactions_with_node(node_url, current_node_id)
                        
                        logging.debug(f"Synchronized with {node_url}")
                        
                    except Exception as e:
                        logging.warning(f"Failed to sync with {node_url}: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error syncing with network: {e}")
            return False
    
    @staticmethod
    def _sync_time_ledger_with_node(node_url, current_node_id):
        """Sync time ledger with a specific node"""
        try:
            # Get our latest timestamp
    # latest_local = SyntheticTimeEntry.query.order_by(  # Phase 7: Database removed
                SyntheticTimeEntry.timestamp_ms.desc()
    # ).first()  # Phase 7: Database removed
            
            since_timestamp = latest_local.timestamp_ms if latest_local else 0
            
            # Request entries from other node
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/node/sync/time",
                params={'since': since_timestamp},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # entries = data.get('entries', [])  # Phase 7: Database removed
                
                # Process entries
                for entry in entries:
                    from services.time_ledger import TimeLedgerService
                    TimeLedgerService.sync_entry(entry, node_url)
                
                logging.info(f"Synced {len(entries)} time ledger entries from {node_url}")
            
        except Exception as e:
            logging.error(f"Error syncing time ledger with {node_url}: {e}")
    
    @staticmethod
    def _sync_transactions_with_node(node_url, current_node_id):
        """Sync transactions with a specific node"""
        try:
            # Get our latest transaction
    # latest_local = Transaction.query.order_by(  # Phase 7: Database removed
                Transaction.created_at.desc()
    # ).first()  # Phase 7: Database removed
            
            since_time = latest_local.created_at if latest_local else datetime.now(timezone.utc) - timedelta(days=1)
            
            # Request transactions from other node
    # response = requests.get(  # Phase 7: Database removed
                f"{node_url}/node/sync/transactions",
                params={'since': since_time.isoformat()},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
    # transactions = data.get('transactions', [])  # Phase 7: Database removed
                
                # Process transactions
                for tx in transactions:
                    from services.reconciliation import ReconciliationService
                    ReconciliationService.sync_transaction(tx, node_url)
                
                logging.info(f"Synced {len(transactions)} transactions from {node_url}")
            
        except Exception as e:
            logging.error(f"Error syncing transactions with {node_url}: {e}")
    
    @staticmethod
    def get_network_status():
        """Get current network status"""
        try:
            # Get all nodes
    # all_nodes = NodeOperator.query.all()  # Phase 7: Database removed
            
            # Check node health
            healthy_nodes = 0
            stale_nodes = 0
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            
            for node in all_nodes:
                if node.last_heartbeat and node.last_heartbeat > cutoff_time:
                    healthy_nodes += 1
                else:
                    stale_nodes += 1
            
            # Get network nodes from config
            configured_nodes = len([n for n in Config.NETWORK_NODES if n.strip()])
            
            return {
                'total_nodes': len(all_nodes),
    # 'active_nodes': NodeOperator.query.filter_by(status='active').count(),  # Phase 7: Database removed
    # 'pending_nodes': NodeOperator.query.filter_by(status='pending').count(),  # Phase 7: Database removed
                'healthy_nodes': healthy_nodes,
                'stale_nodes': stale_nodes,
                'configured_nodes': configured_nodes,
                'network_connected': configured_nodes > 0,
    # 'last_sync': redis_client.get('network:last_sync')  # Phase 7: Database removed
            }
            
        except Exception as e:
            logging.error(f"Error getting network status: {e}")
            return {}
    
    @staticmethod
    def discover_nodes():
        """Discover other nodes in the network"""
        try:
            network_nodes = Config.NETWORK_NODES
            if not network_nodes:
                return []
            
            discovered_nodes = []
            
            for node_url in network_nodes:
                if node_url.strip():
                    try:
    # response = requests.get(  # Phase 7: Database removed
                            f"{node_url}/node/status",
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            node_data = response.json()
                            discovered_nodes.append({
                                'url': node_url,
                                'status': 'online',
                                'data': node_data
                            })
                        else:
                            discovered_nodes.append({
                                'url': node_url,
                                'status': 'offline',
                                'data': None
                            })
                            
                    except Exception as e:
                        discovered_nodes.append({
                            'url': node_url,
                            'status': 'error',
                            'error': str(e)
                        })
            
            return discovered_nodes
            
        except Exception as e:
            logging.error(f"Error discovering nodes: {e}")
            return []
