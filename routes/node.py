from flask import Blueprint, request, jsonify
# from models import NodeOperator, SyntheticTimeEntry, Transaction  # Phase 7: Models removed
from services.network import NetworkService
from services.consensus import ConsensusService
from services.reconciliation import ReconciliationService
from services.time_ledger import TimeLedgerService
from utils.auth import require_node_auth
# from app import db, redis_client  # Phase 7: Database removed
import logging
import json

node_bp = Blueprint('node', __name__)

@node_bp.route('/register', methods=['POST'])
def register_node():
    """Register a new node operator"""
    data = request.json
    
    try:
        required_fields = ['operator_id', 'public_key']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Check if operator already exists
        existing = NodeOperator.query.filter_by(operator_id=data['operator_id']).first()
        if existing:
            return jsonify({'error': 'Operator ID already exists'}), 409
        
        # Create new node operator
        node = NodeOperator(
            operator_id=data['operator_id'],
            public_key=data['public_key'],
            status='pending'
        )
        
        db.session.add(node)
        db.session.commit()
        
        # Broadcast to network
        NetworkService.broadcast_node_registration(node.id)
        
        return jsonify({
            'id': node.id,
            'status': 'pending',
            'message': 'Node registration submitted for voting'
        }), 201
        
    except Exception as e:
        logging.error(f"Error registering node: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/heartbeat', methods=['POST'])
@require_node_auth
def heartbeat():
    """Node heartbeat endpoint"""
    try:
        # Update last heartbeat
        node = NodeOperator.query.get(request.node_id)
        if node:
            node.last_heartbeat = TimeLedgerService.get_current_time()
            db.session.commit()
        
        return jsonify({
            'status': 'acknowledged',
            'timestamp': TimeLedgerService.get_current_time_ms()
        })
        
    except Exception as e:
        logging.error(f"Error processing heartbeat: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/consensus/vote', methods=['POST'])
@require_node_auth
def consensus_vote():
    """Submit a consensus vote"""
    data = request.json
    
    try:
        required_fields = ['subject_id', 'vote_type', 'vote']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        if data['vote_type'] == 'node':
            result = ConsensusService.vote_on_node(
                data['subject_id'],
                data['vote'],
                request.node_id
            )
        elif data['vote_type'] == 'actor':
            result = ConsensusService.vote_on_actor(
                data['subject_id'],
                data['vote'],
                request.node_id
            )
        elif data['vote_type'] == 'oracle':
            result = ConsensusService.vote_on_oracle_statement(
                data['subject_id'],
                data['vote'],
                request.node_id
            )
        else:
            return jsonify({'error': 'Invalid vote type'}), 400
        
        if result:
            return jsonify({'status': 'voted', 'message': 'Vote recorded'})
        else:
            return jsonify({'error': 'Vote failed'}), 500
            
    except Exception as e:
        logging.error(f"Error processing vote: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/sync/time', methods=['POST'])
@require_node_auth
def sync_time():
    """Synchronize time ledger entries"""
    data = request.json
    
    try:
        entries = data.get('entries', [])
        
        # Process each entry
        for entry_data in entries:
            result = TimeLedgerService.sync_entry(entry_data, request.node_id)
            if not result:
                logging.warning(f"Failed to sync entry: {entry_data}")
        
        return jsonify({
            'status': 'synced',
            'processed': len(entries),
            'timestamp': TimeLedgerService.get_current_time_ms()
        })
        
    except Exception as e:
        logging.error(f"Error syncing time ledger: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/sync/transactions', methods=['POST'])
@require_node_auth
def sync_transactions():
    """Synchronize transaction data"""
    data = request.json
    
    try:
        transactions = data.get('transactions', [])
        
        # Process each transaction
        for tx_data in transactions:
            result = ReconciliationService.sync_transaction(tx_data, request.node_id)
            if not result:
                logging.warning(f"Failed to sync transaction: {tx_data}")
        
        return jsonify({
            'status': 'synced',
            'processed': len(transactions),
            'timestamp': TimeLedgerService.get_current_time_ms()
        })
        
    except Exception as e:
        logging.error(f"Error syncing transactions: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/broadcast', methods=['POST'])
@require_node_auth
def broadcast_message():
    """Broadcast a message to the network"""
    data = request.json
    
    try:
        message_type = data.get('type')
        message_data = data.get('data')
        
        if not message_type or not message_data:
            return jsonify({'error': 'Missing message type or data'}), 400
        
        # Broadcast to network
        result = NetworkService.broadcast_message(message_type, message_data, request.node_id)
        
        return jsonify({
            'status': 'broadcast',
            'message_id': result,
            'timestamp': TimeLedgerService.get_current_time_ms()
        })
        
    except Exception as e:
        logging.error(f"Error broadcasting message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/reconcile', methods=['POST'])
@require_node_auth
def reconcile_data():
    """Trigger data reconciliation"""
    data = request.json
    
    try:
        reconcile_type = data.get('type', 'full')
        
        if reconcile_type == 'time':
            result = ReconciliationService.reconcile_time_ledger(request.node_id)
        elif reconcile_type == 'transactions':
            result = ReconciliationService.reconcile_transactions(request.node_id)
        elif reconcile_type == 'full':
            result = ReconciliationService.reconcile_full(request.node_id)
        else:
            return jsonify({'error': 'Invalid reconciliation type'}), 400
        
        return jsonify({
            'status': 'reconciled',
            'result': result,
            'timestamp': TimeLedgerService.get_current_time_ms()
        })
        
    except Exception as e:
        logging.error(f"Error reconciling data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@node_bp.route('/status', methods=['GET'])
@require_node_auth
def node_status():
    """Get node status information"""
    try:
        node = NodeOperator.query.get(request.node_id)
        if not node:
            return jsonify({'error': 'Node not found'}), 404
        
        # Get network stats
        active_nodes = NodeOperator.query.filter_by(status='active').count()
        pending_nodes = NodeOperator.query.filter_by(status='pending').count()
        
        # Get sync status
        last_sync = redis_client.get(f'node:{request.node_id}:last_sync')
        
        return jsonify({
            'node_id': node.id,
            'operator_id': node.operator_id,
            'status': node.status,
            'last_heartbeat': node.last_heartbeat.isoformat() if node.last_heartbeat else None,
            'network': {
                'active_nodes': active_nodes,
                'pending_nodes': pending_nodes,
                'total_nodes': active_nodes + pending_nodes
            },
            'sync': {
                'last_sync': last_sync,
                'timestamp': TimeLedgerService.get_current_time_ms()
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting node status: {e}")
        return jsonify({'error': 'Internal server error'}), 500
